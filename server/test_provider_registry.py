import unittest
from server.provider_registry import ProviderRegistry


class FakeOpenAI:
    def __init__(self, enabled):
        self._enabled = enabled

    def enabled(self):
        return self._enabled

    def api_calls_enabled(self):
        return False


class ProviderRegistryTest(unittest.TestCase):
    def test_openai_key_configuration_is_not_reported_as_online(self):
        provider = ProviderRegistry(FakeOpenAI(True)).get_provider("openai")
        self.assertTrue(provider["configured"])
        self.assertEqual(provider["connectionState"], "DISABLED_BY_POLICY")
        self.assertFalse(provider["apiCallsEnabled"])
        self.assertEqual(provider["capabilities"], [])
        self.assertFalse(provider["online"])
        self.assertFalse(provider["accountSessionConnected"])
        self.assertEqual(provider["identityType"], "project_api_credential")

    def test_missing_openai_key_is_not_configured(self):
        provider = ProviderRegistry(FakeOpenAI(False)).get_provider("openai")
        self.assertFalse(provider["configured"])
        self.assertEqual(provider["connectionState"], "DISABLED_BY_POLICY")
        self.assertFalse(provider["apiCallsEnabled"])

    def test_paid_capabilities_appear_only_when_gate_is_open(self):
        class EnabledOpenAI(FakeOpenAI):
            def api_calls_enabled(self):
                return True
        provider = ProviderRegistry(EnabledOpenAI(True)).get_provider("openai")
        self.assertTrue(provider["apiCallsEnabled"])
        self.assertIn("text_response", provider["capabilities"])

    def test_other_providers_are_explicitly_not_implemented(self):
        providers = ProviderRegistry(FakeOpenAI(False)).list_providers()
        by_id = {item["providerId"]: item for item in providers}
        for provider_id in ("anthropic", "google_gemini"):
            self.assertEqual(by_id[provider_id]["implementation"], "NOT_IMPLEMENTED")
            self.assertEqual(by_id[provider_id]["connectionState"], "NOT_CONFIGURED")
            self.assertFalse(by_id[provider_id]["online"])

    def test_catalog_never_contains_credential_values(self):
        registry = ProviderRegistry(FakeOpenAI(True))
        serialized = repr(registry.list_providers())
        self.assertNotIn("test-key", serialized)
        self.assertIn("OPENAI_API_KEY", serialized)

    def test_successful_request_state_is_not_online_or_account_session(self):
        class VerifiedOpenAI(FakeOpenAI):
            def connection_status(self):
                return {
                    "connectionState": "REQUEST_SUCCEEDED",
                    "lastSuccessfulRequestAt": "2026-11-24T00:00:00+00:00",
                    "lastResponseId": "resp_test",
                    "lastSuccessfulModel": "test-model",
                    "online": False,
                    "accountSessionConnected": False,
                }
        provider = ProviderRegistry(VerifiedOpenAI(True)).get_provider("openai")
        self.assertEqual(provider["connectionState"], "REQUEST_SUCCEEDED")
        self.assertEqual(provider["lastResponseId"], "resp_test")
        self.assertFalse(provider["online"])
        self.assertFalse(provider["accountSessionConnected"])

    def test_unknown_provider_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "provider_not_supported"):
            ProviderRegistry().get_provider("unknown")


if __name__ == "__main__":
    unittest.main()
