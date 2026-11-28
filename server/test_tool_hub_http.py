import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore
from server.tool_permissions import ToolPermissionRegistry
from server.tool_hub import ToolHubService


class ToolHubHttpTest(unittest.TestCase):
    def setUp(self):
        self.tokens = {"token-a": "AI-A", "token-b": "AI-B"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(":memory:")
        self.backend = MessengerBackend(
            self.tokens, {"room": {"AI-A", "AI-B"}}, self.store, authenticator=self.auth
        )
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.tool_hub = ToolHubService(
            permissions=ToolPermissionRegistry({"AI-A": {"duration_timer"}})
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.backend.close()
        MessengerHandler.tool_hub = None

    def request(self, method, path, token=None, body=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        encoded_body = None
        if body is not None:
            encoded_body = json.dumps(body)
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=encoded_body, headers=headers)
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, payload

    def test_capability_discovery_requires_authentication(self):
        status, payload = self.request("GET", "/v1/tools/capabilities")
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "authentication_required")

    def test_capability_discovery_returns_no_blocked_tools(self):
        status, payload = self.request("GET", "/v1/tools/capabilities", "token-a")
        self.assertEqual(status, 200)
        self.assertEqual(payload["principalAiId"], "AI-A")
        self.assertEqual(payload["tools"], [])

    def test_discovery_does_not_leak_other_principals_grants(self):
        status, payload = self.request("GET", "/v1/tools/capabilities", "token-b")
        self.assertEqual(status, 200)
        self.assertEqual(payload["tools"], [])

    def test_invocation_without_grant_is_forbidden(self):
        status, payload = self.request("POST", "/v1/tools/duration_timer/invoke", "token-b")
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"], "forbidden")

    def test_body_cannot_spoof_principal_or_inherit_another_ai_grant(self):
        status, payload = self.request(
            "POST", "/v1/tools/duration_timer/invoke", "token-b",
            body={"aiId": "AI-A", "principalAiId": "AI-A", "toolId": "duration_timer"}
        )
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"], "forbidden")

    def test_invocation_of_blocked_tool_is_conflict_even_with_grant(self):
        status, payload = self.request("POST", "/v1/tools/duration_timer/invoke", "token-a")
        self.assertEqual(status, 409)
        self.assertEqual(payload["error"], "tool_unavailable")

    def test_unknown_tool_is_not_found(self):
        status, payload = self.request("POST", "/v1/tools/unknown_tool/invoke", "token-a")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "tool_not_found")

    def test_ready_tool_still_cannot_execute_without_adapter(self):
        service = MessengerHandler.tool_hub
        service._catalog["duration_timer"].update({"status": "READY", "enabled": True})
        status, payload = self.request("POST", "/v1/tools/duration_timer/invoke", "token-a")
        self.assertEqual(status, 501)
        self.assertEqual(payload["error"], "tool_adapter_not_implemented")


if __name__ == "__main__":
    unittest.main()
