import tempfile
import unittest
from server.sqlite_store import SQLiteMessengerStore

class SQLiteStoreTest(unittest.TestCase):
    def test_schema_and_restart_recovery(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as f:
            store=SQLiteMessengerStore(f.name)
            store.save_conversation("room-1", ["AI-B","AI-A"])
            store.save_message(("m-1","room-1","AI-A",("AI-B",),"hello","req-1",1))
            store.save_idempotency("AI-A","req-1","m-1")
            store.save_ack("m-1","AI-B")
            store.close()

            reopened=SQLiteMessengerStore(f.name)
            self.assertEqual(reopened.load_conversations()["room-1"], {"AI-A","AI-B"})
            self.assertEqual(reopened.load_messages()[0]["message_id"], "m-1")
            self.assertEqual(reopened.find_idempotency("AI-A","req-1"), "m-1")
            self.assertEqual(reopened.load_acknowledgements()["m-1"], {"AI-B"})
            reopened.close()

    def test_memory_store_is_valid_for_unit_tests(self):
        store=SQLiteMessengerStore(":memory:")
        self.assertEqual(store.load_conversations(), {})
        store.close()

if __name__ == "__main__":
    unittest.main()
