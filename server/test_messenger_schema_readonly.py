import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.recovery import verify_messenger_schema
from server.sqlite_store import SQLiteMessengerStore


class MessengerSchemaReadOnlyTests(unittest.TestCase):
    def test_validation_does_not_change_schema_or_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "readonly.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.save_conversation("room-a", ["AI-A", "AI-B"])
            store.save_message(("msg-a", "room-a", "AI-A", ("AI-B",),
                                "payload", "request-a", 1))
            store.close()
            with sqlite3.connect(path) as connection:
                before_tables = connection.execute(
                    "SELECT type,name,sql FROM sqlite_master ORDER BY type,name").fetchall()
                before_rows = connection.execute(
                    "SELECT conversation_id,member_ai_ids FROM conversations").fetchall()
            self.assertEqual(verify_messenger_schema(str(path)),
                             (True, "RESTORE_SCHEMA_COMPATIBLE"))
            with sqlite3.connect(path) as connection:
                after_tables = connection.execute(
                    "SELECT type,name,sql FROM sqlite_master ORDER BY type,name").fetchall()
                after_rows = connection.execute(
                    "SELECT conversation_id,member_ai_ids FROM conversations").fetchall()
            self.assertEqual(before_tables, after_tables)
            self.assertEqual(before_rows, after_rows)


if __name__ == "__main__":
    unittest.main()
