import unittest

from server.gpt6_room_agent import GPT6RoomAgent
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore


class FakeAdapter:
    def __init__(self, enabled=True, calls_enabled=True):
        self._enabled = enabled
        self._calls_enabled = calls_enabled
        self.calls = []

    def enabled(self):
        return self._enabled

    def api_calls_enabled(self):
        return self._calls_enabled

    def respond(self, text):
        self.calls.append(text)
        return {"responseId": "resp-test-1", "model": "mock-model",
                "text": "Resposta GPT-6: " + text}


class GPT6RoomAgentTest(unittest.TestCase):
    def setUp(self):
        self.tokens = {
            "user-token": "AI-USER",
            "peer-token": "AI-PEER",
            "outsider-token": "AI-OUTSIDER",
        }
        self.store = SQLiteMessengerStore(":memory:")
        self.backend = MessengerBackend(
            self.tokens,
            {"shared-room": {"AI-USER", "AI-PEER", "AI-GPT6"}},
            store=self.store,
            internal_ai_ids={"AI-GPT6"},
            identity_display_names={"AI-GPT6": "GPT-6"},
        )
        self.adapter = FakeAdapter()
        self.agent = GPT6RoomAgent(self.backend, self.adapter)

    def tearDown(self):
        self.backend.close()

    def test_user_and_gpt6_messages_are_persisted_for_every_room_participant(self):
        result = self.agent.respond(
            "user-token", "shared-room", "Olá, GPT-6!", "request-0001")
        self.assertEqual(result["userMessage"]["senderAiId"], "AI-USER")
        self.assertEqual(result["assistantMessage"]["senderAiId"], "AI-GPT6")
        self.assertEqual(result["assistant"]["displayName"], "GPT-6")
        self.assertEqual(result["assistantMessage"]["body"], "Resposta GPT-6: Olá, GPT-6!")
        peer_history = self.backend.history("peer-token", "shared-room")
        self.assertEqual([item.sender_ai_id for item in peer_history],
                         ["AI-USER", "AI-GPT6"])
        self.assertEqual(self.adapter.calls, ["Olá, GPT-6!"])

    def test_same_request_retry_returns_persisted_reply_without_second_provider_call(self):
        first = self.agent.respond(
            "user-token", "shared-room", "Teste de repetição", "request-0002")
        second = self.agent.respond(
            "user-token", "shared-room", "Teste de repetição", "request-0002")
        self.assertEqual(first["assistantMessage"]["messageId"],
                         second["assistantMessage"]["messageId"])
        self.assertFalse(first["idempotentReplay"])
        self.assertTrue(second["idempotentReplay"])
        self.assertEqual(len(self.adapter.calls), 1)

    def test_reusing_request_id_with_changed_payload_is_rejected(self):
        self.agent.respond("user-token", "shared-room", "Original", "request-0003")
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            self.agent.respond("user-token", "shared-room", "Alterada", "request-0003")
        self.assertEqual(len(self.adapter.calls), 1)

    def test_room_without_gpt6_membership_is_rejected_before_provider_call(self):
        self.backend.create_conversation(
            "user-token", "ordinary-room", ["AI-USER", "AI-PEER"], "GROUP")
        with self.assertRaisesRegex(ValueError, "gpt6_not_room_member"):
            self.agent.respond("user-token", "ordinary-room", "Olá", "request-0004")
        self.assertEqual(self.adapter.calls, [])

    def test_non_member_cannot_trigger_gpt6_in_another_room(self):
        with self.assertRaisesRegex(PermissionError, "authorization_denied"):
            self.agent.respond(
                "outsider-token", "shared-room", "Olá", "request-0005")
        self.assertEqual(self.adapter.calls, [])

    def test_paid_api_gate_blocks_before_room_message_is_written(self):
        disabled = GPT6RoomAgent(self.backend, FakeAdapter(calls_enabled=False))
        with self.assertRaisesRegex(RuntimeError, "openai_api_calls_disabled"):
            disabled.respond("user-token", "shared-room", "Olá", "request-0006")
        self.assertEqual(self.backend.history("user-token", "shared-room"), [])

    def test_internal_identity_cannot_be_spoofed_by_regular_participant(self):
        with self.assertRaisesRegex(PermissionError, "internal_identity_not_authorized"):
            self.backend.submit_internal(
                "AI-USER", "forged", "shared-room", ["AI-PEER"], "falso", "forged")
        self.assertEqual(self.backend.history("peer-token", "shared-room"), [])


if __name__ == "__main__":
    unittest.main()
