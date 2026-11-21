import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.operational_runtime import OperationalRuntime
from server.sqlite_store import SQLiteMessengerStore


class OperationalRestoreValidationTests(unittest.TestCase):
    def test_validation_event_is_redacted(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.sqlite"
            store = SQLiteMessengerStore(str(candidate))
            store.close()
            runtime = OperationalRuntime()
            self.assertEqual(runtime.validate_restore_candidate(
                str(candidate), correlation_id="schema-check-1"),
                (True, "RESTORE_CANDIDATE_VALIDATED"))
            event = runtime.snapshot()[0]
            self.assertEqual(event.event_type, "STORAGE_RESTORE_CANDIDATE_VALIDATION")
            self.assertEqual(event.correlation_id, "schema-check-1")
            self.assertNotIn(str(candidate), repr(event))

    def test_unsupported_schema_records_safe_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "other.sqlite"
            with sqlite3.connect(candidate) as connection:
                connection.execute("CREATE TABLE unrelated (id INTEGER)")
            runtime = OperationalRuntime()
            self.assertEqual(runtime.validate_restore_candidate(str(candidate)),
                             (False, "RESTORE_CANDIDATE_SCHEMA_UNSUPPORTED"))
            event = runtime.snapshot()[0]
            self.assertEqual(event.outcome, "error")
            self.assertEqual(event.diagnostic_code,
                             "RESTORE_CANDIDATE_SCHEMA_UNSUPPORTED")


if __name__ == "__main__":
    unittest.main()
