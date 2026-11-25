import json
import os
import sqlite3
import tempfile
import unittest

from server.provider_audit_durable_anchor import (
    SQLiteDurableAuditAnchor,
    compare_provider_audit_anchor_copies,
)
from server.provider_audit_remote_anchor import (
    _GENESIS_DIGEST,
    _record_from_checkpoint,
)


class AuditChainRecoverySecurityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.left_path = os.path.join(self.directory.name, "left.sqlite")
        self.right_path = os.path.join(self.directory.name, "right.sqlite")
        self.left = SQLiteDurableAuditAnchor(self.left_path)
        self.right = SQLiteDurableAuditAnchor(self.right_path)

    def tearDown(self):
        self.directory.cleanup()

    def _record(self, sequence, audit_id, previous_digest):
        previous = None if sequence == 1 else {
            "sequence": sequence - 1,
            "record_digest": previous_digest,
        }
        payload = {
            "audit_id": audit_id,
            "event_hash": "%064x" % audit_id,
            "created_at": float(sequence),
            "signature": "%064x" % (audit_id + 9000),
        }
        return _record_from_checkpoint(payload, previous)

    def _append_chain(self, anchor, count=3, audit_offset=100):
        previous = _GENESIS_DIGEST
        for sequence in range(1, count + 1):
            record = self._record(sequence, audit_offset + sequence, previous)
            anchor.append_checkpoint(sequence - 1, record)
            previous = record["record_digest"]
        return {
            "sequence": count,
            "record_digest": previous,
            "checkpoint_audit_id": audit_offset + count,
        }

    def _tamper_connection(self, path, sql, values=()):
        connection = sqlite3.connect(path)
        try:
            connection.execute("DROP TRIGGER IF EXISTS provider_audit_anchor_no_update")
            connection.execute("DROP TRIGGER IF EXISTS provider_audit_anchor_no_delete")
            connection.execute(sql, values)
            connection.commit()
        finally:
            connection.close()

    def test_independent_trusted_head_accepts_exact_complete_history(self):
        head = self._append_chain(self.left)
        result = self.left.verify_history(expected_head=head)
        self.assertTrue(result["valid"])
        self.assertEqual(result["last_sequence"], 3)

    def test_suffix_truncation_is_detected_with_external_head_witness(self):
        head = self._append_chain(self.left)
        self._tamper_connection(
            self.left_path,
            "DELETE FROM provider_audit_anchor_records WHERE sequence=3")
        result = self.left.verify_history(expected_head=head)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "trusted_head_mismatch")
        self.assertEqual(result["actual_head"]["sequence"], 2)

    def test_full_history_rollback_to_empty_is_detected_with_external_witness(self):
        head = self._append_chain(self.left)
        self._tamper_connection(
            self.left_path, "DELETE FROM provider_audit_anchor_records")
        result = self.left.verify_history(expected_head=head)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "trusted_head_mismatch")
        self.assertEqual(result["actual_head"]["sequence"], 0)

    def test_old_record_tampering_is_detected_and_not_repaired(self):
        self._append_chain(self.left)
        before = self.left.read_latest()
        self._tamper_connection(
            self.left_path,
            "UPDATE provider_audit_anchor_records SET record_json=? WHERE sequence=1",
            ('{"corrupt":true}',))
        result = self.left.verify_history()
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "history_record_corrupt")
        self.assertEqual(self.left.read_latest(), before)

    def test_malformed_json_is_a_fail_closed_result_not_an_exception(self):
        self._append_chain(self.left, count=1)
        self._tamper_connection(
            self.left_path,
            "UPDATE provider_audit_anchor_records SET record_json=? WHERE sequence=1",
            ("{not-json",))
        result = self.left.verify_history()
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "history_record_corrupt")

    def test_two_valid_but_divergent_copies_are_rejected(self):
        self._append_chain(self.left, count=2, audit_offset=100)
        self._append_chain(self.right, count=2, audit_offset=200)
        result = compare_provider_audit_anchor_copies(self.left, self.right)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "anchor_copy_divergence")

    def test_matching_copies_and_external_head_are_accepted(self):
        head = self._append_chain(self.left, count=2, audit_offset=100)
        self._append_chain(self.right, count=2, audit_offset=100)
        result = compare_provider_audit_anchor_copies(
            self.left, self.right, expected_head=head)
        self.assertTrue(result["valid"])
        self.assertEqual(result["sequence"], 2)

    def test_corrupt_copy_blocks_comparison_without_automatic_repair(self):
        self._append_chain(self.left, count=2)
        self._append_chain(self.right, count=2)
        before = self.right.read_latest()
        self._tamper_connection(
            self.right_path,
            "UPDATE provider_audit_anchor_records SET record_digest=? WHERE sequence=1",
            ("f" * 64,))
        result = compare_provider_audit_anchor_copies(self.left, self.right)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "anchor_copy_integrity_failed")
        self.assertEqual(self.right.read_latest(), before)

    def test_malformed_external_head_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "trusted_anchor_head_invalid"):
            self.left.verify_history(expected_head={"sequence": True})


if __name__ == "__main__":
    unittest.main()
