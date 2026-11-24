import unittest
from server.provider_registry import ProviderRegistry


class FakeOpenAI:
    def __init__(self, enabled):
        self._enabled = enabled

    def enabled(self):
        return self._enabled


class ProviderRegistryTest(unittest.TestCase):
    def test_openai_key_configuration_is_not_reported_as_online(self):
        provider = ProviderRegistry(FakeOpenAI(True)).get_provider("openai")
        self.assertTrue(provider["configured"])
        self.assertEqual(provider["connectionState"], "CONFIGURED_UNVERIFIED")
        self.assertFalse(provider["online"])
        self.assertFalse(provider["accountSessionConnected"])
        self.assertEqual(provider["identityType"], "project_api_credential")

    def test_missing_openai_key_is_not_configured(self):
        provider = ProviderRegistry(FakeOpenAI(False)).get_provider("openai")
        self.assertFalse(provider["configured"])
        self.assertEqual(provider["connectionState"], "NOT_CONFIGURED")

    def test_other_providers_are_explicitly_not_implemented(self):
        providers = ProviderRegistry(FakeOpenAI(False)).list_providers()
        by_id = {item["providerId"]: item for item in providers}
        for provider_id in ("anthropic", "google_gemini"):
            self.assertEqual(by_id[provider_id]["implementation"], "NOT_IMPLEMENTED")
            self.assertEqual(by_id[provider_id]["connectionState"], "NOT_IMPLEMENTED")
            self.assertFalse(by_id[provider_id]["online"])

    def test_catalog_never_contains_credential_values(self):
        registry = ProviderRegistry(FakeOpenAI(True))
        serialized = repr(registry.list_providers())
        self.assertNotIn("test-key", serialized)
        self.assertIn("OPENAI_API_KEY", serialized)

    def test_unknown_provider_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "provider_not_supported"):
            ProviderRegistry().get_provider("unknown")


if __name__ == "__main__":
    unittest.main()
