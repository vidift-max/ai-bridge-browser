import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

from server.auth import Authenticator
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore


class Mission99MessageContractTest(unittest.TestCase):
    def setUp(self):
        self.tokens = {"token-ai-01": "AI-01", "token-ai-02": "AI-02",
                       "token-outsider": "AI-03"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(":memory:")
        self.backend = MessengerBackend(
            self.tokens, {"room-ai-01-ai-02": {"AI-01", "AI-02"}},
            self.store, authenticator=self.auth)

    def tearDown(self):
        self.backend.close()

    def test_long_poll_wakes_when_ai_01_sends_to_ai_02(self):
        entered = threading.Event()

        def receive():
            entered.set()
            return self.backend.wait_for_messages(
                "token-ai-02", "room-ai-01-ai-02",
                after_sequence=0, limit=10, timeout_seconds=2)

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(receive)
            self.assertTrue(entered.wait(timeout=1))
            # A short scheduling window makes this exercise the waiting path;
            # if the message arrives first, the initial pending check still finds it.
            time.sleep(0.03)
            sent = self.backend.submit(
                "token-ai-01", "m99-message-1", "room-ai-01-ai-02",
                ["AI-02"], "Teste de mensagem AI-01 para AI-02",
                "m99-request-1")
            received = future.result(timeout=3)

        self.assertEqual(sent.sender_ai_id, "AI-01")
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].message_id, "m99-message-1")
        self.assertEqual(received[0].sender_ai_id, "AI-01")
        self.assertEqual(received[0].recipient_ai_ids, ("AI-02",))
        self.assertEqual(received[0].body, "Teste de mensagem AI-01 para AI-02")

    def test_ack_is_recipient_only_and_removes_message_from_pending(self):
        self.backend.submit("token-ai-01", "m99-ack", "room-ai-01-ai-02",
                            ["AI-02"], "ACK boundary", "m99-ack-request")

        with self.assertRaises(PermissionError):
            self.backend.acknowledge("token-ai-01", "m99-ack")
        with self.assertRaises(PermissionError):
            self.backend.acknowledge("token-outsider", "m99-ack")

        first = self.backend.acknowledge("token-ai-02", "m99-ack")
        second = self.backend.acknowledge("token-ai-02", "m99-ack")
        self.assertIn("AI-02", first.acknowledged_by)
        self.assertEqual(first.acknowledged_by, second.acknowledged_by)
        self.assertEqual(self.backend.pending(
            "token-ai-02", "room-ai-01-ai-02", 0, 10), [])

    def test_non_member_cannot_wait_read_history_or_ack(self):
        with self.assertRaises(PermissionError):
            self.backend.wait_for_messages(
                "token-outsider", "room-ai-01-ai-02", 0, 10, 0)
        with self.assertRaises(PermissionError):
            self.backend.pending("token-outsider", "room-ai-01-ai-02", 0, 10)
        with self.assertRaises(PermissionError):
            self.backend.history("token-outsider", "room-ai-01-ai-02", 0, 10)
        with self.assertRaises(PermissionError):
            self.backend.transport_capabilities(
                "token-outsider", "room-ai-01-ai-02")

    def test_long_poll_timeout_and_input_bounds(self):
        started = time.monotonic()
        result = self.backend.wait_for_messages(
            "token-ai-02", "room-ai-01-ai-02", 0, 10, 0.02)
        elapsed = time.monotonic() - started
        self.assertEqual(result, [])
        self.assertLess(elapsed, 0.5)

        for args in ((-1, 10, 0), (0, 101, 0), (0, 10, 26)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.backend.wait_for_messages(
                    "token-ai-02", "room-ai-01-ai-02", *args)

    def test_transport_contract_keeps_only_http_long_poll_enabled(self):
        capabilities = self.backend.transport_capabilities(
            "token-ai-01", "room-ai-01-ai-02")
        self.assertEqual(capabilities["defaultTransport"], "HTTP_LONG_POLL")
        self.assertTrue(capabilities["transports"]["httpLongPoll"]["enabled"])
        self.assertFalse(capabilities["transports"]["webSocket"]["enabled"])
        self.assertFalse(capabilities["transports"]["serverPush"]["enabled"])
        self.assertTrue(capabilities["cursor"]["ackRequired"])


if __name__ == "__main__":
    unittest.main()
