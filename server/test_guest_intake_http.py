import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.rate_limit import SlidingWindowRateLimiter
from server.sqlite_store import SQLiteMessengerStore


class GuestIntakeHttpTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tokens = {"admin-token": "AI-ADMIN", "member-token": "AI-MEMBER"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(self.tmp.name + "/guest.sqlite")
        self.backend = MessengerBackend(
            self.tokens, {"guest-room": {"AI-ADMIN", "AI-MEMBER"}},
            self.store, authenticator=self.auth)
        self.backend.create_conversation(
            "admin-token", "guest-room", ["AI-ADMIN", "AI-MEMBER"], "GROUP")
        self.invite = self.backend.create_room_invite(
            "admin-token", "guest-room", expires_in_seconds=600, max_uses=3)
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

    def request(self, method, path, payload=None, token=None):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {}
        if token:
            headers["Authorization"] = "Bearer " + token
        body = None
        if payload is not None:
            body = json.dumps(payload)
            headers["Content-Type"] = "application/json"
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()
        return response.status, data

    def test_public_guest_submission_requires_no_bearer_and_grants_no_access(self):
        status, data = self.request("POST", "/v1/guest-applications", {
            "inviteToken": self.invite["token"],
            "displayName": "Browser Guest",
            "providerClaim": "GEMINI",
        })
        self.assertEqual(status, 202)
        self.assertEqual(data["application"]["status"], "PENDING")
        self.assertFalse(data["application"]["providerVerified"])
        self.assertFalse(data["application"]["accessGranted"])
        self.assertNotIn("conversationId", data["application"])

    def test_admin_review_requires_authentication_and_room_admin(self):
        status, _ = self.request("POST", "/v1/guest-applications", {
            "inviteToken": self.invite["token"],
            "displayName": "Review Guest",
            "providerClaim": "OTHER",
        })
        self.assertEqual(status, 202)
        status, data = self.request(
            "GET", "/v1/conversations/guest-room/guest-applications")
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "authentication_required")
        status, data = self.request(
            "GET", "/v1/conversations/guest-room/guest-applications",
            token="member-token")
        self.assertEqual(status, 403)
        status, data = self.request(
            "GET", "/v1/conversations/guest-room/guest-applications",
            token="admin-token")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["applications"]), 1)

    def test_admin_can_approve_without_creating_a_session(self):
        _, created = self.request("POST", "/v1/guest-applications", {
            "inviteToken": self.invite["token"],
            "displayName": "Approval Guest",
            "providerClaim": "CLAUDE",
        })
        application_id = created["application"]["applicationId"]
        status, data = self.request(
            "POST", "/v1/conversations/guest-room/guest-applications/" + application_id,
            {"decision": "APPROVE"}, token="admin-token")
        self.assertEqual(status, 200)
        self.assertEqual(data["application"]["status"], "APPROVED_AWAITING_PROVISIONING")
        self.assertNotIn("sessionToken", data["application"])
        self.assertNotIn("bearerToken", data["application"])

    def test_invalid_guest_request_returns_generic_error(self):
        status, data = self.request("POST", "/v1/guest-applications", {
            "inviteToken": "not-a-real-token",
            "displayName": "Guest",
            "providerClaim": "CHATGPT",
        })
        self.assertEqual(status, 400)
        self.assertEqual(data["error"], "guest_invite_unavailable")


if __name__ == "__main__":
    unittest.main()
