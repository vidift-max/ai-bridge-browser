import os
import sqlite3
import tempfile
import threading
import unittest

from server.provider_audit_remote_anchor import (
    _GENESIS_DIGEST,
    _record_from_checkpoint,
    _record_digest,
)
from server.provider_audit_durable_anchor import SQLiteDurableAuditAnchor
from server.provider_audit_checkpoint import create_provider_audit_checkpoint
from server.provider_audit_remote_anchor import publish_provider_audit_remote_anchor, verify_provider_audit_remote_anchor
from server.sqlite_store import SQLiteMessengerStore


class DurableAuditAnchorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.directory.name, "remote-anchor.sqlite")
        self.anchor = SQLiteDurableAuditAnchor(self.path)

    def tearDown(self):
        self.directory.cleanup()

    def _record(self, sequence, audit_id, previous_digest):
        payload = {
            "audit_id": audit_id,
            "event_hash": ("%064x" % audit_id),
            "created_at": float(sequence * 100),
            "signature": ("%064x" % (audit_id + 1000)),
        }
        previous = None
        if sequence > 1:
            previous = {
                "sequence": sequence - 1,
                "record_digest": previous_digest,
            }
        return _record_from_checkpoint(payload, previous)

    def test_first_record_persists_and_survives_adapter_restart(self):
        record = self._record(1, 10, _GENESIS_DIGEST)
        self.anchor.append_checkpoint(0, record)
        restarted = SQLiteDurableAuditAnchor(self.path)
        self.assertEqual(restarted.read_latest(), record)
        self.assertEqual(restarted.verify_history()["records_checked"], 1)

    def test_second_record_advances_digest_chain_and_sequence(self):
        first = self._record(1, 10, _GENESIS_DIGEST)
        self.anchor.append_checkpoint(0, first)
        second = self._record(2, 20, first["record_digest"])
        self.anchor.append_checkpoint(1, second)
        result = self.anchor.verify_history()
        self.assertTrue(result["valid"])
        self.assertEqual(result["last_sequence"], 2)
        self.assertEqual(self.anchor.read_latest(), second)

    def test_stale_expected_sequence_is_rejected(self):
        first = self._record(1, 10, _GENESIS_DIGEST)
        self.anchor.append_checkpoint(0, first)
        second = self._record(2, 20, first["record_digest"])
        with self.assertRaisesRegex(ValueError, "remote_anchor_sequence_conflict"):
            self.anchor.append_checkpoint(0, second)
        self.assertEqual(self.anchor.read_latest(), first)

    def test_sequence_gap_is_rejected(self):
        record = self._record(2, 20, _GENESIS_DIGEST)
        with self.assertRaisesRegex(ValueError, "remote_anchor_sequence_invalid"):
            self.anchor.append_checkpoint(0, record)
        self.assertIsNone(self.anchor.read_latest())

    def test_broken_previous_digest_is_rejected(self):
        record = self._record(1, 10, _GENESIS_DIGEST)
        record["previous_digest"] = "f" * 64
        record["record_digest"] = _record_digest(record)
        with self.assertRaisesRegex(ValueError, "remote_anchor_chain_conflict"):
            self.anchor.append_checkpoint(0, record)

    def test_non_monotonic_audit_id_is_rejected(self):
        first = self._record(1, 20, _GENESIS_DIGEST)
        self.anchor.append_checkpoint(0, first)
        second = self._record(2, 19, first["record_digest"])
        with self.assertRaisesRegex(ValueError, "remote_anchor_audit_id_not_monotonic"):
            self.anchor.append_checkpoint(1, second)

    def test_duplicate_append_is_rejected_without_changing_history(self):
        first = self._record(1, 10, _GENESIS_DIGEST)
        self.anchor.append_checkpoint(0, first)
        with self.assertRaisesRegex(ValueError, "remote_anchor_sequence_conflict"):
            self.anchor.append_checkpoint(0, first)
        self.assertEqual(self.anchor.verify_history()["records_checked"], 1)

    def test_update_and_delete_are_rejected_by_append_only_triggers(self):
        first = self._record(1, 10, _GENESIS_DIGEST)
        self.anchor.append_checkpoint(0, first)
        connection = sqlite3.connect(self.path)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE provider_audit_anchor_records SET checkpoint_audit_id=99")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM provider_audit_anchor_records")
        finally:
            connection.close()

    def test_record_tampering_is_detected_by_history_verification(self):
        first = self._record(1, 10, _GENESIS_DIGEST)
        self.anchor.append_checkpoint(0, first)
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("DROP TRIGGER provider_audit_anchor_no_update")
            connection.execute(
                "UPDATE provider_audit_anchor_records SET record_digest=? WHERE sequence=1",
                ("f" * 64,),
            )
            connection.commit()
        finally:
            connection.close()
        result = self.anchor.verify_history()
        self.assertFalse(result["valid"])
        self.assertEqual(result["first_invalid_sequence"], 1)

    def test_concurrent_initial_append_has_exactly_one_winner(self):
        barrier = threading.Barrier(2)
        results = []
        errors = []
        record = self._record(1, 10, _GENESIS_DIGEST)

        def worker():
            backend = SQLiteDurableAuditAnchor(self.path)
            barrier.wait(timeout=5)
            try:
                results.append(backend.append_checkpoint(0, record))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 1)
        self.assertEqual(self.anchor.verify_history()["records_checked"], 1)

    def test_checkpoint_publication_uses_durable_backend_across_restart(self):
        main_db = os.path.join(self.directory.name, "main.sqlite")
        checkpoint = os.path.join(self.directory.name, "checkpoint.json")
        key = b"m163-test-only-signing-key-material-32-bytes"
        store = SQLiteMessengerStore(main_db)
        try:
            store.claim_provider_request("AI-DURABLE", "req-1", "digest", "room", "AI-DURABLE", 1.0)
            create_provider_audit_checkpoint(store, checkpoint, key, created_at=10.0)
            published = publish_provider_audit_remote_anchor(store, checkpoint, key, self.anchor)
            restarted = SQLiteDurableAuditAnchor(self.path)
            self.assertEqual(restarted.read_latest(), published)
            result = verify_provider_audit_remote_anchor(store, checkpoint, key, restarted)
            self.assertTrue(result["valid"])
        finally:
            store.close()
    def test_memory_database_is_rejected_for_durable_backend(self):
        with self.assertRaisesRegex(ValueError, "durable_anchor_path_required"):
            SQLiteDurableAuditAnchor(":memory:")


if __name__ == "__main__":
    unittest.main()
