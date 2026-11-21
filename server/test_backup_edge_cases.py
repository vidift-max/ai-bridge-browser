import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.backup import create_sqlite_backup


class BackupEdgeCaseTests(unittest.TestCase):
    def test_backup_does_not_modify_source_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.sqlite"
            with sqlite3.connect(source) as connection:
                connection.execute("CREATE TABLE t (value TEXT)")
                connection.execute("INSERT INTO t VALUES ('unchanged')")
            destination = Path(directory) / "backup.sqlite"
            self.assertTrue(create_sqlite_backup(str(source), str(destination))[0])
            with sqlite3.connect(source) as connection:
                self.assertEqual(connection.execute("SELECT value FROM t").fetchone()[0],
                                 "unchanged")

    def test_invalid_destination_parent_returns_safe_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.sqlite"
            with sqlite3.connect(source) as connection:
                connection.execute("CREATE TABLE t (id INTEGER)")
            # A regular file cannot be used as a directory parent.
            parent = Path(directory) / "not-a-directory"
            parent.write_text("x")
            destination = parent / "backup.sqlite"
            self.assertEqual(create_sqlite_backup(str(source), str(destination)),
                             (False, "BACKUP_FAILED"))


if __name__ == "__main__":
    unittest.main()
