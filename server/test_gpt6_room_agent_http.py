import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.auth import Authenticator
from server.gpt6_room_agent import GPT6RoomAgent
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.rate_limit import SlidingWindowRateLimiter
from server.sqlite_store import SQLiteMessengerStore


class FakeAdapter:
    def enabled(self):
        return True

    def api_calls_enabled(self):
        return True

    def respond(self, text):
        return {"responseId": "resp-http-test", "model": "mock-model",
                "text": "GPT-6 recebeu: " + text}


class GPT6RoomAgentHttpTest(unittest.TestCase):
    def setUp(self):
        self.tokens = {"user-token": "AI-USER", "peer-token": "AI-PEER"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(":memory:")
        self.backend = MessengerBackend(
            self.tokens,
            {"shared-room": {"AI-USER", "AI-PEER", "AI-GPT6"}},
            store=self.store,
            authenticator=self.auth,
            identity_display_names={"AI-GPT6": "GPT-6"},
            internal_ai_ids={"AI-GPT6"},
        )
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter()
        MessengerHandler.gpt6_room_agent = GPT6RoomAgent(self.backend, FakeAdapter())
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.backend.close()
        MessengerHandler.gpt6_room_agent = None
        MessengerHandler.backend = None
        MessengerHandler.authenticator = None

    def request(self, token, payload):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        connection.request("POST", "/v1/gpt6/room/respond",
                           body=json.dumps(payload), headers=headers)
        response = connection.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, data

    def test_authenticated_request_persists_user_and_gpt6_messages_in_same_room(self):
        status, data = self.request("user-token", {
            "conversationId": "shared-room",
            "message": "Estamos juntos na sala?",
            "clientRequestId": "http-request-001",
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["userMessage"]["senderAiId"], "AI-USER")
        self.assertEqual(data["assistantMessage"]["senderAiId"], "AI-GPT6")
        self.assertEqual(data["assistantMessage"]["body"],
                         "GPT-6 recebeu: Estamos juntos na sala?")
        peer_history = self.backend.history("peer-token", "shared-room")
        self.assertEqual([item.sender_ai_id for item in peer_history],
                         ["AI-USER", "AI-GPT6"])

    def test_unauthenticated_request_is_rejected(self):
        status, data = self.request(None, {
            "conversationId": "shared-room",
            "message": "Olá",
            "clientRequestId": "http-request-002",
        })
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "authentication_required")

    def test_request_rejects_extra_fields(self):
        status, data = self.request("user-token", {
            "conversationId": "shared-room",
            "message": "Olá",
            "clientRequestId": "http-request-003",
            "provider": "untrusted",
        })
        self.assertEqual(status, 400)
        self.assertEqual(data["error"], "invalid_gpt6_room_request")

    def test_primary_room_gpt6_asset_is_served_with_safe_headers(self):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request("GET", "/ai-room-gpt6.js")
        response = connection.getresponse()
        body = response.read().decode("utf-8")
        headers = dict(response.getheaders())
        connection.close()
        self.assertEqual(response.status, 200)
        self.assertIn("AIBridgeRoomGPT6", body)
        self.assertEqual(headers.get("Content-Type"), "text/javascript; charset=utf-8")
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")


if __name__ == "__main__":
    unittest.main()
