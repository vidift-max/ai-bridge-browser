import json
import os
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
from server.rate_limit import SlidingWindowRateLimiter


class ToolHubHttpTest(unittest.TestCase):
    def setUp(self):
        self.old_admin_token = os.environ.get("TOOL_HUB_ADMIN_TOKEN")
        os.environ["TOOL_HUB_ADMIN_TOKEN"] = "test-tool-hub-admin-token-" + ("x" * 32)
        self.admin_token = os.environ["TOOL_HUB_ADMIN_TOKEN"]
        self.tokens = {"token-a": "AI-A", "token-b": "AI-B"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(":memory:")
        self.backend = MessengerBackend(
            self.tokens, {"room": {"AI-A", "AI-B"}}, self.store, authenticator=self.auth
        )
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter()
        MessengerHandler.tool_hub = ToolHubService(permissions=ToolPermissionRegistry(store=self.store))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.backend.close()
        MessengerHandler.tool_hub = None
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter()
        if self.old_admin_token is None:
            os.environ.pop("TOOL_HUB_ADMIN_TOKEN", None)
        else:
            os.environ["TOOL_HUB_ADMIN_TOKEN"] = self.old_admin_token

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
        status, payload = self.request(
            "POST", "/v1/tools/duration_timer/invoke", "token-b",
            {"requestId": "123e4567-e89b-42d3-a456-426614174000",
             "toolVersion": "1.0.0", "input": {"duration": "1m"}}
        )
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"], "forbidden")

    def test_body_cannot_spoof_principal_or_inherit_another_ai_grant(self):
        status, payload = self.request(
            "POST", "/v1/tools/duration_timer/invoke", "token-b",
            body={"aiId": "AI-A", "principalAiId": "AI-A", "toolId": "duration_timer"}
        )
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"], "forbidden")

    def test_authorized_agent_can_invoke_duration_timer(self):
        MessengerHandler.tool_hub.permissions.grant("AI-A", "duration_timer", "test-fixture")
        status, payload = self.request(
            "POST", "/v1/tools/duration_timer/invoke", "token-a",
            {"requestId": "123e4567-e89b-42d3-a456-426614174000",
             "toolVersion": "1.0.0", "input": {"duration": "90s"}}
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "SUCCEEDED")
        self.assertEqual(payload["result"]["seconds"], 90)
        self.assertTrue(any(
            event.event_type == "TOOL_INVOCATION_ATTEMPTED"
            and event.ai_id == "AI-A"
            for event in self.auth.audit_log.events()
        ))

    def test_unknown_tool_is_not_found(self):
        status, payload = self.request(
            "POST", "/v1/tools/unknown_tool/invoke", "token-a",
            {"requestId": "123e4567-e89b-42d3-a456-426614174000",
             "toolVersion": "1.0.0", "input": {}}
        )
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "tool_not_found")

    def test_ready_tool_adapter_returns_validation_error_for_bad_input(self):
        MessengerHandler.tool_hub.permissions.grant("AI-A", "duration_timer", "test-fixture")
        status, payload = self.request(
            "POST", "/v1/tools/duration_timer/invoke", "token-a",
            {"requestId": "123e4567-e89b-42d3-a456-426614174000",
             "toolVersion": "1.0.0", "input": {"duration": "not-a-duration"}}
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "INVALID_FORMAT")



    def test_capability_discovery_is_rate_limited_per_principal(self):
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=60)
        first_status, _ = self.request("GET", "/v1/tools/capabilities", "token-a")
        second_status, payload = self.request("GET", "/v1/tools/capabilities", "token-a")
        self.assertEqual(first_status, 200)
        self.assertEqual(second_status, 429)
        self.assertEqual(payload["error"], "rate_limit_exceeded")

    def test_invocation_attempts_are_rate_limited_per_principal(self):
        MessengerHandler.tool_hub.permissions.grant("AI-A", "duration_timer", "test-fixture")
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=60)
        body = {"requestId": "123e4567-e89b-42d3-a456-426614174000",
                "toolVersion": "1.0.0", "input": {"duration": "1m"}}
        first_status, _ = self.request("POST", "/v1/tools/duration_timer/invoke", "token-a", body)
        second_status, payload = self.request("POST", "/v1/tools/duration_timer/invoke", "token-a", body)
        self.assertEqual(first_status, 200)
        self.assertEqual(second_status, 429)
        self.assertEqual(payload["error"], "rate_limit_exceeded")


    def test_admin_routes_fail_closed_without_admin_credentials(self):
        os.environ.pop("TOOL_HUB_ADMIN_TOKEN", None)
        status, payload = self.request("GET", "/v1/admin/tool-permissions")
        self.assertEqual(status, 503)
        self.assertEqual(payload["error"], "tool_admin_not_configured")

    def test_admin_permission_listing_requires_admin_token(self):
        status, payload = self.request("GET", "/v1/admin/tool-permissions", "token-a")
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"], "tool_admin_forbidden")

    def test_admin_can_grant_list_and_revoke_durable_permission(self):
        status, payload = self.request(
            "POST", "/v1/admin/tool-permissions", self.admin_token,
            {"principalAiId": "AI-A", "toolId": "duration_timer"}
        )
        self.assertEqual(status, 201)
        self.assertEqual(payload["grant"]["principalAiId"], "AI-A")
        self.assertEqual(payload["grant"]["grantedBy"], "tool-hub-admin")

        status, listing = self.request("GET", "/v1/admin/tool-permissions", self.admin_token)
        self.assertEqual(status, 200)
        self.assertEqual(len(listing["grants"]), 1)
        self.assertEqual(listing["grants"][0]["toolId"], "duration_timer")

        status, revoked = self.request(
            "DELETE", "/v1/admin/tool-permissions/AI-A/duration_timer", self.admin_token
        )
        self.assertEqual(status, 200)
        self.assertTrue(revoked["revoked"])
        self.assertFalse(MessengerHandler.tool_hub.permissions.can_use("AI-A", "duration_timer"))
        status, audit = self.request(
            "GET", "/v1/admin/tool-permissions/audit", self.admin_token
        )
        self.assertEqual(status, 200)
        self.assertEqual([event["action"] for event in audit["events"]], ["GRANT", "REVOKE"])
        self.assertEqual([event["actorId"] for event in audit["events"]],
                         ["tool-hub-admin", "tool-hub-admin"])

        events = [event.event_type for event in self.auth.audit_log.events()]
        self.assertIn("TOOL_PERMISSION_GRANTED", events)
        self.assertIn("TOOL_PERMISSION_REVOKED", events)

    def test_admin_cannot_grant_unknown_tool_or_malformed_principal(self):
        status, payload = self.request(
            "POST", "/v1/admin/tool-permissions", self.admin_token,
            {"principalAiId": "AI-A", "toolId": "shell_exec"}
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "invalid_tool_permission")
        status, payload = self.request(
            "POST", "/v1/admin/tool-permissions", self.admin_token,
            {"principalAiId": " AI-A", "toolId": "duration_timer"}
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "invalid_tool_permission")

    def test_admin_grants_are_persisted_in_sqlite(self):
        status, _ = self.request(
            "POST", "/v1/admin/tool-permissions", self.admin_token,
            {"principalAiId": "AI-A", "toolId": "duration_timer"}
        )
        self.assertEqual(status, 201)
        self.assertTrue(MessengerHandler.tool_hub.permissions.can_use("AI-A", "duration_timer"))
        self.assertFalse(MessengerHandler.tool_hub.permissions.can_use("AI-B", "duration_timer"))
        status, capabilities = self.request("GET", "/v1/tools/capabilities", "token-a")
        self.assertEqual(status, 200)
        self.assertEqual([tool["toolId"] for tool in capabilities["tools"]], ["duration_timer"])
        status, invocation = self.request(
            "POST", "/v1/tools/duration_timer/invoke", "token-a",
            {"requestId": "123e4567-e89b-42d3-a456-426614174000",
             "toolVersion": "1.0.0", "input": {"duration": "2m"}}
        )
        self.assertEqual(status, 200)
        self.assertEqual(invocation["result"]["seconds"], 120)

if __name__ == "__main__":
    unittest.main()
