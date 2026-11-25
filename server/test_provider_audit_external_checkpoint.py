import json
import os
import tempfile
import unittest

from server.provider_audit_checkpoint import (
    create_provider_audit_checkpoint,
    verify_provider_audit_checkpoint,
)
from server.sqlite_store import SQLiteMessengerStore


class ProviderAuditExternalCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.directory.name, "messenger.sqlite")
        self.checkpoint_path = os.path.join(self.directory.name, "independent", "audit.checkpoint.json")
        self.key = b"test-only-checkpoint-key-material-32-bytes-minimum"
        self.store = SQLiteMessengerStore(self.db_path)

    def tearDown(self):
        self.store.close()
        self.directory.cleanup()

    def _claim(self, request_id, now=1.0):
        self.store.claim_provider_request(
            "AI-CHECKPOINT", request_id, "digest", "room", "AI-CHECKPOINT", now)

    def test_signed_checkpoint_survives_store_restart_and_verifies_prefix(self):
        self._claim("restart-1")
        self._claim("restart-2", 2.0)
        checkpoint = create_provider_audit_checkpoint(
            self.store, self.checkpoint_path, self.key, created_at=10.0)
        self.assertEqual(checkpoint["audit_id"], 2)
        self.store.close()
        self.store = SQLiteMessengerStore(self.db_path)
        result = verify_provider_audit_checkpoint(
            self.store, self.checkpoint_path, self.key)
        self.assertTrue(result["valid"])
        self.assertEqual(result["checkpoint_audit_id"], 2)
        self.assertEqual(result["latest_audit_id"], 2)

    def test_checkpoint_detects_deletion_of_anchored_tail_event(self):
        self._claim("tail-a")
        self._claim("tail-b", 2.0)
        create_provider_audit_checkpoint(self.store, self.checkpoint_path, self.key, 3.0)
        self.store.connection.execute(
            "DELETE FROM provider_request_audit_events WHERE audit_id=2")
        self.store.connection.commit()
        result = verify_provider_audit_checkpoint(
            self.store, self.checkpoint_path, self.key)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "checkpoint_ahead_of_database")

    def test_checkpoint_detects_database_rollback_behind_anchor(self):
        self._claim("rollback")
        create_provider_audit_checkpoint(self.store, self.checkpoint_path, self.key, 4.0)
        self.store.connection.execute("DELETE FROM provider_request_audit_events")
        self.store.connection.commit()
        result = verify_provider_audit_checkpoint(
            self.store, self.checkpoint_path, self.key)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "checkpoint_ahead_of_database")

    def test_modified_checkpoint_signature_is_rejected(self):
        self._claim("signature")
        create_provider_audit_checkpoint(self.store, self.checkpoint_path, self.key, 5.0)
        document = json.loads(open(self.checkpoint_path, encoding="utf-8").read())
        document["audit_id"] = 99
        with open(self.checkpoint_path, "w", encoding="utf-8") as handle:
            json.dump(document, handle)
        with self.assertRaisesRegex(ValueError, "checkpoint_signature_invalid"):
            verify_provider_audit_checkpoint(self.store, self.checkpoint_path, self.key)

    def test_wrong_signing_key_is_rejected(self):
        self._claim("wrong-key")
        create_provider_audit_checkpoint(self.store, self.checkpoint_path, self.key, 6.0)
        with self.assertRaisesRegex(ValueError, "checkpoint_signature_invalid"):
            verify_provider_audit_checkpoint(
                self.store, self.checkpoint_path, b"different-key-material-32-bytes-long!!")

    def test_checkpoint_creation_fails_closed_if_chain_is_tampered(self):
        self._claim("tampered")
        self.store.connection.execute(
            "UPDATE provider_request_audit_events SET event_type='FAILED' WHERE audit_id=1")
        self.store.connection.commit()
        with self.assertRaisesRegex(ValueError, "provider_audit_chain_invalid"):
            create_provider_audit_checkpoint(
                self.store, self.checkpoint_path, self.key, 7.0)
        self.assertFalse(os.path.exists(self.checkpoint_path))

    def test_checkpoint_cannot_overwrite_database_file(self):
        with self.assertRaisesRegex(ValueError, "checkpoint_must_be_separate_from_database"):
            create_provider_audit_checkpoint(
                self.store, self.db_path, self.key, 8.0)

    def test_checkpoint_file_is_created_with_restricted_permissions(self):
        self._claim("permissions")
        create_provider_audit_checkpoint(self.store, self.checkpoint_path, self.key, 9.0)
        mode = os.stat(self.checkpoint_path).st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_checkpoint_rejects_short_signing_key(self):
        with self.assertRaisesRegex(ValueError, "invalid_checkpoint_signing_key"):
            create_provider_audit_checkpoint(
                self.store, self.checkpoint_path, b"too-short", 10.0)


if __name__ == "__main__":
    unittest.main()
