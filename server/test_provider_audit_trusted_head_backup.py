import os
import sqlite3
import tempfile
import unittest

from server.provider_audit_durable_anchor import SQLiteDurableAuditAnchor
from server.provider_audit_remote_anchor import _GENESIS_DIGEST, _record_from_checkpoint
from server.provider_audit_trusted_head_backup import (
    SQLiteTrustedHeadWitness,
    create_verified_anchor_backup,
    restore_anchor_backup_to_new_file,
)


class TrustedHeadBackupRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = self.temp.name
        self.anchor_path = os.path.join(self.root, "anchor.sqlite")
        self.witness_path = os.path.join(self.root, "witness.sqlite")
        self.anchor = SQLiteDurableAuditAnchor(self.anchor_path)
        self.witness = SQLiteTrustedHeadWitness(self.witness_path)

    def tearDown(self):
        self.temp.cleanup()

    def add_record(self, audit_id=10):
        record = _record_from_checkpoint({
            "audit_id": audit_id,
            "event_hash": "%064x" % audit_id,
            "created_at": float(audit_id),
            "signature": "%064x" % (audit_id + 1000),
        }, None)
        self.anchor.append_checkpoint(0, record)
        return {"sequence": 1, "record_digest": record["record_digest"],
                "checkpoint_audit_id": audit_id}

    def test_witness_records_and_reopens_independently(self):
        head = self.add_record()
        self.assertTrue(self.witness.record_head(head)["recorded"])
        reopened = SQLiteTrustedHeadWitness(self.witness_path)
        self.assertEqual(reopened.read_latest(), head)

    def test_exact_witness_retry_is_idempotent(self):
        head = self.add_record()
        self.witness.record_head(head)
        self.assertTrue(self.witness.record_head(head)["replayed"])

    def test_witness_rejects_rollback_and_same_sequence_fork(self):
        head = self.add_record()
        self.witness.record_head(head)
        with self.assertRaisesRegex(ValueError, "trusted_head_witness_rollback"):
            self.witness.record_head({
                "sequence": 0, "record_digest": _GENESIS_DIGEST,
                "checkpoint_audit_id": -1})
        with self.assertRaisesRegex(ValueError, "trusted_head_witness_rollback"):
            self.witness.record_head({
                "sequence": 1, "record_digest": "f" * 64,
                "checkpoint_audit_id": 11})

    def test_witness_rejects_boolean_sequence(self):
        with self.assertRaisesRegex(ValueError, "trusted_anchor_head_invalid"):
            self.witness.record_head({
                "sequence": True, "record_digest": "0" * 64,
                "checkpoint_audit_id": -1})

    def test_witness_update_delete_are_blocked(self):
        head = self.add_record()
        self.witness.record_head(head)
        with sqlite3.connect(self.witness_path) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("UPDATE trusted_head_witness SET sequence=8")
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("DELETE FROM trusted_head_witness")

    def test_witness_verifies_anchor_and_detects_rollback(self):
        head = self.add_record()
        self.witness.record_head(head)
        self.assertTrue(self.witness.verify_anchor(self.anchor)["valid"])
        with sqlite3.connect(self.anchor_path) as db:
            db.execute("DROP TRIGGER provider_audit_anchor_no_delete")
            db.execute("DELETE FROM provider_audit_anchor_records")
        result = self.witness.verify_anchor(self.anchor)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "trusted_head_mismatch")

    def test_verified_backup_and_restore_to_new_file(self):
        head = self.add_record()
        self.witness.record_head(head)
        backup = os.path.join(self.root, "backup.sqlite")
        restored = os.path.join(self.root, "restored.sqlite")
        self.assertTrue(create_verified_anchor_backup(
            self.anchor, backup, self.witness.read_latest())["created"])
        result = restore_anchor_backup_to_new_file(
            backup, restored, self.witness.read_latest())
        self.assertTrue(result["restored"])
        self.assertEqual(SQLiteDurableAuditAnchor(restored).verify_history(
            expected_head=head)["last_sequence"], 1)

    def test_backup_refuses_existing_destination(self):
        head = self.add_record()
        self.witness.record_head(head)
        path = os.path.join(self.root, "existing.sqlite")
        with open(path, "wb") as stream:
            stream.write(b"keep")
        with self.assertRaisesRegex(FileExistsError, "anchor_backup_destination_exists"):
            create_verified_anchor_backup(self.anchor, path, head)
        with open(path, "rb") as stream:
            self.assertEqual(stream.read(), b"keep")

    def test_restore_refuses_existing_destination_without_mutation(self):
        head = self.add_record()
        self.witness.record_head(head)
        backup = os.path.join(self.root, "backup.sqlite")
        create_verified_anchor_backup(self.anchor, backup, head)
        destination = os.path.join(self.root, "existing.sqlite")
        with open(destination, "wb") as stream:
            stream.write(b"do-not-overwrite")
        with self.assertRaisesRegex(FileExistsError, "anchor_restore_destination_exists"):
            restore_anchor_backup_to_new_file(backup, destination, head)
        with open(destination, "rb") as stream:
            self.assertEqual(stream.read(), b"do-not-overwrite")

    def test_truncated_backup_is_rejected_before_restore(self):
        head = self.add_record()
        self.witness.record_head(head)
        backup = os.path.join(self.root, "backup.sqlite")
        create_verified_anchor_backup(self.anchor, backup, head)
        with sqlite3.connect(backup) as db:
            db.execute("DROP TRIGGER provider_audit_anchor_no_delete")
            db.execute("DELETE FROM provider_audit_anchor_records")
        destination = os.path.join(self.root, "restored.sqlite")
        with self.assertRaisesRegex(ValueError, "anchor_restore_backup_chain_verification_failed"):
            restore_anchor_backup_to_new_file(backup, destination, head)
        self.assertFalse(os.path.exists(destination))

    def test_backup_rejects_source_that_disagrees_with_witness(self):
        head = self.add_record()
        self.witness.record_head(head)
        with sqlite3.connect(self.anchor_path) as db:
            db.execute("DROP TRIGGER provider_audit_anchor_no_delete")
            db.execute("DELETE FROM provider_audit_anchor_records")
        with self.assertRaisesRegex(ValueError, "anchor_backup_source_integrity_failed"):
            create_verified_anchor_backup(
                self.anchor, os.path.join(self.root, "bad-backup.sqlite"), head)


if __name__ == "__main__":
    unittest.main()
