"""Mission 125: persisted Long Poll recovery and message-retention guarantees."""
import os
import tempfile
import unittest
from server.auth import Authenticator
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore
from server.retention_policy import ONE_HOUR_SECONDS, ONE_DAY_SECONDS

class Mission125LongPollRecoveryRetentionTest(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.db_path = handle.name
        handle.close()
        self.tokens = {"synthetic-token-ai01": "AI-01", "synthetic-token-ai02": "AI-02"}
        self._start()

    def _start(self):
        self.store = SQLiteMessengerStore(self.db_path)
        self.auth = Authenticator(self.tokens)
        self.backend = MessengerBackend(
            self.tokens, {"default": {"AI-01", "AI-02"}},
            self.store, authenticator=self.auth)

    def _restart(self):
        self.backend.close()
        self._start()

    def tearDown(self):
        self.backend.close()
        os.unlink(self.db_path)

    def _send(self, message_id, request_id, body=None, kind="NORMAL", conversation="default"):
        return self.backend.submit(
            "synthetic-token-ai01", message_id, conversation, ["AI-02"],
            body or message_id, request_id, kind)

    def test_sequence_continues_monotonically_after_restart(self):
        first = self._send("m125-seq-1", "m125-seq-r1")
        self._restart()
        second = self._send("m125-seq-2", "m125-seq-r2")
        self.assertEqual((first.sequence, second.sequence), (1, 2))

    def test_unacknowledged_delivery_is_restored_after_restart(self):
        self._send("m125-pending", "m125-pending-r")
        self._restart()
        pending = self.backend.pending("synthetic-token-ai02", "default")
        self.assertEqual([m.message_id for m in pending], ["m125-pending"])

    def test_acknowledgement_remains_effective_after_restart(self):
        self._send("m125-acked", "m125-acked-r")
        self.backend.acknowledge("synthetic-token-ai02", "m125-acked")
        self._restart()
        self.assertEqual(self.backend.pending("synthetic-token-ai02", "default"), [])

    def test_exact_idempotent_retry_after_restart_returns_original_message(self):
        original = self._send("m125-idem", "m125-idem-r", "same body")
        self._restart()
        retry = self._send("m125-idem", "m125-idem-r", "same body")
        self.assertEqual((retry.message_id, retry.sequence), (original.message_id, original.sequence))

    def test_changed_payload_retry_after_restart_is_rejected(self):
        self._send("m125-conflict", "m125-conflict-r", "original")
        self._restart()
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            self._send("m125-conflict", "m125-conflict-r", "changed")

    def test_recipient_identity_is_preserved_across_restart(self):
        self._send("m125-recipient", "m125-recipient-r")
        self._restart()
        self.assertEqual(self.backend.pending("synthetic-token-ai02", "default")[0].recipient_ai_ids, ("AI-02",))
        with self.assertRaises(PermissionError):
            self.backend.pending("synthetic-token-ai01", "default")

    def test_group_normal_message_uses_one_hour_retention(self):
        message = self._send("m125-ret-group", "m125-ret-group-r")
        self.assertEqual(self.backend.message_expires_at(message) - message.created_at_epoch_seconds,
                         ONE_HOUR_SECONDS)

    def test_mission_message_uses_one_day_retention(self):
        message = self._send("m125-ret-mission", "m125-ret-mission-r", kind="MISSION")
        self.assertEqual(self.backend.message_expires_at(message) - message.created_at_epoch_seconds,
                         ONE_DAY_SECONDS)

    def test_private_normal_message_uses_one_day_retention(self):
        self.backend.create_conversation("synthetic-token-ai01", "private-room",
                                          ["AI-01", "AI-02"], "PRIVATE")
        message = self._send("m125-ret-private", "m125-ret-private-r",
                             conversation="private-room")
        self.assertEqual(self.backend.message_expires_at(message) - message.created_at_epoch_seconds,
                         ONE_DAY_SECONDS)

    def test_expiry_purge_removes_delivery_and_releases_idempotency_key(self):
        message = self._send("m125-expired", "m125-expired-r")
        expired_at = message.created_at_epoch_seconds - ONE_HOUR_SECONDS - 1
        self.store._connection.execute(
            "UPDATE messages SET created_at_epoch_seconds=? WHERE message_id=?",
            (expired_at, message.message_id))
        self.store._connection.commit()
        self._restart()
        self.assertEqual(self.backend.pending("synthetic-token-ai02", "default"), [])
        replacement = self._send("m125-replacement", "m125-expired-r", "replacement")
        self.assertEqual(replacement.message_id, "m125-replacement")
        self.assertEqual(replacement.sequence, 2)

if __name__ == "__main__":
    unittest.main()
