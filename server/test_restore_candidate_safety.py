import tempfile
import unittest
from pathlib import Path

from server.backup import create_restore_candidate


class RestoreCandidateSafetyTests(unittest.TestCase):
    def test_corrupt_backup_is_rejected_before_candidate_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            backup = Path(directory) / "corrupt.sqlite"
            backup.write_bytes(b"not-a-sqlite-database")
            candidate = Path(directory) / "candidate.sqlite"
            self.assertEqual(create_restore_candidate(str(backup), str(candidate)),
                             (False, "RESTORE_BACKUP_INVALID"))
            self.assertFalse(candidate.exists())

    def test_existing_candidate_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            backup = Path(directory) / "backup.sqlite"
            backup.write_bytes(b"invalid-but-present")
            candidate = Path(directory) / "candidate.sqlite"
            candidate.write_text("preserve-this")
            self.assertEqual(create_restore_candidate(str(backup), str(candidate)),
                             (False, "RESTORE_CANDIDATE_EXISTS"))
            self.assertEqual(candidate.read_text(), "preserve-this")

    def test_backup_and_candidate_same_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            backup = Path(directory) / "backup.sqlite"
            backup.write_bytes(b"placeholder")
            self.assertEqual(create_restore_candidate(str(backup), str(backup)),
                             (False, "RESTORE_CANDIDATE_CONFLICT"))
            self.assertEqual(backup.read_bytes(), b"placeholder")


if __name__ == "__main__":
    unittest.main()
