import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.backup import create_sqlite_backup


class SQLiteBackupTests(unittest.TestCase):
    def make_source(self, directory):
        source = Path(directory) / "source.sqlite"
        with sqlite3.connect(source) as connection:
            connection.execute("CREATE TABLE messages (id TEXT PRIMARY KEY, body TEXT)")
            connection.execute("INSERT INTO messages VALUES ('m1', 'private-content')")
        return source

    def test_backup_is_valid_and_contains_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.make_source(directory)
            destination = Path(directory) / "snapshots" / "backup.sqlite"
            self.assertEqual(create_sqlite_backup(str(source), str(destination)),
                             (True, "BACKUP_CREATED"))
            with sqlite3.connect(destination) as connection:
                self.assertEqual(connection.execute("SELECT body FROM messages").fetchone()[0],
                                 "private-content")

    def test_existing_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.make_source(directory)
            destination = Path(directory) / "backup.sqlite"
            destination.write_text("keep-me")
            self.assertEqual(create_sqlite_backup(str(source), str(destination)),
                             (False, "BACKUP_DESTINATION_EXISTS"))
            self.assertEqual(destination.read_text(), "keep-me")

    def test_missing_source_fails_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(create_sqlite_backup(str(Path(directory) / "missing"),
                                                  str(Path(directory) / "backup")),
                             (False, "STORAGE_UNAVAILABLE"))

    def test_same_source_and_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.make_source(directory)
            self.assertEqual(create_sqlite_backup(str(source), str(source)),
                             (False, "BACKUP_DESTINATION_CONFLICT"))


if __name__ == "__main__":
    unittest.main()
