import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

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

    def test_lease_renewal_rejects_clock_regression_and_requires_forward_progress(self):
        store = SQLiteMessengerStore(":memory:")
        store.claim_provider_request(
            "AI-01", "clock-renew", "digest", "room", "AI-01", 100.0, lease_seconds=30.0)
        self.assertFalse(store.renew_provider_request_lease(
            "AI-01", "clock-renew", "digest", 1, 90.0, lease_seconds=30.0))
        self.assertEqual(
            store.get_provider_request("AI-01", "clock-renew")["updated_at"], 100.0)
        self.assertFalse(store.renew_provider_request_lease(
            "AI-01", "clock-renew", "digest", 1, 100.0, lease_seconds=30.0))
        self.assertTrue(store.renew_provider_request_lease(
            "AI-01", "clock-renew", "digest", 1, 101.0, lease_seconds=30.0))
        self.assertEqual(
            store.get_provider_request("AI-01", "clock-renew")["updated_at"], 101.0)
        store.close()

    def test_failure_transition_validates_timestamp_and_never_moves_clock_backwards(self):
        store = SQLiteMessengerStore(":memory:")
        store.claim_provider_request(
            "AI-01", "clock-fail", "digest", "room", "AI-01", 100.0)
        with self.assertRaisesRegex(ValueError, "invalid_provider_timestamp"):
            store.fail_provider_request(
                "AI-01", "clock-fail", "digest", "bad_time", float("nan"))
        self.assertEqual(
            store.get_provider_request("AI-01", "clock-fail")["status"], "PROCESSING")
        self.assertTrue(store.fail_provider_request(
            "AI-01", "clock-fail", "digest", "clock_rollback", 90.0))
        row = store.get_provider_request("AI-01", "clock-fail")
        self.assertEqual(row["status"], "FAILED")
        self.assertEqual(row["updated_at"], 100.0)
        retried, outcome = store.claim_provider_request(
            "AI-01", "clock-fail", "digest", "room", "AI-01", 101.0)
        self.assertEqual(outcome, "claimed")
        self.assertEqual(retried["updated_at"], 101.0)
        store.close()

    def test_atomic_completion_rejects_clock_regression_without_persisting(self):
        store = SQLiteMessengerStore(":memory:")
        store.claim_provider_request(
            "AI-01", "clock-complete", "digest", "room", "AI-01", 100.0)
        message = type("Message", (), {
            "message_id": "msg-clock-regression",
            "conversation_id": "room",
            "sender_ai_id": "AI-01",
            "recipient_ai_ids": ("AI-02",),
            "body": "must not persist",
            "client_request_id": "provider-host:clock-complete",
            "sequence": 1,
            "kind": "NORMAL",
            "created_at_epoch_seconds": 99.0,
        })()
        with self.assertRaisesRegex(ValueError, "provider_clock_regression"):
            store.save_provider_message_and_complete(
                "AI-01", "clock-complete", "digest", message,
                {"statement": {}, "signature": "sig", "algorithm": "HMAC-SHA256"},
                "fake", "model", 99.0, 1)
        self.assertEqual(
            store.get_provider_request("AI-01", "clock-complete")["status"], "PROCESSING")
        self.assertIsNone(store.connection.execute(
            "SELECT message_id FROM messages WHERE message_id='msg-clock-regression'").fetchone())
        store.close()

    def test_legacy_completion_path_validates_and_fences_lease_clock(self):
        store = SQLiteMessengerStore(":memory:")
        store.claim_provider_request(
            "AI-01", "legacy-clock", "digest", "room", "AI-01", 100.0, lease_seconds=30.0)
        with self.assertRaisesRegex(ValueError, "provider_clock_regression"):
            store.complete_provider_request(
                "AI-01", "legacy-clock", "digest", "response", "fake", "model",
                {"statement": {}, "signature": "sig", "algorithm": "HMAC-SHA256"},
                "message-1", 99.0, lease_seconds=30.0)
        with self.assertRaisesRegex(ValueError, "provider_request_lease_expired"):
            store.complete_provider_request(
                "AI-01", "legacy-clock", "digest", "response", "fake", "model",
                {"statement": {}, "signature": "sig", "algorithm": "HMAC-SHA256"},
                "message-1", 131.0, lease_seconds=30.0)
        self.assertEqual(
            store.get_provider_request("AI-01", "legacy-clock")["status"], "PROCESSING")
        store.close()

    def test_provider_lease_timestamp_rejects_non_finite_and_non_numeric_values(self):
        store = SQLiteMessengerStore(":memory:")
        for value in (float("nan"), float("inf"), float("-inf"), True, "100"):
            with self.subTest(value=repr(value)):
                with self.assertRaisesRegex(ValueError, "invalid_provider_timestamp"):
                    store.claim_provider_request(
                        "AI-01", "invalid-time-claim", "digest", "room", "AI-01", value)
        row, outcome = store.claim_provider_request(
            "AI-01", "valid-time", "digest", "room", "AI-01", 100.0)
        self.assertEqual(outcome, "claimed")
        original_updated_at = row["updated_at"]
        for value in (float("nan"), float("inf"), float("-inf"), True, "100"):
            with self.subTest(renewal_time=repr(value)):
                with self.assertRaisesRegex(ValueError, "invalid_provider_timestamp"):
                    store.renew_provider_request_lease(
                        "AI-01", "valid-time", "digest", 1, value)
                self.assertEqual(
                    store.get_provider_request("AI-01", "valid-time")["updated_at"],
                    original_updated_at)
        message = type("Message", (), {
            "message_id": "msg-invalid-time",
            "conversation_id": "room",
            "sender_ai_id": "AI-01",
            "recipient_ai_ids": ("AI-02",),
            "body": "must not persist",
            "client_request_id": "provider-host:valid-time",
            "sequence": 1,
            "kind": "NORMAL",
            "created_at_epoch_seconds": 101.0,
        })()
        for value in (float("nan"), float("inf"), float("-inf"), True, "100"):
            with self.subTest(completion_time=repr(value)):
                with self.assertRaisesRegex(ValueError, "invalid_provider_timestamp"):
                    store.save_provider_message_and_complete(
                        "AI-01", "valid-time", "digest", message,
                        {"statement": {}, "signature": "sig", "algorithm": "HMAC-SHA256"},
                        "fake", "model", value, 1)
                self.assertIsNone(store.connection.execute(
                    "SELECT message_id FROM messages WHERE message_id='msg-invalid-time'").fetchone())
                self.assertEqual(
                    store.get_provider_request("AI-01", "valid-time")["status"], "PROCESSING")
        store.close()

    def test_provider_lease_duration_rejects_non_finite_and_non_positive_values(self):
        store = SQLiteMessengerStore(":memory:")
        for value in (0, -1, float("nan"), float("inf"), float("-inf"), True):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "invalid_provider_lease"):
                    store.claim_provider_request(
                        "AI-01", "invalid-claim-" + str(len(str(value))),
                        "digest", "room", "AI-01", 100.0, lease_seconds=value)
                with self.assertRaisesRegex(ValueError, "invalid_provider_lease"):
                    store.renew_provider_request_lease(
                        "AI-01", "req-none", "digest", 1, 100.0, lease_seconds=value)
        store.close()

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


    def test_concurrent_initial_claim_stress_has_exactly_one_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "claim-stress.sqlite")
            stores = [SQLiteMessengerStore(path) for _ in range(8)]
            try:
                for iteration in range(12):
                    barrier = Barrier(len(stores))
                    def claim(index):
                        barrier.wait()
                        return stores[index].claim_provider_request(
                            "AI-01", f"claim-race-{iteration}", "digest",
                            "room-1", "AI-01", 100.0)[1]
                    with ThreadPoolExecutor(max_workers=len(stores)) as pool:
                        outcomes = list(pool.map(claim, range(len(stores))))
                    self.assertEqual(outcomes.count("claimed"), 1)
                    self.assertEqual(outcomes.count("existing"), len(stores) - 1)
                    row = stores[0].get_provider_request("AI-01", f"claim-race-{iteration}")
                    self.assertEqual(row["attempt_generation"], 1)
                    self.assertEqual(row["status"], "PROCESSING")
            finally:
                for store in stores:
                    store.close()

    def test_concurrent_expired_lease_reclaim_stress_has_one_new_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "reclaim-stress.sqlite")
            stores = [SQLiteMessengerStore(path) for _ in range(8)]
            try:
                for iteration in range(12):
                    request_id = f"reclaim-race-{iteration}"
                    stores[0].claim_provider_request(
                        "AI-01", request_id, "digest", "room-1", "AI-01",
                        100.0, lease_seconds=30.0)
                    barrier = Barrier(len(stores))
                    def reclaim(index):
                        barrier.wait()
                        return stores[index].claim_provider_request(
                            "AI-01", request_id, "digest", "room-1", "AI-01",
                            130.0, lease_seconds=30.0)[1]
                    with ThreadPoolExecutor(max_workers=len(stores)) as pool:
                        outcomes = list(pool.map(reclaim, range(len(stores))))
                    self.assertEqual(outcomes.count("claimed"), 1)
                    self.assertEqual(outcomes.count("existing"), len(stores) - 1)
                    row = stores[0].get_provider_request("AI-01", request_id)
                    self.assertEqual(row["attempt_generation"], 2)
                    self.assertEqual(row["status"], "PROCESSING")
            finally:
                for store in stores:
                    store.close()

    def test_renewal_racing_expired_reclaim_preserves_one_valid_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "renew-reclaim-race.sqlite")
            renew_store = SQLiteMessengerStore(path)
            reclaim_store = SQLiteMessengerStore(path)
            try:
                renew_store.claim_provider_request(
                    "AI-01", "renew-reclaim", "digest", "room-1", "AI-01",
                    100.0, lease_seconds=30.0)
                barrier = Barrier(2)
                def renew():
                    barrier.wait()
                    return renew_store.renew_provider_request_lease(
                        "AI-01", "renew-reclaim", "digest", 1, 129.0, 30.0)
                def reclaim():
                    barrier.wait()
                    return reclaim_store.claim_provider_request(
                        "AI-01", "renew-reclaim", "digest", "room-1", "AI-01",
                        130.0, lease_seconds=30.0)[1]
                with ThreadPoolExecutor(max_workers=2) as pool:
                    renewed = pool.submit(renew)
                    reclaimed = pool.submit(reclaim)
                    renewal_result, reclaim_result = renewed.result(), reclaimed.result()
                row = renew_store.get_provider_request("AI-01", "renew-reclaim")
                if renewal_result:
                    self.assertEqual(reclaim_result, "existing")
                    self.assertEqual(row["attempt_generation"], 1)
                    self.assertEqual(row["updated_at"], 129.0)
                else:
                    self.assertEqual(reclaim_result, "claimed")
                    self.assertEqual(row["attempt_generation"], 2)
                    self.assertEqual(row["updated_at"], 130.0)
                self.assertEqual(row["status"], "PROCESSING")
            finally:
                renew_store.close()
                reclaim_store.close()

    def test_completion_racing_expired_reclaim_never_completes_stale_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "complete-reclaim-race.sqlite")
            complete_store = SQLiteMessengerStore(path)
            reclaim_store = SQLiteMessengerStore(path)
            try:
                complete_store.claim_provider_request(
                    "AI-01", "complete-reclaim", "digest", "room-1", "AI-01",
                    100.0, lease_seconds=30.0)
                barrier = Barrier(2)
                def complete():
                    barrier.wait()
                    try:
                        result = complete_store.complete_provider_request(
                            "AI-01", "complete-reclaim", "digest", "response",
                            "fake", "model", {"statement": {}, "signature": "sig",
                            "algorithm": "HMAC-SHA256"}, "message-race", 129.0,
                            lease_seconds=30.0)
                        return ("completed", result["status"])
                    except ValueError as error:
                        return ("rejected", str(error))
                def reclaim():
                    barrier.wait()
                    return reclaim_store.claim_provider_request(
                        "AI-01", "complete-reclaim", "digest", "room-1", "AI-01",
                        130.0, lease_seconds=30.0)[1]
                with ThreadPoolExecutor(max_workers=2) as pool:
                    completion = pool.submit(complete)
                    recovery = pool.submit(reclaim)
                    completion_result, recovery_result = completion.result(), recovery.result()
                row = complete_store.get_provider_request("AI-01", "complete-reclaim")
                if completion_result[0] == "completed":
                    self.assertEqual(recovery_result, "existing")
                    self.assertEqual(row["status"], "COMPLETED")
                    self.assertEqual(row["attempt_generation"], 1)
                else:
                    self.assertEqual(completion_result[1], "provider_request_attempt_fenced")
                    self.assertEqual(recovery_result, "claimed")
                    self.assertEqual(row["status"], "PROCESSING")
                    self.assertEqual(row["attempt_generation"], 2)
            finally:
                complete_store.close()
                reclaim_store.close()

    def test_failure_racing_expired_reclaim_cannot_fail_new_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "failure-reclaim-race.sqlite")
            fail_store = SQLiteMessengerStore(path)
            reclaim_store = SQLiteMessengerStore(path)
            try:
                fail_store.claim_provider_request(
                    "AI-01", "failure-reclaim", "digest", "room-1", "AI-01",
                    100.0, lease_seconds=30.0)
                barrier = Barrier(2)
                def fail():
                    barrier.wait()
                    return fail_store.fail_provider_request(
                        "AI-01", "failure-reclaim", "digest", "late_failure", 129.0, 1)
                def reclaim():
                    barrier.wait()
                    return reclaim_store.claim_provider_request(
                        "AI-01", "failure-reclaim", "digest", "room-1", "AI-01",
                        130.0, lease_seconds=30.0)[1]
                with ThreadPoolExecutor(max_workers=2) as pool:
                    failed = pool.submit(fail)
                    recovery = pool.submit(reclaim)
                    failure_result, recovery_result = failed.result(), recovery.result()
                row = fail_store.get_provider_request("AI-01", "failure-reclaim")
                self.assertEqual(recovery_result, "claimed")
                self.assertEqual(row["status"], "PROCESSING")
                self.assertEqual(row["attempt_generation"], 2)
                if failure_result:
                    self.assertEqual(row["updated_at"], 130.0)
                else:
                    self.assertEqual(row["updated_at"], 130.0)
            finally:
                fail_store.close()
                reclaim_store.close()



if __name__ == "__main__":
    unittest.main()
