import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

from tools.firebase_first_contact_smoke import validate_config, run_probe

BASE = {
    "MESSENGER_FIREBASE_DATABASE_URL": "https://demo-default-rtdb.firebaseio.com",
    "MESSENGER_FIREBASE_AI_A_ID": "AI-01",
    "MESSENGER_FIREBASE_AI_B_ID": "AI-02",
    "MESSENGER_FIREBASE_AI_A_ID_TOKEN": "secret-token-a",
    "MESSENGER_FIREBASE_AI_B_ID_TOKEN": "secret-token-b",
    "MESSENGER_FIREBASE_CONVERSATION_ID": "private-ai-01-ai-02",
}


class FakeRtdb:
    def __init__(self):
        self.messages = {}
        self.acks = {}
        self.requests = []
        self.lock = threading.Lock()

    def handler(self):
        state = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def _body(self):
                length = int(self.headers.get("Content-Length", "0"))
                return json.loads(self.rfile.read(length)) if length else None

            def _reply(self, value, status=200):
                data = json.dumps(value).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _route(self, method):
                parsed = urlsplit(self.path)
                query = parse_qs(parsed.query)
                token = query.get("auth", [""])[0]
                with state.lock:
                    state.requests.append((method, parsed.path, token))
                path = parsed.path
                if path == "/messenger/identities/AI-01.json" and method == "GET":
                    return self._reply({"aiId": "AI-01", "uid": "uid-a"})
                if path == "/messenger/identities/AI-02.json" and method == "GET":
                    return self._reply({"aiId": "AI-02", "uid": "uid-b"})
                if path == "/messenger/conversations/private-ai-01-ai-02.json" and method == "GET":
                    return self._reply({"members": {"AI-01": True, "AI-02": True}})
                if path.endswith("/messages.json") and method == "POST":
                    with state.lock:
                        state.messages["-message-key"] = self._body()
                    return self._reply({"name": "-message-key"})
                if path.endswith("/messages.json") and method == "GET":
                    return self._reply(state.messages)
                if path.endswith("/acks/-message-key/AI-02.json") and method == "PUT":
                    state.acks["-message-key"] = self._body()
                    return self._reply(state.acks["-message-key"])
                if path.endswith("/acks/-message-key/AI-02.json") and method == "GET":
                    return self._reply(state.acks.get("-message-key"))
                return self._reply({"error": "not_found"}, 404)

            def do_GET(self):
                self._route("GET")

            def do_POST(self):
                self._route("POST")

            def do_PUT(self):
                self._route("PUT")

        return Handler


class FirebaseHttpContractTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeRtdb()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.fake.handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.config = validate_config(BASE)
        self.config["database_url"] = "http://127.0.0.1:%d" % self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_read_only_preflight_uses_both_identity_tokens_and_only_get(self):
        result = run_probe(self.config, send=False)
        self.assertEqual(result["state"], "PREFLIGHT_PASS")
        self.assertEqual(len(self.fake.requests), 3)
        self.assertTrue(all(method == "GET" for method, _, _ in self.fake.requests))
        self.assertIn(("GET", "/messenger/identities/AI-01.json", "secret-token-a"), self.fake.requests)
        self.assertIn(("GET", "/messenger/identities/AI-02.json", "secret-token-b"), self.fake.requests)

    def test_send_round_trip_posts_nonce_then_receiver_ack_is_verified(self):
        result = run_probe(self.config, send=True, wait_seconds=2)
        self.assertEqual(result["state"], "TEXT_ROUND_TRIP_PASS")
        self.assertEqual(result["acknowledgement"], "VERIFIED")
        methods = [item[0] for item in self.fake.requests]
        self.assertEqual(methods, ["GET", "GET", "GET", "POST", "GET", "PUT", "GET"])
        sent = self.fake.messages["-message-key"]
        self.assertEqual(sent["senderAiId"], "AI-01")
        self.assertEqual(sent["recipientAiIds"], {"AI-02": True})
        self.assertTrue(sent["body"].startswith("first-contact-"))
        self.assertIs(self.fake.acks["-message-key"], True)

    def test_tokens_are_not_in_probe_result(self):
        result = run_probe(self.config, send=True, wait_seconds=2)
        serialized = json.dumps(result)
        self.assertNotIn("secret-token-a", serialized)
        self.assertNotIn("secret-token-b", serialized)

    def test_recipient_authentication_is_used_for_message_read_and_ack_write(self):
        run_probe(self.config, send=True, wait_seconds=2)
        reads = [r for r in self.fake.requests if r[1].endswith("/messages.json")]
        ack_write = [r for r in self.fake.requests if "/acks/" in r[1] and r[0] == "PUT"]
        self.assertEqual(reads[0][2], "secret-token-b")
        self.assertEqual(ack_write[0][2], "secret-token-b")

    def test_sender_token_verifies_ack(self):
        run_probe(self.config, send=True, wait_seconds=2)
        ack_read = [r for r in self.fake.requests if "/acks/" in r[1] and r[0] == "GET"]
        self.assertEqual(len(ack_read), 1)
        self.assertEqual(ack_read[0][2], "secret-token-a")


if __name__ == "__main__":
    unittest.main()
