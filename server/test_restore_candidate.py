import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.backup import create_restore_candidate
from server.recovery import verify_sqlite_recovery


class RestoreCandidateTests(unittest.TestCase):
    def make_backup(self, directory):
        backup = Path(directory) / "backup.sqlite"
        with sqlite3.connect(backup) as connection:
            connection.execute("CREATE TABLE messages (id TEXT PRIMARY KEY, body TEXT)")
            connection.execute("INSERT INTO messages VALUES ('m1', 'snapshot')")
        return backup

    def test_creates_separate_integrity_checked_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            backup = self.make_backup(directory)
            candidate = Path(directory) / "staging" / "candidate.sqlite"
            self.assertEqual(create_restore_candidate(str(backup), str(candidate)),
                             (True, "RESTORE_CANDIDATE_CREATED"))
            self.assertTrue(verify_sqlite_recovery(str(candidate))[0])
            with sqlite3.connect(candidate) as connection:
                self.assertEqual(connection.execute(
                    "SELECT body FROM messages WHERE id='m1'").fetchone()[0], "snapshot")
            self.assertNotEqual(backup.resolve(), candidate.resolve())

    def test_missing_backup_fails_without_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.sqlite"
            self.assertEqual(create_restore_candidate(
                str(Path(directory) / "missing.sqlite"), str(candidate)),
                (False, "RESTORE_BACKUP_UNAVAILABLE"))
            self.assertFalse(candidate.exists())


if __name__ == "__main__":
    unittest.main()
