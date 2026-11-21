import unittest

from server.auth import Authenticator
from server.messenger_backend import MessengerBackend


class Mission15TransportAbuseTest(unittest.TestCase):
    def setUp(self):
        self.tokens = {"token-a": "AI-A", "token-b": "AI-B"}
        self.auth = Authenticator(self.tokens)
        self.backend = MessengerBackend(self.tokens, {"room": {"AI-A", "AI-B"}}, authenticator=self.auth)

    def tearDown(self):
        self.backend.close()

    def test_negative_cursor_is_rejected(self):
        self.backend.submit("token-a", "m1", "room", ["AI-B"], "x", "r1")
        with self.assertRaisesRegex(ValueError, "invalid_cursor"):
            self.backend.pending("token-b", "room", after_sequence=-1)

    def test_ack_by_non_recipient_is_rejected(self):
        self.backend.submit("token-a", "m1", "room", ["AI-B"], "x", "r1")
        with self.assertRaisesRegex(PermissionError, "authorization_denied"):
            self.backend.acknowledge("token-a", "m1")

    def test_duplicate_replay_does_not_advance_sequence(self):
        first = self.backend.submit("token-a", "m1", "room", ["AI-B"], "x", "r1")
        replay = self.backend.submit("token-a", "m1", "room", ["AI-B"], "x", "r1")
        second = self.backend.submit("token-a", "m2", "room", ["AI-B"], "y", "r2")
        self.assertEqual(first.sequence, replay.sequence)
        self.assertEqual(second.sequence, first.sequence + 1)


if __name__ == "__main__":
    unittest.main()
