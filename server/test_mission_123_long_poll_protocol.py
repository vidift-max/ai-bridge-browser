"""Mission 123: harden the HTTP Long Poll query and delivery contract.

Loopback-only integration tests with synthetic identities and temporary SQLite.
"""
import json
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.rate_limit import SlidingWindowRateLimiter
from server.sqlite_store import SQLiteMessengerStore


class Mission123LongPollProtocolHardeningTest(unittest.TestCase):
    def setUp(self):
        self.db = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.db.close()
        self.tokens = {
            "synthetic-token-ai01": "AI-01",
            "synthetic-token-ai02": "AI-02",
            "synthetic-token-ai03": "AI-03",
        }
        self._start_runtime()

    def _start_runtime(self):
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(self.db.name)
        self.backend = MessengerBackend(
            self.tokens, {"default": {"AI-01", "AI-02"}},
            self.store, authenticator=self.auth)
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter()
        MessengerHandler.operational = None
        MessengerHandler.audio_store = None
        MessengerHandler.voice_control = None
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def _stop_runtime(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.backend.close()

    def tearDown(self):
        self._stop_runtime()
        MessengerHandler.backend = None
        MessengerHandler.authenticator = None
        MessengerHandler.operational = None
        MessengerHandler.audio_store = None
        MessengerHandler.voice_control = None
        import os
        os.unlink(self.db.name)

    def request(self, method, path, token="synthetic-token-ai02", payload=None, timeout=5):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=timeout)
        headers = {}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        body = None
        if payload is not None:
            body = json.dumps(payload)
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, data

    def send(self, message_id, request_id, body=None):
        return self.request("POST", "/v1/messages", "synthetic-token-ai01", {
            "messageId": message_id, "conversationId": "default",
            "recipientAiIds": ["AI-02"], "body": body or message_id,
            "clientRequestId": request_id,
        })

    def poll_path(self, after=0, limit=10, timeout=0):
        return (f"/v1/conversations/default/messages/wait?"
                f"after={after}&limit={limit}&timeout={timeout}")

    def poll(self, after=0, limit=10, timeout=0, token="synthetic-token-ai02"):
        return self.request("GET", self.poll_path(after, limit, timeout), token,
                            timeout=max(5, timeout + 2))

    def test_missing_query_parameter_is_rejected(self):
        status, result = self.request(
            "GET", "/v1/conversations/default/messages/wait?after=0&limit=10")
        self.assertEqual((status, result["error"]), (400, "invalid_long_poll"))

    def test_duplicate_query_parameter_is_rejected(self):
        status, result = self.request(
            "GET", "/v1/conversations/default/messages/wait?after=0&after=1&limit=10&timeout=0")
        self.assertEqual((status, result["error"]), (400, "invalid_long_poll"))

    def test_unknown_query_parameter_is_rejected(self):
        status, result = self.request(
            "GET", "/v1/conversations/default/messages/wait?after=0&limit=10&timeout=0&extra=1")
        self.assertEqual((status, result["error"]), (400, "invalid_long_poll"))

    def test_non_decimal_and_out_of_range_values_are_rejected(self):
        invalid_queries = [
            "after=-1&limit=10&timeout=0",
            "after=0&limit=0&timeout=0",
            "after=0&limit=101&timeout=0",
            "after=0&limit=10&timeout=26",
            "after=9007199254740992&limit=10&timeout=0",
            "after=%D9%A0&limit=10&timeout=0",
        ]
        for query in invalid_queries:
            with self.subTest(query=query):
                status, result = self.request(
                    "GET", "/v1/conversations/default/messages/wait?" + query)
                self.assertEqual((status, result["error"]), (400, "invalid_long_poll"))

    def test_long_poll_requires_authentication(self):
        status, result = self.request(
            "GET", self.poll_path(), token=None)
        self.assertEqual(status, 401)
        self.assertEqual(result["error"], "authentication_required")

    def test_zero_timeout_returns_empty_success_without_waiting(self):
        started = time.monotonic()
        status, result = self.poll(timeout=0)
        elapsed = time.monotonic() - started
        self.assertEqual(status, 200)
        self.assertEqual(result["messages"], [])
        self.assertLess(elapsed, 1.0)

    def test_already_queued_message_is_returned_immediately(self):
        self.send("m123-immediate", "m123-immediate-request")
        started = time.monotonic()
        status, result = self.poll(timeout=5)
        self.assertEqual(status, 200)
        self.assertEqual([m["messageId"] for m in result["messages"]],
                         ["m123-immediate"])
        self.assertLess(time.monotonic() - started, 1.0)

    def test_batch_limit_and_sequence_order_are_respected(self):
        for index in range(3):
            self.send(f"m123-batch-{index}", f"m123-batch-request-{index}")
        status, result = self.poll(limit=2)
        self.assertEqual(status, 200)
        self.assertEqual([m["messageId"] for m in result["messages"]],
                         ["m123-batch-0", "m123-batch-1"])
        self.assertEqual([m["sequence"] for m in result["messages"]], [1, 2])

    def test_after_cursor_excludes_older_sequences(self):
        for index in range(3):
            self.send(f"m123-cursor-{index}", f"m123-cursor-request-{index}")
        status, result = self.poll(after=2)
        self.assertEqual(status, 200)
        self.assertEqual([m["messageId"] for m in result["messages"]],
                         ["m123-cursor-2"])
        self.assertEqual(result["messages"][0]["sequence"], 3)

    def test_multiple_waiters_are_woken_and_receive_same_unacked_message(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(self.poll, 0, 10, 3)
            second = pool.submit(self.poll, 0, 10, 3)
            time.sleep(0.15)
            self.send("m123-fanout", "m123-fanout-request")
            first_status, first_result = first.result(timeout=5)
            second_status, second_result = second.result(timeout=5)
        self.assertEqual((first_status, second_status), (200, 200))
        self.assertEqual(first_result["messages"][0]["messageId"], "m123-fanout")
        self.assertEqual(second_result["messages"][0]["messageId"], "m123-fanout")

    def test_ack_removes_message_from_all_future_waiters(self):
        self.send("m123-acked", "m123-acked-request")
        ack_status, ack = self.request(
            "POST", "/v1/messages/m123-acked/ack", "synthetic-token-ai02", {})
        self.assertEqual((ack_status, ack["state"]), (200, "ACKNOWLEDGED"))
        status, result = self.poll(timeout=0)
        self.assertEqual(status, 200)
        self.assertEqual(result["messages"], [])


if __name__ == "__main__":
    unittest.main()
