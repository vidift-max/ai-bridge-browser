import tempfile
import unittest
from server.sqlite_store import SQLiteMessengerStore


class SQLiteAudioAttachmentTest(unittest.TestCase):
    def test_audio_attachment_metadata_survives_restart(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as f:
            first = SQLiteMessengerStore(f.name)
            first.save_audio_attachment((
                "0123456789abcdef0123456789abcdef",
                "message-1",
                "room-1",
                "AI-A",
                "audio/ogg",
                42,
                "a" * 64,
            ))
            first.close()

            second = SQLiteMessengerStore(f.name)
            rows = second.load_audio_attachments_for_message("message-1")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["object_id"], "0123456789abcdef0123456789abcdef")
            self.assertEqual(rows[0]["conversation_id"], "room-1")
            self.assertEqual(rows[0]["sender_ai_id"], "AI-A")
            self.assertEqual(rows[0]["content_type"], "audio/ogg")
            self.assertEqual(rows[0]["size"], 42)
            self.assertEqual(rows[0]["sha256"], "a" * 64)
            second.close()

    def test_audio_attachment_delete_is_idempotent(self):
        store = SQLiteMessengerStore(":memory:")
        store.save_audio_attachment((
            "abcdefabcdefabcdefabcdefabcdefab",
            "message-2",
            "room-2",
            "AI-A",
            "audio/ogg",
            10,
            "b" * 64,
        ))
        self.assertTrue(store.delete_audio_attachment("abcdefabcdefabcdefabcdefabcdefab"))
        self.assertFalse(store.delete_audio_attachment("abcdefabcdefabcdefabcdefabcdefab"))
        self.assertEqual(store.load_audio_attachments_for_message("message-2"), [])
        store.close()

    def test_existing_v1_database_migrates_to_v2(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as f:
            import sqlite3
            connection = sqlite3.connect(f.name)
            connection.executescript("""
                CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE conversations (conversation_id TEXT PRIMARY KEY, member_ai_ids TEXT NOT NULL);
                CREATE TABLE messages (
                    message_id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL,
                    sender_ai_id TEXT NOT NULL, recipient_ai_ids TEXT NOT NULL,
                    body TEXT NOT NULL, client_request_id TEXT NOT NULL, sequence INTEGER NOT NULL
                );
                CREATE TABLE idempotency (
                    sender_ai_id TEXT NOT NULL, client_request_id TEXT NOT NULL,
                    message_id TEXT NOT NULL, PRIMARY KEY(sender_ai_id, client_request_id)
                );
                CREATE TABLE acknowledgements (
                    message_id TEXT NOT NULL, ai_id TEXT NOT NULL,
                    PRIMARY KEY(message_id, ai_id)
                );
                CREATE UNIQUE INDEX idx_messages_conversation_sequence
                    ON messages(conversation_id, sequence);
                INSERT INTO schema_meta(key,value) VALUES('version','1');
            """)
            connection.commit()
            connection.close()
            migrated = SQLiteMessengerStore(f.name)
            migrated.save_audio_attachment((
                "1234567890abcdef1234567890abcdef",
                "message-3",
                "room",
                "AI-A",
                "audio/ogg",
                4,
                "c" * 64,
            ))
            self.assertEqual(len(migrated.load_audio_attachments_for_message("message-3")), 1)
            migrated.close()


if __name__ == "__main__":
    unittest.main()
