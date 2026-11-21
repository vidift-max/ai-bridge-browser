import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.operational_runtime import OperationalRuntime


class OperationalBackupTests(unittest.TestCase):
    def test_backup_records_success_event_without_paths_or_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.sqlite"
            with sqlite3.connect(source) as connection:
                connection.execute("CREATE TABLE t (secret TEXT)")
                connection.execute("INSERT INTO t VALUES ('private')")
            destination = Path(directory) / "backup.sqlite"
            runtime = OperationalRuntime()
            self.assertEqual(runtime.create_backup(str(source), str(destination),
                                                   correlation_id="backup-corr"),
                             (True, "BACKUP_CREATED"))
            event = runtime.snapshot()[0]
            self.assertEqual(event.event_type, "STORAGE_BACKUP")
            self.assertEqual(event.correlation_id, "backup-corr")
            self.assertNotIn("private", repr(event))
            self.assertNotIn(str(source), repr(event))


if __name__ == "__main__":
    unittest.main()
