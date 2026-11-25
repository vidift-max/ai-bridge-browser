import os
import tempfile
import threading
import unittest

from server.provider_audit_checkpoint import create_provider_audit_checkpoint
from server.provider_audit_remote_anchor import (
    publish_provider_audit_remote_anchor,
    verify_provider_audit_remote_anchor,
    _GENESIS_DIGEST,
    _validate_record,
)
from server.sqlite_store import SQLiteMessengerStore


class FakeRemoteAnchor:
    """Test-only atomic append-only remote anchor; not a production service."""
    def __init__(self):
        self.records = []
        self.lock = threading.Lock()
        self.available = True

    def read_latest(self):
        if not self.available:
            raise ConnectionError("remote_anchor_unavailable")
        with self.lock:
            return dict(self.records[-1]) if self.records else None

    def append_checkpoint(self, expected_sequence, record):
        if not self.available:
            raise ConnectionError("remote_anchor_unavailable")
        with self.lock:
            actual = self.records[-1]["sequence"] if self.records else 0
            if expected_sequence != actual:
                raise ValueError("remote_anchor_sequence_conflict")
            if record["sequence"] != actual + 1:
                raise ValueError("remote_anchor_sequence_invalid")
            if record["previous_digest"] != (
                    self.records[-1]["record_digest"] if self.records else _GENESIS_DIGEST):
                raise ValueError("remote_anchor_chain_conflict")
            if self.records and record["checkpoint_audit_id"] <= self.records[-1]["checkpoint_audit_id"]:
                raise ValueError("remote_anchor_audit_id_not_monotonic")
            _validate_record(record)
            self.records.append(dict(record))
            return dict(record)


class ProviderAuditRemoteAnchorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.directory.name, "messenger.sqlite")
        self.checkpoint_path = os.path.join(self.directory.name, "checkpoint.json")
        self.key = b"test-only-remote-anchor-key-material-32-bytes"
        self.store = SQLiteMessengerStore(self.db_path)
        self.remote = FakeRemoteAnchor()

    def tearDown(self):
        self.store.close()
        self.directory.cleanup()

    def _claim(self, request_id, now):
        self.store.claim_provider_request(
            "AI-REMOTE", request_id, "digest", "room", "AI-REMOTE", now)

    def _checkpoint(self, now):
        return create_provider_audit_checkpoint(
            self.store, self.checkpoint_path, self.key, created_at=now)

    def test_first_checkpoint_is_published_as_sequence_one(self):
        self._claim("first", 1.0)
        self._checkpoint(10.0)
        record = publish_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        self.assertEqual(record["sequence"], 1)
        self.assertEqual(record["previous_digest"], _GENESIS_DIGEST)

    def test_republishing_same_checkpoint_is_idempotent(self):
        self._claim("idempotent", 1.0)
        self._checkpoint(10.0)
        first = publish_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        second = publish_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        self.assertEqual(first, second)
        self.assertEqual(len(self.remote.records), 1)

    def test_newer_checkpoint_advances_monotonic_sequence(self):
        self._claim("advance-a", 1.0)
        self._checkpoint(10.0)
        first = publish_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        self._claim("advance-b", 2.0)
        self._checkpoint(20.0)
        second = publish_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        self.assertEqual(second["sequence"], 2)
        self.assertEqual(second["previous_digest"], first["record_digest"])
        self.assertGreater(second["checkpoint_audit_id"], first["checkpoint_audit_id"])

    def test_remote_verification_accepts_latest_anchored_checkpoint(self):
        self._claim("verify", 1.0)
        self._checkpoint(10.0)
        publish_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        result = verify_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        self.assertTrue(result["valid"])
        self.assertEqual(result["remote_sequence"], 1)

    def test_older_local_checkpoint_is_rejected_after_newer_anchor(self):
        self._claim("old", 1.0)
        self._checkpoint(10.0)
        old_checkpoint = open(self.checkpoint_path, encoding="utf-8").read()
        publish_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        self._claim("new", 2.0)
        self._checkpoint(20.0)
        publish_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        with open(self.checkpoint_path, "w", encoding="utf-8") as handle:
            handle.write(old_checkpoint)
        result = verify_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "local_checkpoint_rollback")

    def test_unanchored_newer_local_checkpoint_is_not_verified(self):
        self._claim("anchored", 1.0)
        self._checkpoint(10.0)
        publish_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        self._claim("not-yet-anchored", 2.0)
        self._checkpoint(20.0)
        result = verify_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "local_checkpoint_not_yet_anchored")

    def test_remote_record_digest_tampering_is_rejected(self):
        self._claim("tamper", 1.0)
        self._checkpoint(10.0)
        publish_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        self.remote.records[0]["checkpoint_audit_id"] = 999
        with self.assertRaisesRegex(ValueError, "remote_anchor_record_digest_invalid"):
            verify_provider_audit_remote_anchor(
                self.store, self.checkpoint_path, self.key, self.remote)

    def test_remote_unavailability_fails_closed_without_local_mutation(self):
        self._claim("offline", 1.0)
        self._checkpoint(10.0)
        self.remote.available = False
        before = self.store.verify_provider_request_audit_chain()
        with self.assertRaisesRegex(ConnectionError, "remote_anchor_unavailable"):
            publish_provider_audit_remote_anchor(
                self.store, self.checkpoint_path, self.key, self.remote)
        after = self.store.verify_provider_request_audit_chain()
        self.assertEqual(before, after)
        self.assertEqual(self.remote.records, [])

    def test_concurrent_publishers_cannot_create_two_sequence_one_records(self):
        self._claim("race", 1.0)
        self._checkpoint(10.0)
        barrier = threading.Barrier(2)
        results = []
        errors = []

        def worker():
            barrier.wait(timeout=5)
            try:
                results.append(publish_provider_audit_remote_anchor(
                    self.store, self.checkpoint_path, self.key, self.remote))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(len(self.remote.records), 1)
        self.assertEqual(len(results) + len(errors), 2)
        self.assertTrue(all(record["sequence"] == 1 for record in results))

    def test_remote_empty_state_is_not_reported_as_verified(self):
        self._claim("empty", 1.0)
        self._checkpoint(10.0)
        result = verify_provider_audit_remote_anchor(
            self.store, self.checkpoint_path, self.key, self.remote)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "remote_anchor_empty")


if __name__ == "__main__":
    unittest.main()
