import multiprocessing
import tempfile
import unittest

from server.rate_limit import RateLimitExceeded, SQLiteSlidingWindowRateLimiter
from server.sqlite_store import SQLiteMessengerStore


def _consume_in_process(database_path, barrier, results, now):
    store = SQLiteMessengerStore(database_path)
    try:
        barrier.wait(timeout=10)
        results.put(store.consume_rate_limit("AI-A", now, 60, 3))
    finally:
        store.close()


class SQLiteRateLimitProcessTests(unittest.TestCase):
    def test_limit_is_shared_across_independent_processes(self):
        context = multiprocessing.get_context("spawn")
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as database:
            initial = SQLiteMessengerStore(database.name)
            initial.close()
            workers = 8
            barrier = context.Barrier(workers)
            results = context.Queue()
            processes = [
                context.Process(
                    target=_consume_in_process,
                    args=(database.name, barrier, results, 1000.0),
                )
                for _ in range(workers)
            ]
            for process in processes:
                process.start()
            outcomes = []
            for _ in processes:
                outcomes.append(results.get(timeout=20))
            for process in processes:
                process.join(timeout=20)
                self.assertEqual(process.exitcode, 0)
            self.assertEqual(outcomes.count(True), 3)
            self.assertEqual(outcomes.count(False), 5)

    def test_principals_are_isolated_and_window_expires(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as database:
            store = SQLiteMessengerStore(database.name)
            limiter = SQLiteSlidingWindowRateLimiter(
                store, max_events=2, window_seconds=10, clock=lambda: 100.0
            )
            try:
                self.assertTrue(limiter.allow("AI-A"))
                self.assertTrue(limiter.allow("AI-A"))
                with self.assertRaises(RateLimitExceeded):
                    limiter.allow("AI-A")
                self.assertTrue(limiter.allow("AI-B"))
                self.assertTrue(limiter.allow("AI-A", now=111.0))
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
