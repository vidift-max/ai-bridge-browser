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


class GuestProvisioningHttpTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.tokens = {"admin-token": "AI-ADMIN", "member-token": "AI-MEMBER"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(self.temp.name + "/guest.sqlite")
        self.backend = MessengerBackend(
            self.tokens, {}, self.store, authenticator=self.auth)
        self.backend.create_conversation(
            "admin-token", "guest-room", ["AI-ADMIN", "AI-MEMBER"], "GROUP")
        invite = self.backend.create_room_invite(
            "admin-token", "guest-room", expires_in_seconds=600, max_uses=3)
        self.application = self.backend.submit_public_guest_application({
            "inviteToken": invite["token"],
            "displayName": "HTTP Guest",
            "providerClaim": "GEMINI",
        })
        self.backend.decide_guest_application(
            "admin-token", "guest-room", self.application["applicationId"], "APPROVE")
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
        self.temp.cleanup()

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

    def path(self, action):
        return ("/v1/conversations/guest-room/guest-applications/"
                + self.application["applicationId"] + "/" + action)

    def test_admin_can_provision_and_receives_one_time_credential(self):
        status, data = self.request("POST", self.path("provision"), {}, "admin-token")
        self.assertEqual(status, 201)
        provisioning = data["provisioning"]
        self.assertTrue(provisioning["credential"])
        self.assertTrue(provisioning["credentialShownOnce"])
        self.assertFalse(provisioning["providerVerified"])
        self.assertEqual(provisioning["identity"]["displayName"], "HTTP Guest")
        status, _ = self.request("POST", self.path("provision"), {}, "admin-token")
        self.assertEqual(status, 400)

    def test_non_admin_cannot_provision_or_revoke(self):
        status, data = self.request("POST", self.path("provision"), {}, "member-token")
        self.assertEqual(status, 403)
        self.assertEqual(data["error"], "forbidden")

    def test_admin_can_revoke_provisioned_guest(self):
        status, created = self.request("POST", self.path("provision"), {}, "admin-token")
        self.assertEqual(status, 201)
        token = created["provisioning"]["credential"]
        status, data = self.request("POST", self.path("revoke"), {}, "admin-token")
        self.assertEqual(status, 200)
        self.assertEqual(data["provisioning"]["status"], "REVOKED")
        with self.assertRaises(PermissionError):
            self.backend.authenticate(token)


if __name__ == "__main__":
    unittest.main()
