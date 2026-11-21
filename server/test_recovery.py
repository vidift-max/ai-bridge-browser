import sqlite3
import tempfile
import unittest
from pathlib import Path

from recovery import verify_sqlite_recovery


class RecoveryTests(unittest.TestCase):
    def test_valid_sqlite_database_recovers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "messenger.sqlite"
            with sqlite3.connect(path) as connection:
                connection.execute("CREATE TABLE messages (id TEXT PRIMARY KEY)")
            self.assertEqual(verify_sqlite_recovery(str(path)), (True, "STORAGE_RECOVERY_OK"))

    def test_missing_database_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.sqlite"
            self.assertEqual(verify_sqlite_recovery(str(path)), (False, "STORAGE_UNAVAILABLE"))


if __name__ == "__main__":
    unittest.main()
