import tempfile
import unittest
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore

class MessengerBackendTest(unittest.TestCase):
    def setUp(self):
        self.backend = MessengerBackend({"opaque-a": "AI-A", "opaque-b": "AI-B"}, {"room-1": {"AI-A", "AI-B"}})

    def tearDown(self):
        self.backend.close()

    def test_authenticated_submit_and_pending(self):
        msg=self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"hello","req-1")
        self.assertEqual(msg.sender_ai_id,"AI-A")
        self.assertEqual(self.backend.pending("opaque-b","room-1")[0].message_id,"m-1")

    def test_restart_recovers_message_and_ack(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as f:
            first=MessengerBackend({"opaque-a":"AI-A","opaque-b":"AI-B"},{"room-1":{"AI-A","AI-B"}},SQLiteMessengerStore(f.name))
            first.submit("opaque-a","m-1","room-1",["AI-B"],"hello","req-1")
            first.acknowledge("opaque-b","m-1")
            first.close()
            second=MessengerBackend({"opaque-a":"AI-A","opaque-b":"AI-B"},{"room-1":{"AI-A","AI-B"}},SQLiteMessengerStore(f.name))
            self.assertEqual(second.pending("opaque-b","room-1"),[])
            self.assertEqual(second.submit("opaque-a","m-1","room-1",["AI-B"],"hello","req-1").message_id,"m-1")
            second.close()

    def test_unauthenticated_submit_rejected(self):
        with self.assertRaises(PermissionError):
            self.backend.submit("bad","m-1","room-1",["AI-B"],"hello","req-1")

    def test_idempotency_conflict_rejected(self):
        self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"hello","req-1")
        with self.assertRaises(ValueError):
            self.backend.submit("opaque-a","m-2","room-1",["AI-B"],"different","req-1")

    def test_duplicate_message_id_rejected(self):
        self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"hello","req-1")
        with self.assertRaises(ValueError):
            self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"other","req-2")

    def test_recipients_are_deduplicated(self):
        msg=self.backend.submit("opaque-a","m-1","room-1",["AI-B","AI-B"],"hello","req-1")
        self.assertEqual(msg.recipient_ai_ids,("AI-B",))

    def test_body_limit_rejected(self):
        with self.assertRaises(ValueError):
            self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"x"*5001,"req-1")

    def test_pending_cursor(self):
        self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"one","req-1")
        self.backend.submit("opaque-a","m-2","room-1",["AI-B"],"two","req-2")
        self.assertEqual([m.message_id for m in self.backend.pending("opaque-b","room-1",after_sequence=1)],["m-2"])

if __name__ == "__main__":
    unittest.main()
