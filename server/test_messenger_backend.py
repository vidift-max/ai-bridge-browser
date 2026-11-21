import unittest
from server.messenger_backend import MessengerBackend

class MessengerBackendTest(unittest.TestCase):
    def setUp(self):
        self.backend = MessengerBackend({"opaque-a": "AI-A", "opaque-b": "AI-B"}, {"room-1": {"AI-A", "AI-B"}})

    def test_authenticated_submit_and_pending(self):
        msg = self.backend.submit("opaque-a", "m-1", "room-1", ["AI-B"], "hello", "req-1")
        self.assertEqual(msg.sender_ai_id, "AI-A")
        self.assertEqual(self.backend.pending("opaque-b", "room-1")[0].message_id, "m-1")

    def test_unauthenticated_submit_rejected(self):
        with self.assertRaises(PermissionError):
            self.backend.submit("bad", "m-1", "room-1", ["AI-B"], "hello", "req-1")

    def test_idempotency_conflict_rejected(self):
        self.backend.submit("opaque-a", "m-1", "room-1", ["AI-B"], "hello", "req-1")
        with self.assertRaises(ValueError):
            self.backend.submit("opaque-a", "m-2", "room-1", ["AI-B"], "different", "req-1")

    def test_acknowledgement_removes_pending(self):
        self.backend.submit("opaque-a", "m-1", "room-1", ["AI-B"], "hello", "req-1")
        self.backend.acknowledge("opaque-b", "m-1")
        self.assertEqual(self.backend.pending("opaque-b", "room-1"), [])

if __name__ == "__main__":
    unittest.main()
