import json
import tempfile
import threading
import unittest
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.identity_registry import IdentityRegistry
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore


class IdentityRegistryHttpTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        path = self.temp.name + "/messenger.sqlite"
        tokens = {"secret-alpha": "AI-ALPHA", "secret-bravo": "AI-BRAVO"}
        self.auth = Authenticator(tokens)
        self.store = SQLiteMessengerStore(path)
        self.backend = MessengerBackend(tokens, {"default": set(tokens.values())},
                                        self.store, authenticator=self.auth)
        self.registry = IdentityRegistry(path)
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.identity_registry = self.registry
        MessengerHandler.operational = None
        self.server = HTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.registry.close()
        self.backend.close()
        self.temp.cleanup()

    def get(self, path, token=None):
        headers = {}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = Request(self.base + path, headers=headers)
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def test_authenticated_self_registration_is_idempotent(self):
        status, first = self.get("/v1/me/phone", "secret-alpha")
        again_status, again = self.get("/v1/me/phone", "secret-alpha")
        self.assertEqual(status, 200)
        self.assertEqual(again_status, 200)
        self.assertEqual(first["phone"]["displayNumber"], "AI-PHONE-000001")
        self.assertEqual(first["phone"], again["phone"])

    def test_authenticated_phone_number_lookup(self):
        self.get("/v1/me/phone", "secret-alpha")
        status, result = self.get("/v1/phones/AI-PHONE-000001", "secret-bravo")
        self.assertEqual(status, 200)
        self.assertEqual(result["phone"]["aiId"], "AI-ALPHA")

    def test_registry_routes_require_authentication(self):
        status, result = self.get("/v1/me/phone")
        self.assertEqual(status, 401)
        self.assertEqual(result["error"], "authentication_required")

    def test_unknown_number_returns_not_found(self):
        status, result = self.get("/v1/phones/AI-PHONE-999999", "secret-alpha")
        self.assertEqual(status, 404)
        self.assertEqual(result["error"], "phone_not_found")


if __name__ == "__main__":
    unittest.main()
