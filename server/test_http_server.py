import unittest
from server.auth import Authenticator
from server.http_server import MessengerHandler


class HttpContractTest(unittest.TestCase):
    def test_health_and_readiness_routes_are_defined(self):
        self.assertIn("/healthz", MessengerHandler.do_GET.__code__.co_consts)
        self.assertIn("/readyz", MessengerHandler.do_GET.__code__.co_consts)

    def test_guest_web_portal_route_is_defined(self):
        constants = MessengerHandler.do_GET.__code__.co_consts
        self.assertTrue(any(isinstance(value, tuple) and "/guest" in value for value in constants))
        self.assertTrue(hasattr(MessengerHandler, "_guest_web"))
        self.assertIn("/v1/guest-sessions/current", constants)

    def test_guest_session_exchange_and_logout_routes_are_defined(self):
        constants = MessengerHandler.do_POST.__code__.co_consts
        self.assertIn("/v1/guest-sessions", constants)
        self.assertIn("/v1/guest-sessions/logout", constants)

    def test_gpt6_web_route_is_defined(self):
        constants = MessengerHandler.do_GET.__code__.co_consts
        self.assertTrue(any(isinstance(value, tuple) and "/gpt6" in value for value in constants))
        self.assertTrue(hasattr(MessengerHandler, "_gpt6_web"))

    def test_wifi_policy_script_route_is_defined(self):
        self.assertIn("/wifi-only.js", MessengerHandler.do_GET.__code__.co_consts)
        self.assertTrue(hasattr(MessengerHandler, "_wifi_only_script"))

    def test_local_ai_capability_script_route_is_defined(self):
        self.assertIn("/local-ai-capability.js", MessengerHandler.do_GET.__code__.co_consts)
        self.assertTrue(hasattr(MessengerHandler, "_local_ai_capability_script"))

    def test_room_event_notification_script_route_is_defined(self):
        self.assertIn("/ai-room-event-notifications.js", MessengerHandler.do_GET.__code__.co_consts)
        self.assertTrue(hasattr(MessengerHandler, "_room_event_notifications_script"))

    def test_routes_are_defined(self):
        self.assertTrue(hasattr(MessengerHandler, "do_GET"))
        self.assertTrue(hasattr(MessengerHandler, "do_POST"))
        self.assertIn("/v1/messages", MessengerHandler.do_POST.__code__.co_consts)

    def test_local_ai_catalog_route_is_defined(self):
        self.assertIn("/v1/local-ai", MessengerHandler.do_GET.__code__.co_consts)
        self.assertIn("LOCAL_AI_CATALOG_READ", MessengerHandler.do_GET.__code__.co_consts)

    def test_authenticated_operations_summary_route_is_defined(self):
        self.assertIn("/v1/operations/summary", MessengerHandler.do_GET.__code__.co_consts)
        self.assertIn("summary", MessengerHandler.do_GET.__code__.co_names)

    def test_local_ai_catalog_exposes_inference_contract_without_execution_route(self):
        constants = MessengerHandler.do_GET.__code__.co_consts
        self.assertTrue(any(
            isinstance(value, tuple) and "inferenceContract" in value
            for value in constants
        ))
        self.assertIn("/v1/local-ai", constants)
        self.assertNotIn("/v1/local-ai/execute", constants)

    def test_provider_catalog_route_is_defined(self):
        self.assertIn("/v1/providers", MessengerHandler.do_GET.__code__.co_consts)
        self.assertTrue(hasattr(MessengerHandler, "provider_registry"))


    def test_gpt6_status_distinguishes_request_success_from_online_presence(self):
        constants = MessengerHandler.do_GET.__code__.co_consts
        self.assertIn("connection_status", constants)
        status_fields = next(
            (value for value in constants
             if isinstance(value, tuple) and "connectionState" in value),
            (),
        )
        self.assertIn("accountSessionConnected", status_fields)
        self.assertIn("online", status_fields)

    def test_paid_provider_routes_have_fail_closed_policy_guard(self):
        constants = MessengerHandler.do_POST.__code__.co_consts
        self.assertIn("openai_api_calls_disabled", constants)

    def test_authentication_boundary_is_present(self):
        self.assertTrue(hasattr(MessengerHandler, "_principal"))
        self.assertIn("authentication_required", MessengerHandler.do_GET.__code__.co_consts)

    def test_revoked_credential_is_rejected_before_protected_work(self):
        auth = Authenticator({"token-a": "AI-A"})
        auth.revoke("token-a")
        with self.assertRaises(PermissionError):
            auth.authenticate("token-a")

    def test_authenticated_conversation_runtime_assets_are_allowlisted(self):
        constants = MessengerHandler.do_GET.__code__.co_consts
        for asset in (
            "/ai-conversation-loop.js",
            "/ai-agent-adapter.js",
            "/ai-conversation-runtime.js",
            "/ai-conversation-panel.js",
        ):
            self.assertIn(asset, constants)
        self.assertTrue(hasattr(MessengerHandler, "_ai_conversation_script"))

    def test_conversation_asset_handler_rejects_unlisted_files(self):
        import inspect
        source = inspect.getsource(MessengerHandler._ai_conversation_script)
        self.assertIn("allowed = {", source)
        self.assertIn('if filename not in allowed:', source)
        self.assertIn("ai_conversation_script_not_found", source)


if __name__ == "__main__":
    unittest.main()

