import unittest

from server.agent_provider_registry import AgentProviderBindingRegistry


class AgentProviderBindingRegistryTests(unittest.TestCase):
    def test_bindings_are_independent_per_ai_identity(self):
        registry = AgentProviderBindingRegistry({"openai", "anthropic"})
        first = registry.bind("AI-01", "openai", "secret-ref-ai-01", "model-a", enabled=True)
        second = registry.bind("AI-02", "anthropic", "secret-ref-ai-02", "model-b", enabled=True)
        self.assertEqual(first.ai_id, "AI-01")
        self.assertEqual(second.ai_id, "AI-02")
        self.assertEqual(registry.resolve_enabled("AI-01").provider_id, "openai")
        self.assertEqual(registry.resolve_enabled("AI-02").provider_id, "anthropic")

    def test_registry_never_accepts_secret_value_as_an_identity_binding(self):
        registry = AgentProviderBindingRegistry({"openai"})
        binding = registry.bind("AI-01", "openai", "env:AI01_OPENAI_KEY", enabled=False)
        self.assertEqual(binding.credential_ref, "env:AI01_OPENAI_KEY")
        self.assertFalse(binding.enabled)

    def test_unknown_provider_is_rejected(self):
        registry = AgentProviderBindingRegistry({"openai"})
        with self.assertRaisesRegex(ValueError, "provider_not_supported"):
            registry.bind("AI-01", "unknown", "env:UNKNOWN")

    def test_unbinding_is_explicit(self):
        registry = AgentProviderBindingRegistry({"openai"})
        registry.bind("AI-01", "openai", "env:AI01_OPENAI_KEY")
        self.assertIsNotNone(registry.unbind("AI-01"))
        self.assertIsNone(registry.get("AI-01"))


if __name__ == "__main__":
    unittest.main()
