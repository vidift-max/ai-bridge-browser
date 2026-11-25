import json
import os
import tempfile
import unittest

from server.sqlite_store import SQLiteMessengerStore


class ProviderRequestStoreTests(unittest.TestCase):
    def test_schema_v12_and_durable_claim_lifecycle(self):
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
        store.save_message_with_idempotency((
            "msg-atomic", "room", "AI-01", ("AI-02",), "already there",
            "other-request", 1, "NORMAL", 1.5))
        with self.assertRaises(Exception):
            store.save_provider_message_and_complete(
                "AI-01", "req-atomic", "digest", message,
                {"statement": {}, "signature": "sig", "algorithm": "HMAC-SHA256"},
                "provider", "model", 2.0)
        self.assertEqual(store.connection.execute(
            "SELECT body FROM messages WHERE message_id='msg-atomic'").fetchone()["body"], "already there")
        self.assertEqual(store.get_provider_request("AI-01", "req-atomic")["status"], "PROCESSING")

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

    def test_failed_request_can_be_claimed_again_after_restart(self):
        store = SQLiteMessengerStore(":memory:")
        store.claim_provider_request("AI-01", "req-4", "digest-e", "room-1", "AI-01", 100.0)
        self.assertTrue(store.fail_provider_request("AI-01", "req-4", "digest-e", "provider_execution_failed", 101.0))
        row, outcome = store.claim_provider_request(
            "AI-01", "req-4", "digest-e", "room-1", "AI-01", 102.0)
        self.assertEqual(outcome, "existing")
        self.assertEqual(row["status"], "FAILED")
        store.close()


if __name__ == "__main__":
    unittest.main()
