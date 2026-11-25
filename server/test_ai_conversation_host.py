import unittest

from server.ai_conversation_host import AgentSessionError, AgentSessionRegistry, TwoAgentConversationHost
from server.ai_provider_host import AuthenticatedProviderHost, ProviderHostError
from server.auth import Authenticator
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore


class FakeClock:
    def __init__(self):
        self.now = 1000

    def __call__(self):
        return self.now


class TwoAgentConversationHostTest(unittest.TestCase):
    def setUp(self):
        self.tokens = {"token-a": "AI-A", "token-b": "AI-B"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(":memory:")
        self.backend = MessengerBackend(
            self.tokens, {"default": {"AI-A", "AI-B"}},
            store=self.store, authenticator=self.auth,
        )
        self.backend.create_conversation("token-a", "private-ab", ["AI-A", "AI-B"], "PRIVATE")
        self.backend.create_conversation("token-a", "group-ab", ["AI-A", "AI-B"], "GROUP")
        self.clock = FakeClock()
        self.calls = {"AI-A": [], "AI-B": []}

        def authorize(principal, conversation_id, agent_id):
            members = self.backend.conversation_members().get(conversation_id, set())
            return (principal == agent_id and len(members) == 2 and agent_id in members
                    and self.backend.conversation_kinds().get(conversation_id) == "PRIVATE")

        def resolve(agent_id):
            if agent_id not in self.calls:
                return None
            def invoke(prompt):
                self.calls[agent_id].append(prompt)
                return {"text": agent_id + " respondeu: " + prompt,
                        "providerId": "fake-" + agent_id, "model": "fake-model"}
            return invoke

        self.provider_host = AuthenticatedProviderHost(
            authenticate=self.backend.authenticate,
            authorize_agent=authorize,
            resolve_provider=resolve,
            attestation_key=b"m" * 32,
            clock=self.clock,
        )
        self.registry = AgentSessionRegistry(
            self.backend, clock=self.clock, ttl_seconds=60, max_sessions=10)
        self.host = TwoAgentConversationHost(self.backend, self.provider_host, self.registry)

    def tearDown(self):
        self.backend.close()

    def register_both(self):
        self.registry.register("token-a", "private-ab")
        self.registry.register("token-b", "private-ab")

    def test_each_participant_registers_its_own_session_and_peer_provider_runs(self):
        self.register_both()
        result = self.host.respond("token-a", {
            "conversationId": "private-ab", "agentId": "AI-B",
            "requestId": "m177-turn-1", "prompt": "Olá, IA-B",
        })
        message = result["message"]
        self.assertEqual(message["senderAiId"], "AI-B")
        self.assertEqual(message["recipientAiIds"], ["AI-A"])
        self.assertEqual(message["body"], "AI-B respondeu: Olá, IA-B")
        self.assertEqual(self.calls["AI-B"], ["Olá, IA-B"])
        self.assertEqual(self.calls["AI-A"], [])
        self.assertTrue(self.provider_host.verify_attestation(
            result["attestation"], message["body"]))

    def test_round_trip_can_invoke_both_independent_agent_sessions(self):
        self.register_both()
        first = self.host.respond("token-a", {
            "conversationId": "private-ab", "agentId": "AI-B",
            "requestId": "m177-turn-1", "prompt": "Comece a conversa",
        })
        second = self.host.respond("token-a", {
            "conversationId": "private-ab", "agentId": "AI-A",
            "requestId": "m177-turn-2", "prompt": first["message"]["body"],
        })
        self.assertEqual(first["message"]["senderAiId"], "AI-B")
        self.assertEqual(second["message"]["senderAiId"], "AI-A")
        self.assertEqual(self.calls["AI-B"], ["Comece a conversa"])
        self.assertEqual(self.calls["AI-A"], [first["message"]["body"]])
        self.assertEqual(len(self.backend.history("token-a", "private-ab")), 2)
        self.assertEqual(len(self.backend.history("token-b", "private-ab")), 2)

    def test_missing_peer_session_fails_before_provider_call(self):
        self.registry.register("token-a", "private-ab")
        with self.assertRaisesRegex(AgentSessionError, "agent_session_not_registered"):
            self.host.respond("token-a", {
                "conversationId": "private-ab", "agentId": "AI-B",
                "requestId": "m177-no-peer", "prompt": "Olá",
            })
        self.assertEqual(self.calls["AI-B"], [])

    def test_expired_session_is_not_resolved(self):
        self.registry.register("token-b", "private-ab")
        self.clock.now += 61
        with self.assertRaisesRegex(AgentSessionError, "agent_session_not_registered"):
            self.registry.resolve("private-ab", "AI-B")

    def test_registration_rejects_group_and_non_member_rooms(self):
        with self.assertRaisesRegex(AgentSessionError, "private_two_member_room_required"):
            self.registry.register("token-a", "group-ab")
        with self.assertRaisesRegex(AgentSessionError, "invalid_conversation_id"):
            self.registry.register("token-a", "")

    def test_unregistered_or_non_member_target_cannot_be_invoked(self):
        self.register_both()
        with self.assertRaisesRegex(AgentSessionError, "private_two_member_room_required"):
            self.host.respond("token-a", {
                "conversationId": "private-ab", "agentId": "AI-OUTSIDER",
                "requestId": "m177-outside", "prompt": "Olá",
            })
        self.assertEqual(self.calls["AI-A"], [])
        self.assertEqual(self.calls["AI-B"], [])

    def test_session_revocation_blocks_next_turn(self):
        self.register_both()
        self.assertTrue(self.registry.revoke("private-ab", "AI-B"))
        with self.assertRaisesRegex(AgentSessionError, "agent_session_not_registered"):
            self.host.respond("token-a", {
                "conversationId": "private-ab", "agentId": "AI-B",
                "requestId": "m177-revoked", "prompt": "Olá",
            })

    def test_registry_capacity_is_bounded(self):
        registry = AgentSessionRegistry(self.backend, clock=self.clock,
                                        ttl_seconds=60, max_sessions=2)
        registry.register("token-a", "private-ab")
        registry.register("token-b", "private-ab")
        self.backend.create_conversation("token-a", "private-cd", ["AI-A", "AI-B"], "PRIVATE")
        self.clock.now += 1
        with self.assertRaisesRegex(AgentSessionError, "session_registry_full"):
            registry.register("token-a", "private-cd")


if __name__ == "__main__":
    unittest.main()
