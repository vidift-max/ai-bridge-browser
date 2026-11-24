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

    def _seed_ack_message(self, store, message_id="m-ack", room_id="room-ack",
                          recipients=("AI-B",)):
        store.save_conversation(room_id, ["AI-A", "AI-B"])
        store.save_message((message_id, room_id, "AI-A", recipients,
                            "ack test", f"req-{message_id}", 1))

    def test_ack_store_requires_existing_message_and_recipient(self):
        store = SQLiteMessengerStore(":memory:")
        self._seed_ack_message(store)
        with self.assertRaisesRegex(ValueError, "ack_message_not_found"):
            store.save_ack("missing", "AI-B")
        with self.assertRaisesRegex(ValueError, "ack_recipient_required"):
            store.save_ack("m-ack", "AI-A")
        self.assertEqual(store.load_acknowledgements(), {})
        store.close()

    def test_ack_store_requires_current_conversation_membership(self):
        store = SQLiteMessengerStore(":memory:")
        self._seed_ack_message(store)
        store.save_conversation("room-ack", ["AI-A"])
        with self.assertRaisesRegex(ValueError, "ack_room_membership_required"):
            store.save_ack("m-ack", "AI-B")
        self.assertEqual(store.load_acknowledgements(), {})
        store.close()

    def test_ack_store_is_idempotent_and_reports_insert(self):
        store = SQLiteMessengerStore(":memory:")
        self._seed_ack_message(store)
        self.assertTrue(store.save_ack("m-ack", "AI-B"))
        self.assertFalse(store.save_ack("m-ack", "AI-B"))
        self.assertEqual(store.load_acknowledgements(), {"m-ack": {"AI-B"}})
        store.close()

    def test_ack_store_rejects_blank_and_non_string_identifiers(self):
        store = SQLiteMessengerStore(":memory:")
        for message_id, ai_id in (("", "AI-B"), ("m", ""), (None, "AI-B"),
                                  ("m", None), ([], "AI-B")):
            with self.subTest(message_id=message_id, ai_id=ai_id):
                with self.assertRaisesRegex(ValueError, "invalid_ack_identity"):
                    store.save_ack(message_id, ai_id)
        store.close()

    def test_delete_message_cleans_acknowledgement_rows(self):
        store = SQLiteMessengerStore(":memory:")
        self._seed_ack_message(store)
        store.save_ack("m-ack", "AI-B")
        self.assertTrue(store.delete_message("m-ack"))
        self.assertEqual(store.load_acknowledgements(), {})
        self.assertFalse(store.delete_message("m-ack"))
        store.close()

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
