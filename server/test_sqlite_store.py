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

    def test_voice_mute_survives_restart_and_expires(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as f:
            store = SQLiteMessengerStore(f.name)
            store.save_voice_mute("room-1", "AI-B", "AI-A", 200.0)
            store.close()

            reopened = SQLiteMessengerStore(f.name)
            rows = reopened.load_active_voice_mutes(150.0)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["muted_by_ai_id"], "AI-A")
            self.assertEqual(reopened.load_active_voice_mutes(200.0), [])
            reopened.close()

    def test_voice_mute_delete_is_scoped_to_room_and_ai(self):
        store = SQLiteMessengerStore(":memory:")
        store.save_voice_mute("room-1", "AI-B", "AI-A", 500.0)
        store.save_voice_mute("room-2", "AI-B", "AI-C", 500.0)
        self.assertTrue(store.delete_voice_mute("room-1", "AI-B"))
        rows = store.load_active_voice_mutes(100.0)
        self.assertEqual([(row["conversation_id"], row["ai_id"])
                          for row in rows], [("room-2", "AI-B")])
        store.close()

    def test_memory_store_is_valid_for_unit_tests(self):
        store=SQLiteMessengerStore(":memory:")
        self.assertEqual(store.load_conversations(), {})
        store.close()

if __name__ == "__main__":
    unittest.main()
