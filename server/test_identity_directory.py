import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore
from server.identity_directory import IdentityDirectory
from server.rate_limit import SlidingWindowRateLimiter


class IdentityDirectoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteMessengerStore(self.temp.name + "/messenger.sqlite")
        self.tokens = {"token-a": "AI-A", "token-b": "AI-B", "token-c": "AI-C"}
        self.auth = Authenticator(self.tokens)
        self.backend = MessengerBackend(
            self.tokens, {"room": {"AI-A", "AI-B"}}, self.store,
            authenticator=self.auth)
        self.directory = self.backend._identities
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

    def request(self, token, path):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {"Authorization": "Bearer " + token} if token else {}
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, payload

    def test_internal_numbers_are_stable_and_unique_after_restart(self):
        first = self.directory.get("AI-A")
        second = self.directory.get("AI-B")
        self.assertNotEqual(first["internalNumber"], second["internalNumber"])
        self.directory.provision("AI-A", "Assistente Alfa")
        self.assertEqual(self.directory.get("AI-A")["internalNumber"],
                         first["internalNumber"])
        self.assertEqual(self.directory.get("AI-A")["displayName"],
                         "Assistente Alfa")
        self.backend.close()
        self.store = SQLiteMessengerStore(self.temp.name + "/messenger.sqlite")
        reopened = IdentityDirectory(self.store._connection, self.tokens.values())
        self.assertEqual(reopened.get("AI-A")["internalNumber"],
                         first["internalNumber"])
        self.assertEqual(reopened.get("AI-A")["displayName"], "Assistente Alfa")

    def test_client_cannot_choose_internal_number_or_display_name(self):
        identity = self.directory.get("AI-A")
        self.assertEqual(set(identity), {
            "internalNumber", "aiId", "displayName", "createdAt"})
        with self.assertRaises(ValueError):
            self.directory.provision("AI-A", " " * 2)

    def test_room_identity_endpoint_is_member_scoped_and_authenticated(self):
        status, payload = self.request("token-a", "/v1/conversations/room/identities")
        self.assertEqual(status, 200)
        self.assertEqual({item["aiId"] for item in payload["participants"]},
                         {"AI-A", "AI-B"})
        for item in payload["participants"]:
            self.assertIsInstance(item["internalNumber"], int)
            self.assertTrue(item["displayName"])
            self.assertIn(item["status"], ("ONLINE", "OFFLINE"))
        status, payload = self.request("token-c", "/v1/conversations/room/identities")
        self.assertEqual(status, 403)
        status, payload = self.request("", "/v1/conversations/room/identities")
        self.assertEqual(status, 401)


if __name__ == "__main__":
    unittest.main()
