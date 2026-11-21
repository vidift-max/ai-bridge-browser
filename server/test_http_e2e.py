import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore


class HttpE2ETest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        self.tokens = {"token-a": "AI-A", "token-b": "AI-B"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(self.tmp.name)
        self.backend = MessengerBackend(self.tokens, {"room": {"AI-A", "AI-B"}}, self.store, authenticator=self.auth)
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
        self.backend.close()

    def request(self, method, path, token, payload=None):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        body = None
        headers = {"Authorization": "Bearer " + token}
        if payload is not None:
            body = json.dumps(payload)
            headers["Content-Type"] = "application/json"
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()
        return response.status, data

    def test_two_principal_http_flow(self):
        status, sent = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-http-1", "conversationId": "room",
            "recipientAiIds": ["AI-B"], "body": "hello over local HTTP",
            "clientRequestId": "req-http-1"})
        self.assertEqual(status, 200); self.assertEqual(sent["senderAiId"], "AI-A")

        status, pending = self.request("GET", "/v1/conversations/room/messages", "token-b")
        self.assertEqual(status, 200); self.assertEqual(pending["principalAiId"], "AI-B")
        self.assertEqual(pending["messages"][0]["messageId"], "m-http-1")

        status, ack = self.request("POST", "/v1/messages/m-http-1/ack", "token-b")
        self.assertEqual(status, 200); self.assertEqual(ack["state"], "ACKNOWLEDGED")

    def test_old_credential_is_rejected_after_rotation(self):
        self.auth.rotate("token-a", "token-a-2")
        status, _ = self.request("POST", "/v1/messages", "token-a", {
            "messageId": "m-http-2", "conversationId": "room", "recipientAiIds": ["AI-B"],
            "body": "must fail", "clientRequestId": "req-http-2"})
        self.assertEqual(status, 401)


if __name__ == "__main__":
    unittest.main()
