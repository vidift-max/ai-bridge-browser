import json
import os
import tempfile
import threading
import unittest

from server.provider_audit_remote_anchor import (
    _GENESIS_DIGEST,
    _record_digest,
    _record_from_checkpoint,
)
from server.provider_audit_durable_anchor import SQLiteDurableAuditAnchor
from server.provider_audit_remote_service import ProviderAuditRemoteService
from server.test_provider_audit_remote_anchor import FakeRemoteAnchor


def make_record(audit_id, previous=None):
    checkpoint = {
        "audit_id": audit_id,
        "event_hash": "%064x" % audit_id,
        "created_at": float(audit_id),
        "signature": "%064x" % (audit_id + 1000),
    }
    return _record_from_checkpoint(checkpoint, previous)


class RemoteAnchorAdapterConformanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.directory.name, "anchor.sqlite")
        self.adapters = {
            "fake": FakeRemoteAnchor(),
            "sqlite": SQLiteDurableAuditAnchor(self.database_path),
        }

    def tearDown(self):
        self.directory.cleanup()

    def test_initial_append_and_read_after_write(self):
        record = make_record(100)
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                stored = adapter.append_checkpoint(0, record)
                self.assertEqual(stored, record)
                self.assertEqual(adapter.read_latest(), record)

    def test_stale_expected_sequence_cannot_overwrite_committed_head(self):
        first = make_record(100)
        conflicting = make_record(101)
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                adapter.append_checkpoint(0, first)
                with self.assertRaisesRegex(ValueError, "sequence_conflict"):
                    adapter.append_checkpoint(0, conflicting)
                self.assertEqual(adapter.read_latest(), first)

    def test_sequence_gap_is_rejected_without_mutation(self):
        gap = make_record(100)
        gap["sequence"] = 2
        gap["record_digest"] = _record_digest(gap)
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                with self.assertRaisesRegex(ValueError, "sequence_invalid"):
                    adapter.append_checkpoint(0, gap)
                self.assertIsNone(adapter.read_latest())

    def test_concurrent_initial_append_has_one_winner(self):
        record = make_record(100)
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                barrier = threading.Barrier(2)
                successes = []
                failures = []

                def append():
                    barrier.wait(timeout=5)
                    try:
                        successes.append(adapter.append_checkpoint(0, record))
                    except Exception as exc:
                        failures.append(exc)

                threads = [threading.Thread(target=append) for _ in range(2)]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join(timeout=10)
                self.assertFalse(any(thread.is_alive() for thread in threads))
                self.assertEqual(len(successes), 1)
                self.assertEqual(len(failures), 1)
                self.assertEqual(adapter.read_latest(), record)

    def test_previous_digest_fork_is_rejected(self):
        first = make_record(100)
        fork = make_record(101, {
            "sequence": 1,
            "record_digest": "f" * 64,
        })
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                adapter.append_checkpoint(0, first)
                with self.assertRaisesRegex(ValueError, "chain_conflict"):
                    adapter.append_checkpoint(1, fork)
                self.assertEqual(adapter.read_latest(), first)

    def test_non_monotonic_checkpoint_audit_id_is_rejected(self):
        first = make_record(100)
        older = make_record(99, {
            "sequence": 1,
            "record_digest": first["record_digest"],
        })
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                adapter.append_checkpoint(0, first)
                with self.assertRaisesRegex(ValueError, "audit_id_not_monotonic"):
                    adapter.append_checkpoint(1, older)
                self.assertEqual(adapter.read_latest(), first)

    def test_tampered_record_digest_is_rejected_before_write(self):
        record = make_record(100)
        record["record_digest"] = "0" * 64
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                with self.assertRaisesRegex(ValueError, "record_digest_invalid"):
                    adapter.append_checkpoint(0, record)
                self.assertIsNone(adapter.read_latest())

    def test_boolean_expected_sequence_is_rejected(self):
        record = make_record(100)
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                with self.assertRaisesRegex(ValueError, "expected_sequence_invalid"):
                    adapter.append_checkpoint(True, record)
                self.assertIsNone(adapter.read_latest())

    def test_sqlite_committed_record_survives_adapter_restart(self):
        record = make_record(100)
        self.adapters["sqlite"].append_checkpoint(0, record)
        restarted = SQLiteDurableAuditAnchor(self.database_path)
        self.assertEqual(restarted.read_latest(), record)
        self.assertEqual(restarted.verify_history()["records_checked"], 1)


class RemoteAnchorRetryConformanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.anchor = SQLiteDurableAuditAnchor(
            os.path.join(self.directory.name, "anchor.sqlite"))
        self.headers = {
            "Authorization": "Bearer conformance-token",
            "Content-Type": "application/json",
        }
        self.record = make_record(200)

    def tearDown(self):
        self.directory.cleanup()

    def _service(self, anchor):
        return ProviderAuditRemoteService(
            anchor,
            authenticate_token=lambda token: "conformance-agent"
            if token == "conformance-token" else None,
            authorize_principal=lambda principal: principal == "conformance-agent",
        )

    def _post(self, service):
        return service.handle(
            "POST", "/v1/audit-anchor/checkpoints", self.headers,
            json.dumps({"expected_sequence": 0, "record": self.record}).encode())

    def test_exact_retry_is_idempotent(self):
        service = self._service(self.anchor)
        first_status, _ = self._post(service)
        retry_status, retry_body = self._post(service)
        self.assertEqual(first_status, 201)
        self.assertEqual(retry_status, 200)
        self.assertTrue(retry_body["replayed"])
        self.assertEqual(self.anchor.verify_history()["records_checked"], 1)

    def test_different_record_at_same_sequence_is_conflict(self):
        service = self._service(self.anchor)
        self.assertEqual(self._post(service)[0], 201)
        different = make_record(201)
        status, body = service.handle(
            "POST", "/v1/audit-anchor/checkpoints", self.headers,
            json.dumps({"expected_sequence": 0, "record": different}).encode())
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "remote_anchor_sequence_conflict")
        self.assertEqual(self.anchor.read_latest(), self.record)

    def test_timeout_after_commit_is_resolved_by_exact_retry(self):
        class CommitThenTimeout:
            def __init__(self, delegate):
                self.delegate = delegate
                self.first_append = True

            def read_latest(self):
                return self.delegate.read_latest()

            def append_checkpoint(self, expected_sequence, record):
                stored = self.delegate.append_checkpoint(expected_sequence, record)
                if self.first_append:
                    self.first_append = False
                    raise TimeoutError("response lost after durable commit")
                return stored

        service = self._service(CommitThenTimeout(self.anchor))
        first_status, first_body = self._post(service)
        self.assertEqual(first_status, 503)
        self.assertEqual(first_body["error"], "anchor_unavailable")
        self.assertEqual(self.anchor.read_latest(), self.record)

        retry_status, retry_body = self._post(service)
        self.assertEqual(retry_status, 200)
        self.assertTrue(retry_body["replayed"])
        self.assertEqual(self.anchor.verify_history()["records_checked"], 1)


if __name__ == "__main__":
    unittest.main()
