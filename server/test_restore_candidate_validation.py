import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.backup import validate_restore_candidate
from server.sqlite_store import SQLiteMessengerStore


class RestoreCandidateValidationTests(unittest.TestCase):
    def test_valid_candidate_passes_integrity_and_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.close()
            self.assertEqual(validate_restore_candidate(str(path)),
                             (True, "RESTORE_CANDIDATE_VALIDATED"))

    def test_integrity_valid_but_wrong_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrong-schema.sqlite"
            with sqlite3.connect(path) as connection:
                connection.execute("CREATE TABLE unrelated (id INTEGER)")
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_SCHEMA_UNSUPPORTED"))

    def test_corrupt_candidate_fails_integrity_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corrupt.sqlite"
            path.write_bytes(b"not sqlite")
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_INTEGRITY_FAILED"))


if __name__ == "__main__":
    unittest.main()
