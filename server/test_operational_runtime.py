import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.operational_runtime import OperationalRuntime


class OperationalRuntimeTests(unittest.TestCase):
    def test_storage_check_records_success_without_database_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "db.sqlite"
            with sqlite3.connect(path) as connection:
                connection.execute("CREATE TABLE private_data (value TEXT)")
                connection.execute("INSERT INTO private_data VALUES ('do-not-log')")
            runtime = OperationalRuntime()
            self.assertEqual(runtime.check_storage(str(path), correlation_id="corr-1"),
                             (True, "STORAGE_RECOVERY_OK"))
            event = runtime.snapshot()[0]
            self.assertEqual(event.correlation_id, "corr-1")
            self.assertNotIn("do-not-log", repr(event))

    def test_missing_storage_records_safe_failure_code(self):
        runtime = OperationalRuntime()
        ok, code = runtime.check_storage("/path/that/does/not/exist/db.sqlite")
        self.assertFalse(ok)
        self.assertEqual(code, "STORAGE_UNAVAILABLE")
        self.assertEqual(runtime.snapshot()[0].diagnostic_code, code)

    def test_secret_metadata_is_filtered(self):
        runtime = OperationalRuntime()
        event = runtime.record("AUTH_FAILURE", metadata={
            "authorization_header": "Bearer secret",
            "reason": "invalid",
        })
        self.assertNotIn("authorization_header", event.metadata)
        self.assertEqual(event.metadata["reason"], "invalid")


if __name__ == "__main__":
    unittest.main()
