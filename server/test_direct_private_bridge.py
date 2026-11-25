import unittest
from server.messenger_backend import MessengerBackend


class DirectPrivateBridgeTest(unittest.TestCase):
    def setUp(self):
        self.backend = MessengerBackend(
            {"token-one": "AI-ONE", "token-two": "AI-TWO",
             "token-outsider": "AI-OUTSIDER"},
            {},
        )

    def tearDown(self):
        self.backend.close()

    def test_private_link_creates_exactly_two_authorized_identities(self):
        room = self.backend.create_conversation(
            "token-one", "private-link-1", ["AI-ONE", "AI-TWO"], "PRIVATE")
        self.assertEqual(room["kind"], "PRIVATE")
        self.assertEqual(room["memberCount"], 2)
        self.assertEqual(room["memberAiIds"], ["AI-ONE", "AI-TWO"])

    def test_private_text_bridge_delivers_only_to_the_linked_peer(self):
        self.backend.create_conversation(
            "token-one", "private-link-2", ["AI-ONE", "AI-TWO"], "PRIVATE")
        message = self.backend.submit(
            "token-one", "private-message-1", "private-link-2",
            ["AI-TWO"], "Olá, IA 2.", "private-request-1")
        pending = self.backend.pending("token-two", "private-link-2")
        self.assertEqual([item.message_id for item in pending], [message.message_id])
        self.assertEqual(pending[0].body, "Olá, IA 2.")
        self.assertEqual(self.backend.pending("token-one", "private-link-2"), [])

    def test_private_bridge_rejects_outsider_and_recipient_outside_room(self):
        self.backend.create_conversation(
            "token-one", "private-link-3", ["AI-ONE", "AI-TWO"], "PRIVATE")
        with self.assertRaises(PermissionError):
            self.backend.pending("token-outsider", "private-link-3")
        with self.assertRaisesRegex(PermissionError, "recipient_authorization_denied"):
            self.backend.submit(
                "token-one", "private-message-leak", "private-link-3",
                ["AI-OUTSIDER"], "não deve vazar", "private-request-leak")

    def test_private_bridge_retry_is_idempotent_and_acknowledgement_stops_redelivery(self):
        self.backend.create_conversation(
            "token-one", "private-link-4", ["AI-ONE", "AI-TWO"], "PRIVATE")
        first = self.backend.submit(
            "token-one", "private-message-2", "private-link-4",
            ["AI-TWO"], "mensagem repetível", "private-request-2")
        retry = self.backend.submit(
            "token-one", "private-message-2", "private-link-4",
            ["AI-TWO"], "mensagem repetível", "private-request-2")
        self.assertIs(first, retry)
        self.assertEqual(len(self.backend.pending("token-two", "private-link-4")), 1)
        self.backend.acknowledge("token-two", first.message_id)
        self.assertEqual(self.backend.pending("token-two", "private-link-4"), [])


if __name__ == "__main__":
    unittest.main()
