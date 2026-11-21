import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.recovery import verify_messenger_schema
from server.sqlite_store import SQLiteMessengerStore


class MessengerSchemaValidationTests(unittest.TestCase):
    def test_accepts_supported_messenger_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "messenger.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.close()
            self.assertEqual(verify_messenger_schema(str(path)),
                             (True, "RESTORE_SCHEMA_COMPATIBLE"))

    def test_rejects_database_without_messenger_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "other.sqlite"
            with sqlite3.connect(path) as connection:
                connection.execute("CREATE TABLE unrelated (id INTEGER)")
            self.assertEqual(verify_messenger_schema(str(path)),
                             (False, "RESTORE_SCHEMA_UNSUPPORTED"))

    def test_missing_candidate_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(verify_messenger_schema(
                str(Path(directory) / "missing.sqlite")),
                (False, "RESTORE_SCHEMA_UNAVAILABLE"))


    def test_rejects_non_unique_or_wrong_index_definition(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrong-index.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.close()
            with sqlite3.connect(path) as connection:
                connection.execute("DROP INDEX idx_messages_conversation_sequence")
                connection.execute(
                    "CREATE INDEX idx_messages_conversation_sequence "
                    "ON messages(conversation_id, sequence)"
                )
            self.assertEqual(verify_messenger_schema(str(path)),
                             (False, "RESTORE_SCHEMA_UNSUPPORTED"))

    def test_rejects_unique_index_with_wrong_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrong-index-columns.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.close()
            with sqlite3.connect(path) as connection:
                connection.execute("DROP INDEX idx_messages_conversation_sequence")
                connection.execute(
                    "CREATE UNIQUE INDEX idx_messages_conversation_sequence "
                    "ON messages(message_id, sequence)"
                )
            self.assertEqual(verify_messenger_schema(str(path)),
                             (False, "RESTORE_SCHEMA_UNSUPPORTED"))

if __name__ == "__main__":
    unittest.main()
