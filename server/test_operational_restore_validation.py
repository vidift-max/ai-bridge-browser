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


    def test_inconsistent_data_records_safe_failure_without_path(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.sqlite"
            store = SQLiteMessengerStore(str(candidate))
            store.save_conversation("room-1", ["AI-A", "AI-B"])
            store.save_message(("m-1", "room-1", "AI-A", ("AI-B",), "secret-body", "req-1", 1))
            store.close()
            with sqlite3.connect(candidate) as connection:
                connection.execute("UPDATE messages SET conversation_id='orphan-room'")
            runtime = OperationalRuntime()
            self.assertEqual(runtime.validate_restore_candidate(
                str(candidate), correlation_id="data-check-1"),
                (False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"))
            event = runtime.snapshot()[0]
            self.assertEqual(event.event_type, "STORAGE_RESTORE_CANDIDATE_VALIDATION")
            self.assertEqual(event.diagnostic_code, "RESTORE_CANDIDATE_DATA_INCONSISTENT")
            self.assertNotIn(str(candidate), repr(event))
            self.assertNotIn("secret-body", repr(event))

if __name__ == "__main__":
    unittest.main()
