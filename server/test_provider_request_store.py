import json
import os
import tempfile
import unittest

from server.sqlite_store import SQLiteMessengerStore


class ProviderRequestStoreTests(unittest.TestCase):
    def test_schema_v13_and_durable_claim_lifecycle(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "messenger.sqlite")
            store = SQLiteMessengerStore(path)
            row, outcome = store.claim_provider_request(
                "AI-01", "req-1", "digest-a", "room-1", "AI-01", 100.0)
            self.assertEqual(outcome, "claimed")
            self.assertEqual(row["status"], "PROCESSING")
            store.close()

            reopened = SQLiteMessengerStore(path)
            row = reopened.get_provider_request("AI-01", "req-1")
            self.assertEqual(row["status"], "PROCESSING")
            self.assertEqual(row["request_digest"], "digest-a")
            reopened.close()

    def test_atomic_provider_message_completion_rolls_back_together(self):
        store = SQLiteMessengerStore(":memory:")
        store.claim_provider_request("AI-01", "req-atomic", "digest", "room", "AI-01", 1.0)
        message = type("Message", (), {
            "message_id": "msg-atomic",
            "conversation_id": "room",
            "sender_ai_id": "AI-01",
            "recipient_ai_ids": ("AI-02",),
            "body": "hello",
            "client_request_id": "provider-host:req-atomic",
            "sequence": 1,
            "kind": "NORMAL",
            "created_at_epoch_seconds": 2.0,
        })()
        store.connection.execute(
            """INSERT INTO messages(
               message_id,conversation_id,sender_ai_id,recipient_ai_ids,body,
               client_request_id,sequence,kind,created_at_epoch_seconds)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            ("msg-atomic","room","AI-01","AI-02","already there",
             "other-request",1,"NORMAL",1.5))
        store.connection.commit()
        with self.assertRaises(Exception):
            store.save_provider_message_and_complete(
                "AI-01", "req-atomic", "digest", message,
                {"statement": {}, "signature": "sig", "algorithm": "HMAC-SHA256"},
                "provider", "model", 2.0)
        self.assertEqual(store.connection.execute(
            "SELECT body FROM messages WHERE message_id='msg-atomic'").fetchone()["body"], "already there")
        self.assertEqual(store.get_provider_request("AI-01", "req-atomic")["status"], "PROCESSING")

    def test_atomic_provider_message_completion_rejects_expired_lease(self):
        store = SQLiteMessengerStore(":memory:")
        store.claim_provider_request(
            "AI-01", "req-expired-complete", "digest-exp", "room-1", "AI-01",
            100.0, lease_seconds=30.0)
        message = type("Message", (), {
            "message_id": "msg-expired-complete",
            "conversation_id": "room-1",
            "sender_ai_id": "AI-01",
            "recipient_ai_ids": ("AI-02",),
            "body": "must not persist",
            "client_request_id": "provider-host:req-expired-complete",
            "sequence": 1,
            "kind": "NORMAL",
            "created_at_epoch_seconds": 130.0,
        })()
        with self.assertRaisesRegex(ValueError, "provider_request_lease_expired"):
            store.save_provider_message_and_complete(
                "AI-01", "req-expired-complete", "digest-exp", message,
                {"statement": {}, "signature": "sig", "algorithm": "HMAC-SHA256"},
                "fake", "model", 130.0, 1, lease_seconds=30.0)
        self.assertIsNone(store.connection.execute(
            "SELECT message_id FROM messages WHERE message_id='msg-expired-complete'").fetchone())
        row = store.get_provider_request("AI-01", "req-expired-complete")
        self.assertEqual(row["status"], "PROCESSING")
        store.close()

    def test_same_request_claim_is_stable_across_two_store_connections(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "concurrent.sqlite")
            first = SQLiteMessengerStore(path)
            second = SQLiteMessengerStore(path)
            _, first_outcome = first.claim_provider_request(
                "AI-01", "req-concurrent", "digest", "room", "AI-01", 1.0)
            row, second_outcome = second.claim_provider_request(
                "AI-01", "req-concurrent", "digest", "room", "AI-01", 2.0)
            self.assertEqual(first_outcome, "claimed")
            self.assertEqual(second_outcome, "existing")
            self.assertEqual(row["status"], "PROCESSING")
            first.close()
            second.close()

    def test_same_request_recovers_completed_record(self):
        store = SQLiteMessengerStore(":memory:")
        row, outcome = store.claim_provider_request(
            "AI-01", "req-2", "digest-b", "room-1", "AI-01", 100.0)
        self.assertEqual(outcome, "claimed")
        attestation = {"statement": {"responseSha256": "x"}, "signature": "sig", "algorithm": "HMAC-SHA256"}
        completed = store.complete_provider_request(
            "AI-01", "req-2", "digest-b", "hello", "openai", "model-x",
            attestation, "provider-msg-1", 101.0)
        self.assertEqual(completed["status"], "COMPLETED")
        recovered, outcome = store.claim_provider_request(
            "AI-01", "req-2", "digest-b", "room-1", "AI-01", 102.0)
        self.assertEqual(outcome, "existing")
        self.assertEqual(recovered["response_text"], "hello")
        self.assertEqual(recovered["message_id"], "provider-msg-1")
        self.assertEqual(json.loads(recovered["attestation_json"])["signature"], "sig")

    def test_same_request_with_different_payload_digest_conflicts(self):
        store = SQLiteMessengerStore(":memory:")
        store.claim_provider_request("AI-01", "req-3", "digest-c", "room-1", "AI-01", 100.0)
        row, outcome = store.claim_provider_request(
            "AI-01", "req-3", "digest-d", "room-1", "AI-01", 101.0)
        self.assertEqual(outcome, "conflict")
        self.assertEqual(row["request_digest"], "digest-c")


    def test_provider_lease_renewal_and_expired_generation_rejection(self):
        store = SQLiteMessengerStore(":memory:")
        first, outcome = store.claim_provider_request(
            "AI-01", "req-lease", "digest-lease", "room-1", "AI-01", 100.0,
            lease_seconds=360.0)
        self.assertEqual(outcome, "claimed")
        self.assertTrue(store.renew_provider_request_lease(
            "AI-01", "req-lease", "digest-lease", 1, 200.0, 360.0))
        self.assertFalse(store.renew_provider_request_lease(
            "AI-01", "req-lease", "digest-lease", 1, 561.0, 360.0))
        second, outcome = store.claim_provider_request(
            "AI-01", "req-lease", "digest-lease", "room-1", "AI-01", 561.0,
            lease_seconds=360.0)
        self.assertEqual(outcome, "claimed")
        self.assertEqual(second["attempt_generation"], 2)
        self.assertFalse(store.renew_provider_request_lease(
            "AI-01", "req-lease", "digest-lease", 1, 562.0, 360.0))
        self.assertTrue(store.renew_provider_request_lease(
            "AI-01", "req-lease", "digest-lease", 2, 562.0, 360.0))
        store.close()

    def test_stale_provider_attempt_is_fenced_after_lease_reclaim(self):
        store = SQLiteMessengerStore(":memory:")
        first, outcome = store.claim_provider_request(
            "AI-01", "req-fence", "digest-f", "room-1", "AI-01", 100.0,
            lease_seconds=30.0)
        self.assertEqual(outcome, "claimed")
        self.assertEqual(first["attempt_generation"], 1)

        second, outcome = store.claim_provider_request(
            "AI-01", "req-fence", "digest-f", "room-1", "AI-01", 131.0,
            lease_seconds=30.0)
        self.assertEqual(outcome, "claimed")
        self.assertEqual(second["attempt_generation"], 2)

        self.assertFalse(store.fail_provider_request(
            "AI-01", "req-fence", "digest-f", "late_failure", 132.0, 1))
        row = store.get_provider_request("AI-01", "req-fence")
        self.assertEqual(row["status"], "PROCESSING")
        self.assertEqual(row["attempt_generation"], 2)

        message = type("Message", (), {
            "message_id": "msg-fenced",
            "conversation_id": "room-1",
            "sender_ai_id": "AI-01",
            "recipient_ai_ids": ("AI-02",),
            "body": "current attempt",
            "client_request_id": "provider-host:req-fence",
            "sequence": 1,
            "kind": "NORMAL",
            "created_at_epoch_seconds": 133.0,
        })()
        with self.assertRaisesRegex(ValueError, "provider_request_attempt_fenced"):
            store.save_provider_message_and_complete(
                "AI-01", "req-fence", "digest-f", message,
                {"statement": {}, "signature": "sig", "algorithm": "HMAC-SHA256"},
                "fake", "model", 134.0, 1, lease_seconds=30.0)
        with self.assertRaisesRegex(ValueError, "provider_request_attempt_fenced"):
            store.complete_provider_request(
                "AI-01", "req-fence", "digest-f", "late response", "fake", "model",
                {"statement": {}, "signature": "sig", "algorithm": "HMAC-SHA256"},
                "late-message", 134.0, 1)
        with self.assertRaisesRegex(ValueError, "provider_request_attempt_fenced"):
            store.save_provider_message_and_complete(
                "AI-01", "req-fence", "digest-f", message,
                {"statement": {}, "signature": "sig", "algorithm": "HMAC-SHA256"},
                "fake", "model", 134.0, 1)
        completed, created = store.save_provider_message_and_complete(
            "AI-01", "req-fence", "digest-f", message,
            {"statement": {}, "signature": "sig", "algorithm": "HMAC-SHA256"},
            "fake", "model", 135.0, 2)
        self.assertTrue(created)
        self.assertEqual(completed["status"], "COMPLETED")
        self.assertEqual(completed["attempt_generation"], 2)
        store.close()

    def test_unexpired_processing_claim_is_not_stolen(self):
        store = SQLiteMessengerStore(":memory:")
        first, outcome = store.claim_provider_request(
            "AI-01", "req-live", "digest-live", "room-1", "AI-01", 100.0,
            lease_seconds=30.0)
        self.assertEqual(outcome, "claimed")
        second, outcome = store.claim_provider_request(
            "AI-01", "req-live", "digest-live", "room-1", "AI-01", 129.0,
            lease_seconds=30.0)
        self.assertEqual(outcome, "existing")
        self.assertEqual(second["attempt_generation"], first["attempt_generation"])
        store.close()

    def test_failed_request_can_be_claimed_again_after_restart(self):
        store = SQLiteMessengerStore(":memory:")
        store.claim_provider_request("AI-01", "req-4", "digest-e", "room-1", "AI-01", 100.0)
        self.assertTrue(store.fail_provider_request("AI-01", "req-4", "digest-e", "provider_execution_failed", 101.0))
        row, outcome = store.claim_provider_request(
            "AI-01", "req-4", "digest-e", "room-1", "AI-01", 102.0)
        self.assertEqual(outcome, "claimed")
        self.assertEqual(row["status"], "PROCESSING")
        store.close()


if __name__ == "__main__":
    unittest.main()
