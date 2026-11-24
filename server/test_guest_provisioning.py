import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone

from server.auth import Authenticator
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore


class GuestCredentialProvisioningTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = self.temp.name + "/messenger.sqlite"
        self.tokens = {"admin-token": "AI-ADMIN", "member-token": "AI-MEMBER"}
        self.store = SQLiteMessengerStore(self.path)
        self.auth = Authenticator(self.tokens)
        self.backend = MessengerBackend(
            self.tokens, {}, self.store, authenticator=self.auth)
        self.backend.create_conversation(
            "admin-token", "room-a", ["AI-ADMIN", "AI-MEMBER"], "GROUP")
        self.backend.create_conversation(
            "admin-token", "room-b", ["AI-ADMIN", "AI-MEMBER"], "GROUP")
        self.invite = self.backend.create_room_invite(
            "admin-token", "room-a", expires_in_seconds=600, max_uses=5)
        self.application = self.backend.submit_public_guest_application({
            "inviteToken": self.invite["token"],
            "displayName": "External Guest",
            "providerClaim": "CLAUDE",
        })
        self.backend.decide_guest_application(
            "admin-token", "room-a", self.application["applicationId"], "APPROVE")

    def tearDown(self):
        try:
            self.backend.close()
        finally:
            self.temp.cleanup()

    def provision(self):
        return self.backend.provision_guest_application(
            "admin-token", "room-a", self.application["applicationId"])

    def test_admin_provisions_one_identity_with_room_scoped_access(self):
        result = self.provision()
        ai_id = result["identity"]["aiId"]
        token = result["credential"]
        self.assertTrue(ai_id.startswith("AI-GUEST-"))
        self.assertEqual(result["identity"]["displayName"], "External Guest")
        self.assertTrue(result["credentialShownOnce"])
        self.assertFalse(result["providerVerified"])
        self.assertEqual(result["roomAccess"], "INVITED_ROOM_ONLY")
        self.assertEqual(self.backend.authenticate(token), ai_id)
        self.assertIn(ai_id, self.backend.conversation_members()["room-a"])
        self.assertNotIn(ai_id, self.backend.conversation_members()["room-b"])
        self.assertFalse(self.store.is_conversation_admin("room-a", ai_id))
        row = self.store._connection.execute(
            "SELECT token_hash FROM credential_records WHERE ai_id=?", (ai_id,)).fetchone()
        self.assertEqual(len(row["token_hash"]), 64)
        self.assertNotEqual(row["token_hash"], token)

    def test_only_approved_application_can_be_provisioned(self):
        invite = self.backend.create_room_invite(
            "admin-token", "room-a", expires_in_seconds=600, max_uses=2)
        pending = self.backend.submit_public_guest_application({
            "inviteToken": invite["token"], "displayName": "Pending Guest",
            "providerClaim": "OTHER"})
        with self.assertRaisesRegex(ValueError, "guest_application_unavailable"):
            self.backend.provision_guest_application(
                "admin-token", "room-a", pending["applicationId"])

    def test_non_admin_cannot_provision(self):
        with self.assertRaisesRegex(PermissionError, "room_admin_required"):
            self.backend.provision_guest_application(
                "member-token", "room-a", self.application["applicationId"])

    def test_provisioning_is_one_time_and_replay_safe(self):
        first = self.provision()
        with self.assertRaisesRegex(ValueError, "guest_application_unavailable"):
            self.provision()
        self.assertEqual(
            self.store._connection.execute(
                "SELECT COUNT(*) FROM credential_records WHERE ai_id=?",
                (first["identity"]["aiId"],)).fetchone()[0], 1)

    def test_credential_and_membership_survive_backend_restart(self):
        first = self.provision()
        token = first["credential"]
        ai_id = first["identity"]["aiId"]
        self.backend.close()
        new_store = SQLiteMessengerStore(self.path)
        new_backend = MessengerBackend(
            self.tokens, {}, new_store, authenticator=Authenticator(self.tokens))
        try:
            self.assertEqual(new_backend.authenticate(token), ai_id)
            self.assertIn(ai_id, new_backend.conversation_members()["room-a"])
            self.assertNotIn(ai_id, new_backend.conversation_members()["room-b"])
        finally:
            new_backend.close()

    def test_admin_revocation_invalidates_credential_and_removes_room_access(self):
        result = self.provision()
        ai_id, token = result["identity"]["aiId"], result["credential"]
        revoked = self.backend.revoke_guest_provisioning(
            "admin-token", "room-a", self.application["applicationId"])
        self.assertEqual(revoked["status"], "REVOKED")
        self.assertNotIn(ai_id, self.backend.conversation_members()["room-a"])
        with self.assertRaisesRegex(PermissionError, "authentication_required"):
            self.backend.authenticate(token)
        status = self.store._connection.execute(
            "SELECT status FROM credential_records WHERE ai_id=?", (ai_id,)).fetchone()[0]
        self.assertEqual(status, "REVOKED")

    def test_credential_expiry_is_enforced(self):
        result = self.provision()
        token = result["credential"]
        future = datetime.now(timezone.utc) + timedelta(days=31)
        self.assertEqual(self.auth._registry.status(token, now=future), "EXPIRED")
        with self.assertRaisesRegex(PermissionError, "authentication_required"):
            self.auth._registry.authenticate(token, now=future)

    def test_concurrent_provisioning_issues_at_most_one_credential(self):
        outcomes = []
        def worker():
            try:
                outcomes.append(("ok", self.provision()))
            except ValueError:
                outcomes.append(("blocked", None))
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        self.assertEqual(sum(kind == "ok" for kind, _ in outcomes), 1)
        self.assertEqual(sum(kind == "blocked" for kind, _ in outcomes), 1)


if __name__ == "__main__":
    unittest.main()
