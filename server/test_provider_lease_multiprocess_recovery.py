import multiprocessing
import os
import tempfile
import unittest

from server.sqlite_store import SQLiteMessengerStore


def _claim_worker(database_path, request_id, start_event, result_queue, now):
    store = SQLiteMessengerStore(database_path)
    try:
        start_event.wait(10)
        _, outcome = store.claim_provider_request(
            "AI-MP", request_id, "payload-digest", "room-mp", "AI-MP",
            now, lease_seconds=30.0)
        result_queue.put(outcome)
    finally:
        store.close()


def _crash_after_claim_worker(database_path, request_id, now):
    store = SQLiteMessengerStore(database_path)
    store.claim_provider_request(
        "AI-MP", request_id, "payload-digest", "room-mp", "AI-MP",
        now, lease_seconds=30.0)
    # Deliberately bypass cleanup to model abrupt process death after durable claim.
    os._exit(0)


def _claim_then_crash_worker(database_path, request_id, now):
    store = SQLiteMessengerStore(database_path)
    store.claim_provider_request(
        "AI-MP", request_id, "payload-digest", "room-mp", "AI-MP",
        now, lease_seconds=30.0)
    os._exit(0)


def _reclaim_worker(database_path, request_id, result_queue, now=130.0):
    store = SQLiteMessengerStore(database_path)
    try:
        row, outcome = store.claim_provider_request(
            "AI-MP", request_id, "payload-digest", "room-mp", "AI-MP",
            now, lease_seconds=30.0)
        result_queue.put((outcome, row["attempt_generation"], row["status"]))
    finally:
        store.close()


class ProviderLeaseMultiprocessRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.tempdir.name, "provider.sqlite")
        self.ctx = multiprocessing.get_context("spawn")
        initialized = SQLiteMessengerStore(self.database_path)
        initialized.close()

    def tearDown(self):
        self.tempdir.cleanup()

    def _join_successfully(self, process):
        process.join(15)
        self.assertFalse(process.is_alive(), "worker_process_timeout")
        self.assertEqual(process.exitcode, 0)

    def test_independent_processes_have_exactly_one_initial_claimant(self):
        start = self.ctx.Event()
        results = self.ctx.Queue()
        workers = [
            self.ctx.Process(
                target=_claim_worker,
                args=(self.database_path, "multi-claim", start, results, 100.0),
            )
            for _ in range(6)
        ]
        for worker in workers:
            worker.start()
        start.set()
        outcomes = []
        try:
            for _ in workers:
                outcomes.append(results.get(timeout=15))
        finally:
            for worker in workers:
                self._join_successfully(worker)
        self.assertEqual(outcomes.count("claimed"), 1)
        self.assertEqual(outcomes.count("existing"), 5)
        store = SQLiteMessengerStore(self.database_path)
        try:
            row = store.get_provider_request("AI-MP", "multi-claim")
            self.assertEqual(row["attempt_generation"], 1)
            self.assertEqual(row["status"], "PROCESSING")
        finally:
            store.close()

    def test_abrupt_process_exit_recovers_after_database_reopen(self):
        results = self.ctx.Queue()
        crashed = self.ctx.Process(
            target=_crash_after_claim_worker,
            args=(self.database_path, "crash-recovery", 100.0),
        )
        crashed.start()
        self._join_successfully(crashed)

        # A fresh process reopens the same durable database after lease expiry.
        recovered = self.ctx.Process(
            target=_reclaim_worker,
            args=(self.database_path, "crash-recovery", results),
        )
        recovered.start()
        self._join_successfully(recovered)
        self.assertEqual(results.get(timeout=5), ("claimed", 2, "PROCESSING"))

        store = SQLiteMessengerStore(self.database_path)
        try:
            row = store.get_provider_request("AI-MP", "crash-recovery")
            self.assertEqual(row["attempt_generation"], 2)
            self.assertEqual(row["status"], "PROCESSING")
            self.assertEqual(row["updated_at"], 130.0)
        finally:
            store.close()

    def test_old_generation_cannot_complete_after_process_recovery(self):
        store = SQLiteMessengerStore(self.database_path)
        try:
            _, outcome = store.claim_provider_request(
                "AI-MP", "stale-after-restart", "payload-digest",
                "room-mp", "AI-MP", 100.0, lease_seconds=30.0)
            self.assertEqual(outcome, "claimed")
        finally:
            store.close()

        results = self.ctx.Queue()
        recovered = self.ctx.Process(
            target=_reclaim_worker,
            args=(self.database_path, "stale-after-restart", results, 130.0),
        )
        recovered.start()
        self._join_successfully(recovered)
        self.assertEqual(results.get(timeout=5), ("claimed", 2, "PROCESSING"))

        store = SQLiteMessengerStore(self.database_path)
        try:
            with self.assertRaisesRegex(ValueError, "provider_request_attempt_fenced"):
                store.complete_provider_request(
                    "AI-MP", "stale-after-restart", "payload-digest", "stale response",
                    "fake-provider", "fake-model",
                    {"statement": {}, "signature": "test", "algorithm": "HMAC-SHA256"},
                    "stale-message", 131.0, attempt_generation=1, lease_seconds=30.0)
            row = store.get_provider_request("AI-MP", "stale-after-restart")
            self.assertEqual(row["status"], "PROCESSING")
            self.assertEqual(row["attempt_generation"], 2)
            self.assertIsNone(store.connection.execute(
                "SELECT message_id FROM messages WHERE message_id='stale-message'"
            ).fetchone())
        finally:
            store.close()


    def test_repeated_process_crashes_advance_generation_without_losing_lease_state(self):
        request_id = "repeated-crash"
        for attempt, now in enumerate((100.0, 130.0, 160.0), start=1):
            crashed = self.ctx.Process(
                target=_claim_then_crash_worker,
                args=(self.database_path, request_id, now),
            )
            crashed.start()
            self._join_successfully(crashed)
            store = SQLiteMessengerStore(self.database_path)
            try:
                row = store.get_provider_request("AI-MP", request_id)
                self.assertEqual(row["status"], "PROCESSING")
                self.assertEqual(row["attempt_generation"], attempt)
                self.assertEqual(row["updated_at"], now)
            finally:
                store.close()

        results = self.ctx.Queue()
        final_recovery = self.ctx.Process(
            target=_reclaim_worker,
            args=(self.database_path, request_id, results, 190.0),
        )
        final_recovery.start()
        self._join_successfully(final_recovery)
        self.assertEqual(results.get(timeout=5), ("claimed", 4, "PROCESSING"))
        store = SQLiteMessengerStore(self.database_path)
        try:
            row = store.get_provider_request("AI-MP", request_id)
            self.assertEqual(row["attempt_generation"], 4)
            self.assertEqual(row["status"], "PROCESSING")
            self.assertEqual(row["updated_at"], 190.0)
        finally:
            store.close()

    def test_only_one_independent_process_reclaims_after_crash(self):
        request_id = "crash-reclaim-race"
        crashed = self.ctx.Process(
            target=_crash_after_claim_worker,
            args=(self.database_path, request_id, 100.0),
        )
        crashed.start()
        self._join_successfully(crashed)

        results = self.ctx.Queue()
        workers = [
            self.ctx.Process(
                target=_reclaim_worker,
                args=(self.database_path, request_id, results, 130.0),
            )
            for _ in range(5)
        ]
        for worker in workers:
            worker.start()
        outcomes = []
        try:
            for _ in workers:
                outcomes.append(results.get(timeout=15))
        finally:
            for worker in workers:
                self._join_successfully(worker)

        self.assertEqual(outcomes.count(("claimed", 2, "PROCESSING")), 1)
        self.assertEqual(outcomes.count(("existing", 2, "PROCESSING")), 4)
        store = SQLiteMessengerStore(self.database_path)
        try:
            row = store.get_provider_request("AI-MP", request_id)
            self.assertEqual(row["attempt_generation"], 2)
            self.assertEqual(row["status"], "PROCESSING")
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
