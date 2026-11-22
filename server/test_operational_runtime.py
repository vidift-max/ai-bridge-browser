import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.operational_runtime import OperationalRuntime\nfrom server.sqlite_store import SQLiteMessengerStore


class OperationalRuntimeTests(unittest.TestCase):
    def test_storage_check_records_success_without_database_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "db.sqlite"
            self.make_valid_messenger_db(path)
            runtime = OperationalRuntime()
            self.assertEqual(runtime.check_storage(str(path), correlation_id="corr-1"),
                             (True, "STORAGE_RECOVERY_OK"))
            event = runtime.snapshot()[0]
            self.assertEqual(event.correlation_id, "corr-1")
            self.assertNotIn("hello", repr(event))


    def make_valid_messenger_db(self, path):
        store = SQLiteMessengerStore(str(path))
        store.save_conversation("room", ["AI-A", "AI-B"])
        store.save_message_with_idempotency(
            ("m-1", "room", "AI-A", ("AI-B",), "hello", "req-1", 1))
        store.close()

    def test_storage_check_accepts_valid_messenger_schema_and_references(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "messenger.sqlite"
            self.make_valid_messenger_db(path)
            self.assertEqual(OperationalRuntime().check_storage(str(path)),
                             (True, "STORAGE_RECOVERY_OK"))

    def test_storage_check_rejects_sqlite_file_with_unrelated_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrong-schema.sqlite"
            with sqlite3.connect(path) as connection:
                connection.execute("CREATE TABLE unrelated (value TEXT)")
            self.assertEqual(OperationalRuntime().check_storage(str(path)),
                             (False, "RESTORE_SCHEMA_UNSUPPORTED"))

    def test_storage_check_rejects_missing_idempotency_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing-idempotency.sqlite"
            self.make_valid_messenger_db(path)
            with sqlite3.connect(path) as connection:
                connection.execute("DELETE FROM idempotency")
            self.assertEqual(OperationalRuntime().check_storage(str(path)),
                             (False, "RESTORE_DATA_IDEMPOTENCY_INVALID"))


    def test_storage_check_rejects_acknowledgement_by_non_recipient_member(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sender-ack.sqlite"
            self.make_valid_messenger_db(path)
            with sqlite3.connect(path) as connection:
                connection.execute(
                    "INSERT INTO acknowledgements(message_id, ai_id) VALUES('m-1', 'AI-A')")
            self.assertEqual(OperationalRuntime().check_storage(str(path)),
                             (False, "RESTORE_DATA_ACKNOWLEDGEMENT_INVALID"))

    def test_storage_check_rejects_acknowledgement_for_unknown_message(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "orphan-ack.sqlite"
            self.make_valid_messenger_db(path)
            with sqlite3.connect(path) as connection:
                connection.execute(
                    "INSERT INTO acknowledgements(message_id, ai_id) VALUES('missing', 'AI-B')")
            self.assertEqual(OperationalRuntime().check_storage(str(path)),
                             (False, "RESTORE_DATA_ACKNOWLEDGEMENT_INVALID"))

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
