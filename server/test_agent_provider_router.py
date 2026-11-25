import json
import os
import unittest
from unittest.mock import patch, MagicMock

from server.agent_provider_router import AgentProviderRouter
from server.provider_adapters import AnthropicTextAdapter, GeminiTextAdapter


class FakeAdapter:
    model = "fake-v1"
    def __init__(self, configured=True, enabled=True):
        self.configured, self.allowed, self.calls = configured, enabled, []
    def enabled(self): return self.configured
    def api_calls_enabled(self): return self.allowed
    def respond(self, prompt):
        self.calls.append(prompt)
        return {"text": "reply:" + prompt, "model": self.model}


class AgentProviderRouterTest(unittest.TestCase):
    def test_routes_two_agents_to_distinct_provider_adapters(self):
        a, b = FakeAdapter(), FakeAdapter()
        router = AgentProviderRouter({"anthropic": a, "google_gemini": b},
            {"AI-A": "anthropic", "AI-B": "google_gemini"})
        self.assertEqual(router.resolve("AI-A")("hello")["providerId"], "anthropic")
        self.assertEqual(router.resolve("AI-B")("world")["providerId"], "google_gemini")
        self.assertEqual(a.calls, ["hello"])
        self.assertEqual(b.calls, ["world"])

    def test_unassigned_or_disabled_provider_fails_closed(self):
        disabled = FakeAdapter(configured=True, enabled=False)
        router = AgentProviderRouter({"anthropic": disabled}, {"AI-A": "anthropic"})
        self.assertIsNone(router.resolve("AI-A"))
        self.assertIsNone(router.resolve("AI-B"))
        self.assertEqual(router.readiness(["AI-A", "AI-B"])[0]["state"], "DISABLED_BY_POLICY")
        self.assertEqual(router.readiness(["AI-B"])[0]["state"], "NOT_CONFIGURED")

    def test_invalid_assignments_rejected(self):
        for value in ('{"AI-A":"unknown"}', '{"not-an-ai":"openai"}', '[]', '{'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                AgentProviderRouter({}, value)

    def test_readiness_never_exposes_credentials(self):
        router = AgentProviderRouter({"anthropic": FakeAdapter()},
                                     {"AI-A": "anthropic"})
        encoded = json.dumps(router.readiness(["AI-A"]))
        self.assertNotIn("secret", encoded)
        self.assertNotIn("api_key", encoded)


class ProviderAdapterGateTest(unittest.TestCase):
    def test_anthropic_is_disabled_by_default_even_with_key(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_CALLS_ENABLED": "false"}):
            adapter = AnthropicTextAdapter(api_key="private-test-key")
            self.assertTrue(adapter.enabled())
            self.assertFalse(adapter.api_calls_enabled())
            with self.assertRaisesRegex(RuntimeError, "anthropic_api_calls_disabled"):
                adapter.respond("hello")

    def test_gemini_is_disabled_by_default_even_with_key(self):
        with patch.dict(os.environ, {"GEMINI_API_CALLS_ENABLED": "false"}):
            adapter = GeminiTextAdapter(api_key="private-test-key")
            self.assertTrue(adapter.enabled())
            self.assertFalse(adapter.api_calls_enabled())
            with self.assertRaisesRegex(RuntimeError, "google_gemini_api_calls_disabled"):
                adapter.respond("hello")


    def test_anthropic_adapter_uses_messages_endpoint_and_private_header(self):
        import json
        payload = {"id": "msg-test", "model": "claude-test",
                   "content": [{"type": "text", "text": "Claude respondeu"}]}
        response = MagicMock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps(payload).encode()
        with patch.dict(os.environ, {"ANTHROPIC_API_CALLS_ENABLED": "true"}), \\
             patch("server.provider_adapters.urllib.request.urlopen", return_value=response) as call:
            result = AnthropicTextAdapter(api_key="private-anthropic-key").respond("oi")
        request = call.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(request.get_header("X-api-key"), "private-anthropic-key")
        self.assertEqual(json.loads(request.data)["messages"][0]["content"], "oi")
        self.assertEqual(result["text"], "Claude respondeu")
        self.assertEqual(result["responseId"], "msg-test")

    def test_gemini_adapter_uses_generate_content_and_private_header(self):
        import json
        payload = {"responseId": "gemini-test", "model": "gemini-test",
                   "candidates": [{"content": {"parts": [{"text": "Gemini respondeu"}]}}]}
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps(payload).encode()
        with patch.dict(os.environ, {"GEMINI_API_CALLS_ENABLED": "true"}), \\
             patch("server.provider_adapters.urllib.request.urlopen", return_value=response) as call:
            result = GeminiTextAdapter(api_key="private-gemini-key").respond("oi")
        request = call.call_args.args[0]
        self.assertIn(":generateContent", request.full_url)
        self.assertNotIn("private-gemini-key", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "private-gemini-key")
        self.assertEqual(json.loads(request.data)["contents"][0]["parts"][0]["text"], "oi")
        self.assertEqual(result["text"], "Gemini respondeu")

    def test_provider_adapters_reject_empty_and_oversized_prompts(self):
        for adapter in (AnthropicTextAdapter(api_key="k"),
                        GeminiTextAdapter(api_key="k")):
            with self.assertRaises(ValueError): adapter.respond("")
            with self.assertRaises(ValueError): adapter.respond("x" * 5001)


if __name__ == "__main__":
    unittest.main()
