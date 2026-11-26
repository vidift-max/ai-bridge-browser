import unittest

from server.auth import Authenticator
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore
from server.ai_provider_host import ProviderHostError
from server.two_agent_runtime import build_two_agent_runtime


class FakeAdapter:
    def __init__(self, provider_id, *, calls_enabled=True):
        self.provider_id = provider_id
        self.calls_enabled = calls_enabled
        self.calls = []

    def enabled(self):
        return True

    def api_calls_enabled(self):
        return self.calls_enabled

    def respond(self, prompt):
        self.calls.append(prompt)
        return {
            "text": self.provider_id + " respondeu: " + prompt,
            "providerId": self.provider_id,
            "model": self.provider_id + "-test",
        }


class TwoAgentRuntimeCompositionTest(unittest.TestCase):
    def setUp(self):
        self.tokens = {"user-token": "AI-USER", "peer-token": "AI-PEER"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(":memory:")
        self.backend = MessengerBackend(
            self.tokens, {"default": {"AI-USER", "AI-PEER"}},
            store=self.store, authenticator=self.auth)
        self.backend.create_conversation(
            "user-token", "private-two-ai", ["AI-USER", "AI-PEER"], "PRIVATE")
        self.openai = FakeAdapter("openai")
        self.anthropic = FakeAdapter("anthropic")
        self.adapters = {"openai": self.openai, "anthropic": self.anthropic}
        self.assignments = {"AI-USER": "openai", "AI-PEER": "anthropic"}

    def tearDown(self):
        self.backend.close()

    def build(self, *, key="11" * 32, assignments=None):
        return build_two_agent_runtime(
            self.backend, self.tokens, self.adapters,
            host_key_hex=key,
            assignments=self.assignments if assignments is None else assignments)

    def test_missing_host_key_keeps_runtime_fail_closed(self):
        runtime = self.build(key="")
        self.assertIsNotNone(runtime.router)
        self.assertIsNone(runtime.provider_host)
        self.assertIsNone(runtime.session_registry)
        self.assertIsNone(runtime.conversation_host)

    def test_invalid_or_wrong_length_host_key_is_rejected(self):
        for key in ("not-hex", "11" * 31, "11" * 33, "11" * 31 + " 11"):
            with self.subTest(key_length=len(key)):
                with self.assertRaisesRegex(RuntimeError, "AI_PROVIDER_HOST_HMAC_KEY_HEX"):
                    self.build(key=key)

    def test_production_composition_supports_two_independent_authenticated_turns(self):
        runtime = self.build()
        self.assertIsNotNone(runtime.provider_host)
        self.assertIsNotNone(runtime.session_registry)
        self.assertIsNotNone(runtime.conversation_host)
        first_session = runtime.session_registry.register("user-token", "private-two-ai")
        second_session = runtime.session_registry.register("peer-token", "private-two-ai")
        self.assertEqual(first_session["aiId"], "AI-USER")
        self.assertEqual(second_session["aiId"], "AI-PEER")

        first = runtime.conversation_host.respond("user-token", {
            "conversationId": "private-two-ai", "agentId": "AI-PEER",
            "requestId": "m190-user-to-peer", "prompt": "Olá, IA parceira.",
        })
        second = runtime.conversation_host.respond("peer-token", {
            "conversationId": "private-two-ai", "agentId": "AI-USER",
            "requestId": "m190-peer-to-user", "prompt": first["message"]["body"],
        })
        self.assertEqual(first["message"]["senderAiId"], "AI-PEER")
        self.assertEqual(second["message"]["senderAiId"], "AI-USER")
        self.assertEqual(first["attestation"]["statement"]["providerId"], "anthropic")
        self.assertEqual(second["attestation"]["statement"]["providerId"], "openai")
        self.assertTrue(runtime.provider_host.verify_attestation(
            first["attestation"], first["message"]["body"]))
        self.assertTrue(runtime.provider_host.verify_attestation(
            second["attestation"], second["message"]["body"]))
        expected = [first["message"]["messageId"], second["message"]["messageId"]]
        for token in ("user-token", "peer-token"):
            self.assertEqual(
                [item.message_id for item in self.backend.history(token, "private-two-ai")],
                expected)
        self.assertEqual(self.anthropic.calls, ["Olá, IA parceira."])
        self.assertEqual(self.openai.calls, [first["message"]["body"]])

    def test_provider_policy_disabled_blocks_execution_without_fallback(self):
        self.anthropic.calls_enabled = False
        runtime = self.build()
        runtime.session_registry.register("user-token", "private-two-ai")
        runtime.session_registry.register("peer-token", "private-two-ai")
        with self.assertRaises(ProviderHostError):
            runtime.conversation_host.respond("user-token", {
                "conversationId": "private-two-ai", "agentId": "AI-PEER",
                "requestId": "m190-policy-off", "prompt": "Não deve sair.",
            })
        self.assertEqual(self.anthropic.calls, [])
        self.assertEqual(self.openai.calls, [])

    def test_unassigned_identity_cannot_be_invoked(self):
        runtime = self.build(assignments={"AI-USER": "openai"})
        self.assertIsNone(runtime.router.resolve("AI-PEER"))
        self.assertIsNotNone(runtime.router.resolve("AI-USER"))


if __name__ == "__main__":
    unittest.main()
