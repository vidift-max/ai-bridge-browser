import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.operational_runtime import OperationalRuntime


class OperationalRestoreCandidateTests(unittest.TestCase):
    def test_success_event_contains_no_paths_or_database_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            backup = Path(directory) / "backup.sqlite"
            with sqlite3.connect(backup) as connection:
                connection.execute("CREATE TABLE secrets (value TEXT)")
                connection.execute("INSERT INTO secrets VALUES ('do-not-log-this')")
            candidate = Path(directory) / "candidate.sqlite"
            runtime = OperationalRuntime()
            self.assertEqual(runtime.create_restore_candidate(
                str(backup), str(candidate), correlation_id="restore-corr"),
                (True, "RESTORE_CANDIDATE_CREATED"))
            event = runtime.snapshot()[0]
            self.assertEqual(event.event_type, "STORAGE_RESTORE_CANDIDATE")
            self.assertEqual(event.correlation_id, "restore-corr")
            rendered = repr(event)
            self.assertNotIn(str(backup), rendered)
            self.assertNotIn(str(candidate), rendered)
            self.assertNotIn("do-not-log-this", rendered)

    def test_failure_event_uses_safe_diagnostic_code(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = OperationalRuntime()
            self.assertEqual(runtime.create_restore_candidate(
                str(Path(directory) / "missing.sqlite"),
                str(Path(directory) / "candidate.sqlite")),
                (False, "RESTORE_BACKUP_UNAVAILABLE"))
            event = runtime.snapshot()[0]
            self.assertEqual(event.event_type, "STORAGE_RESTORE_CANDIDATE")
            self.assertEqual(event.outcome, "error")
            self.assertEqual(event.diagnostic_code, "RESTORE_BACKUP_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
