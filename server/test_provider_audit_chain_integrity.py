import os
import tempfile
import threading
import unittest

from server.sqlite_store import SQLiteMessengerStore


class ProviderAuditChainIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.store = SQLiteMessengerStore(":memory:")

    def tearDown(self):
        self.store.close()

    def _claim(self, request_id, now=1.0):
        self.store.claim_provider_request(
            "AI-CHAIN", request_id, "digest", "room", "AI-CHAIN", now)

    def test_new_events_have_valid_sha256_chain_and_expose_hashes(self):
        self._claim("chain-a")
        self._claim("chain-b", 2.0)
        result = self.store.verify_provider_request_audit_chain()
        self.assertTrue(result["valid"])
        self.assertEqual(result["events_checked"], 2)
        rows = self.store.list_provider_request_audit_events("AI-CHAIN", "chain-a")
        self.assertEqual(len(rows[0]["previous_hash"]), 64)
        self.assertEqual(len(rows[0]["event_hash"]), 64)
        self.assertEqual(rows[0]["previous_hash"], "0" * 64)

    def test_event_field_tampering_is_detected(self):
        self._claim("tamper")
        self.store.connection.execute(
            "UPDATE provider_request_audit_events SET event_type='FAILED' WHERE audit_id=1")
        self.store.connection.commit()
        result = self.store.verify_provider_request_audit_chain()
        self.assertFalse(result["valid"])
        self.assertEqual(result["first_invalid_audit_id"], 1)

    def test_middle_event_deletion_is_detected_by_next_link(self):
        for index in range(3):
            self._claim("delete-" + str(index), float(index + 1))
        self.store.connection.execute(
            "DELETE FROM provider_request_audit_events WHERE audit_id=2")
        self.store.connection.commit()
        result = self.store.verify_provider_request_audit_chain()
        self.assertFalse(result["valid"])
        self.assertEqual(result["first_invalid_audit_id"], 3)

    def test_event_reordering_is_detected(self):
        self._claim("order-a")
        self._claim("order-b", 2.0)
        self.store.connection.execute(
            "UPDATE provider_request_audit_events SET audit_id=-1 WHERE audit_id=1")
        self.store.connection.execute(
            "UPDATE provider_request_audit_events SET audit_id=1 WHERE audit_id=2")
        self.store.connection.execute(
            "UPDATE provider_request_audit_events SET audit_id=2 WHERE audit_id=-1")
        self.store.connection.commit()
        result = self.store.verify_provider_request_audit_chain()
        self.assertFalse(result["valid"])

    def test_concurrent_independent_connections_preserve_one_valid_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "audit.sqlite")
            initialized = SQLiteMessengerStore(path)
            initialized.close()
            barrier = threading.Barrier(6)
            failures = []

            def worker(index):
                connection = SQLiteMessengerStore(path)
                try:
                    barrier.wait(timeout=5)
                    connection.claim_provider_request(
                        "AI-CONCURRENT", "request-" + str(index), "digest",
                        "room", "AI-CONCURRENT", float(index + 1))
                except Exception as exc:
                    failures.append(repr(exc))
                finally:
                    connection.close()

            threads = [threading.Thread(target=worker, args=(i,)) for i in range(6)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
            self.assertFalse(any(thread.is_alive() for thread in threads))
            self.assertEqual(failures, [])
            verifier = SQLiteMessengerStore(path)
            try:
                result = verifier.verify_provider_request_audit_chain()
                self.assertTrue(result["valid"])
                self.assertEqual(result["events_checked"], 6)
            finally:
                verifier.close()

    def test_schema_v14_existing_events_are_backfilled_during_upgrade(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "legacy.sqlite")
            import sqlite3
            connection = sqlite3.connect(path)
            connection.execute(
                "CREATE TABLE schema_meta (key TEXT PRIMARY KEY,value TEXT NOT NULL)")
            connection.execute(
                "INSERT INTO schema_meta(key,value) VALUES('version','14')")
            connection.execute("""
                CREATE TABLE provider_request_audit_events (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    principal_ai_id TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    attempt_generation INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    event_at REAL NOT NULL,
                    from_status TEXT,
                    to_status TEXT NOT NULL,
                    error_code TEXT
                )
            """)
            connection.execute("""
                INSERT INTO provider_request_audit_events(
                    principal_ai_id,request_id,attempt_generation,event_type,event_at,
                    from_status,to_status,error_code)
                VALUES('AI-LEGACY','old-1',1,'CLAIMED',1.0,NULL,'PROCESSING',NULL)
            """)
            connection.execute("""
                INSERT INTO provider_request_audit_events(
                    principal_ai_id,request_id,attempt_generation,event_type,event_at,
                    from_status,to_status,error_code)
                VALUES('AI-LEGACY','old-2',1,'CLAIMED',2.0,NULL,'PROCESSING',NULL)
            """)
            connection.commit()
            connection.close()

            upgraded = SQLiteMessengerStore(path)
            try:
                self.assertEqual(
                    upgraded.connection.execute(
                        "SELECT value FROM schema_meta WHERE key='version'"
                    ).fetchone()["value"], "15")
                result = upgraded.verify_provider_request_audit_chain()
                self.assertTrue(result["valid"])
                self.assertEqual(result["events_checked"], 2)
            finally:
                upgraded.close()


if __name__ == "__main__":
    unittest.main()
