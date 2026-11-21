import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.recovery import verify_messenger_schema
from server.sqlite_store import SQLiteMessengerStore


class MessengerSchemaVersionTests(unittest.TestCase):
    def test_rejects_future_schema_version(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "future.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.close()
            with sqlite3.connect(path) as connection:
                connection.execute(
                    "UPDATE schema_meta SET value='999' WHERE key='version'")
            self.assertEqual(verify_messenger_schema(str(path)),
                             (False, "RESTORE_SCHEMA_UNSUPPORTED"))

    def test_rejects_missing_required_index(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing-index.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.close()
            with sqlite3.connect(path) as connection:
                connection.execute("DROP INDEX idx_messages_conversation_sequence")
            self.assertEqual(verify_messenger_schema(str(path)),
                             (False, "RESTORE_SCHEMA_UNSUPPORTED"))


if __name__ == "__main__":
    unittest.main()
