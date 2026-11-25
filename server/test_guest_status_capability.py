import base64
import hashlib
import json
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.rate_limit import SlidingWindowRateLimiter
from server.sqlite_store import SQLiteMessengerStore, SCHEMA_VERSION


def capability(seed):
    raw = bytes([seed]) * 32
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


class GuestStatusCapabilityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tokens = {"admin-token": "AI-ADMIN", "member-token": "AI-MEMBER"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(self.tmp.name + "/guest-status.sqlite")
        self.backend = MessengerBackend(self.tokens, {}, self.store, authenticator=self.auth)
        self.backend.create_conversation("admin-token", "guest-room", ["AI-ADMIN", "AI-MEMBER"], "GROUP")
        self.invite = self.backend.create_room_invite("admin-token", "guest-room", expires_in_seconds=600, max_uses=1)
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter()
        MessengerHandler.operational = None
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.backend.close()
        self.tmp.cleanup()

    def request(self, method, path, payload=None):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        body = json.dumps(payload) if payload is not None else None
        headers = {"Content-Type": "application/json"} if body is not None else {}
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        result = json.loads(response.read().decode("utf-8"))
        conn.close()
        return response.status, result

    def submit(self, name="Status Guest", cap=None):
        return self.request("POST", "/v1/guest-applications", {
            "inviteToken": self.invite["token"],
            "displayName": name,
            "providerClaim": "CLAUDE",
            "statusCapability": cap or capability(7),
        })

    def test_schema_v10_adds_nullable_digest_columns(self):
        self.assertEqual(SCHEMA_VERSION, 10)
        columns = {row["name"] for row in self.store.connection.execute("PRAGMA table_info(guest_applications)")}
        self.assertIn("status_capability_hash", columns)
        self.assertIn("status_capability_expires_at", columns)

    def test_submission_persists_only_sha256_digest(self):
        cap = capability(7)
        status, result = self.submit(cap=cap)
        self.assertEqual(status, 202)
        row = self.store.connection.execute("SELECT status_capability_hash,status_capability_expires_at FROM guest_applications").fetchone()
        self.assertEqual(row["status_capability_hash"], hashlib.sha256(base64.urlsafe_b64decode(cap + "=")).hexdigest())
        self.assertNotEqual(row["status_capability_hash"], cap)
        self.assertGreater(row["status_capability_expires_at"], time.time())
        self.assertNotIn("statusCapability", json.dumps(result))
        self.assertNotIn("credential", json.dumps(result))

    def test_same_capability_retry_is_idempotent_even_when_invite_use_is_consumed(self):
        cap = capability(8)
        first_status, first = self.submit(cap=cap)
        second_status, second = self.submit(cap=cap)
        self.assertEqual(first_status, 202)
        self.assertEqual(second_status, 202)
        self.assertEqual(first["application"]["applicationId"], second["application"]["applicationId"])
        self.assertTrue(second["application"]["idempotentReplay"])
        uses = self.store.connection.execute("SELECT uses FROM room_invites").fetchone()[0]
        self.assertEqual(uses, 1)

    def test_different_capability_duplicate_discloses_no_application_status(self):
        self.submit(cap=capability(9))
        status, result = self.submit(cap=capability(10))
        self.assertEqual(status, 202)
        self.assertEqual(result["application"], {"duplicate": True, "accessGranted": False, "providerVerified": False})

    def test_status_endpoint_returns_minimal_pending_state(self):
        cap = capability(11)
        self.submit(cap=cap)
        status, result = self.request("POST", "/v1/guest-applications/status", {"statusCapability": cap})
        self.assertEqual(status, 200)
        self.assertEqual(set(result), {"status"})
        self.assertEqual(set(result["status"]), {"state", "updatedAt"})
        self.assertEqual(result["status"]["state"], "PENDING")

    def test_status_tracks_approval_provisioning_and_revocation(self):
        cap = capability(12)
        _, receipt = self.submit(cap=cap)
        app_id = receipt["application"]["applicationId"]
        self.backend.decide_guest_application("admin-token", "guest-room", app_id, "APPROVE")
        self.assertEqual(self.backend.get_public_guest_application_status(cap)["state"], "APPROVED_AWAITING_PROVISIONING")
        self.backend.provision_guest_application("admin-token", "guest-room", app_id)
        self.assertEqual(self.backend.get_public_guest_application_status(cap)["state"], "ACTIVE")
        self.backend.revoke_guest_provisioning("admin-token", "guest-room", app_id)
        self.assertEqual(self.backend.get_public_guest_application_status(cap)["state"], "REVOKED")
        self.assertNotIn("credential", self.backend.get_public_guest_application_status(cap))

    def test_rejected_application_has_terminal_public_state(self):
        cap = capability(13)
        _, receipt = self.submit(cap=cap)
        self.backend.decide_guest_application("admin-token", "guest-room", receipt["application"]["applicationId"], "REJECT")
        self.assertEqual(self.backend.get_public_guest_application_status(cap)["state"], "REJECTED")

    def test_unknown_malformed_and_expired_capabilities_share_not_found(self):
        for value in ("?", capability(14)[:-1], capability(14) + "A"):
            status, body = self.request("POST", "/v1/guest-applications/status", {"statusCapability": value})
            self.assertEqual(status, 404)
            self.assertEqual(body["error"], "guest_application_status_unavailable")
        cap = capability(15)
        self.submit(cap=cap)
        self.store.connection.execute("UPDATE guest_applications SET status_capability_expires_at=?", (time.time() - 1,))
        self.store.connection.commit()
        status, body = self.request("POST", "/v1/guest-applications/status", {"statusCapability": cap})
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "guest_application_status_unavailable")

    def test_status_route_rejects_extra_fields_and_application_id_auth(self):
        self.submit(cap=capability(16))
        status, body = self.request("POST", "/v1/guest-applications/status", {
            "statusCapability": capability(16), "applicationId": "not-an-authenticator"})
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "guest_application_status_unavailable")

    def test_legacy_application_without_capability_is_not_publicly_queryable(self):
        legacy = self.backend.submit_public_guest_application({
            "inviteToken": self.invite["token"], "displayName": "Legacy Guest", "providerClaim": "OTHER"})
        self.assertIsNone(self.store.connection.execute(
            "SELECT status_capability_hash FROM guest_applications WHERE application_id=?",
            (legacy["applicationId"],)).fetchone()[0])


    def test_schema_v9_migration_preserves_legacy_rows_without_public_capability(self):
        import sqlite3
        legacy_path = self.tmp.name + "/legacy-v9.sqlite"
        with sqlite3.connect(legacy_path) as connection:
            connection.execute("CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            connection.execute("INSERT INTO schema_meta(key,value) VALUES('version','9')")
            connection.execute("CREATE TABLE guest_applications (application_id TEXT PRIMARY KEY, status TEXT, provisioning_status TEXT)")
            connection.execute("INSERT INTO guest_applications(application_id,status,provisioning_status) VALUES('legacy-app','PENDING','NOT_STARTED')")
        migrated = SQLiteMessengerStore(legacy_path)
        try:
            row = migrated.connection.execute("SELECT application_id,status_capability_hash,status_capability_expires_at FROM guest_applications WHERE application_id='legacy-app'").fetchone()
            self.assertEqual(row["application_id"], "legacy-app")
            self.assertIsNone(row["status_capability_hash"])
            self.assertIsNone(row["status_capability_expires_at"])
            version = migrated.connection.execute("SELECT value FROM schema_meta WHERE key='version'").fetchone()[0]
            self.assertEqual(version, "10")
        finally:
            migrated.close()



    def test_capability_cannot_be_reused_for_a_different_application(self):
        cap = capability(17)
        self.submit(name="First Guest", cap=cap)
        status, result = self.submit(name="Different Guest", cap=cap)
        self.assertEqual(status, 202)
        self.assertEqual(result["application"], {"duplicate": True, "accessGranted": False, "providerVerified": False})
        count = self.store.connection.execute("SELECT COUNT(*) FROM guest_applications").fetchone()[0]
        self.assertEqual(count, 1)



if __name__ == "__main__":
    unittest.main()
