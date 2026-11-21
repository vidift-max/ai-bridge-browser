import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.backup import create_restore_candidate


class RestoreCandidatePreservationTests(unittest.TestCase):
    def test_source_backup_remains_unchanged_and_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            backup = Path(directory) / "backup.sqlite"
            with sqlite3.connect(backup) as connection:
                connection.execute("CREATE TABLE items (value TEXT)")
                connection.execute("INSERT INTO items VALUES ('keep')")
            with sqlite3.connect(backup) as connection:
                before = connection.execute("SELECT value FROM items").fetchall()
            candidate = Path(directory) / "candidate.sqlite"
            self.assertTrue(create_restore_candidate(str(backup), str(candidate))[0])
            with sqlite3.connect(backup) as connection:
                after = connection.execute("SELECT value FROM items").fetchall()
            self.assertEqual(before, after)
            with sqlite3.connect(candidate) as connection:
                self.assertEqual(connection.execute("SELECT value FROM items").fetchall(),
                                 [("keep",)])

    def test_invalid_candidate_parent_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            backup = Path(directory) / "backup.sqlite"
            with sqlite3.connect(backup) as connection:
                connection.execute("CREATE TABLE items (id INTEGER)")
            parent = Path(directory) / "not-a-directory"
            parent.write_text("x")
            candidate = parent / "candidate.sqlite"
            self.assertEqual(create_restore_candidate(str(backup), str(candidate)),
                             (False, "RESTORE_CANDIDATE_FAILED"))
            self.assertFalse(candidate.exists())


if __name__ == "__main__":
    unittest.main()
