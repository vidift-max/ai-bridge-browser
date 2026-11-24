import json
import tempfile
import threading
import unittest
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore


class IdentityHttpTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        path = self.temp.name + "/messenger.sqlite"
        tokens = {"secret-alpha": "AI-ALPHA", "secret-bravo": "AI-BRAVO"}
        self.auth = Authenticator(tokens)
        self.store = SQLiteMessengerStore(path)
        self.backend = MessengerBackend(tokens, {"default": set(tokens.values())},
                                        self.store, authenticator=self.auth)
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.operational = None
        self.server = HTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.backend.close()
        self.temp.cleanup()

    def request(self, path, token=None):
        headers = {}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = Request(self.base + path, headers=headers)
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def post(self, path, payload, token=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = Request(self.base + path, data=json.dumps(payload).encode("utf-8"),
                          headers=headers, method="POST")
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def test_room_inbox_helper_is_served_as_javascript(self):
        with urlopen(self.base + "/ai-room-inbox.js", timeout=3) as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("AIBridgeRoomInbox", body)
            self.assertIn("mergePage", body)

    def test_room_message_actions_helper_is_served_as_javascript(self):
        with urlopen(self.base + "/ai-room-message-actions.js", timeout=3) as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("AIBridgeRoomMessageActions", body)
            self.assertIn("copyMessage", body)

    def test_room_message_search_helper_is_served_as_javascript(self):
        with urlopen(self.base + "/ai-room-message-search.js", timeout=3) as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("AIBridgeRoomMessageSearch", body)
            self.assertIn("filterMessages", body)

    def test_room_message_conversation_export_helper_is_served_as_javascript(self):
        with urlopen(self.base + "/ai-room-conversation-export.js", timeout=3) as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("AIBridgeRoomConversationExport", body)
            self.assertIn("buildExport", body)

    def test_room_creation_helper_is_served_as_javascript(self):
        with urlopen(self.base + "/ai-room-creation.js", timeout=3) as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("AIBridgeRoomCreation", body)
            self.assertIn("createConversation", body)

    def test_authenticated_group_creation_returns_room(self):
        status, result = self.post("/v1/conversations", {
            "conversationId": "team-alpha",
            "kind": "GROUP",
            "memberAiIds": ["AI-ALPHA", "AI-BRAVO"]
        }, "secret-alpha")
        self.assertEqual(status, 201)
        self.assertEqual(result["conversation"]["memberCount"], 2)
        self.assertEqual(result["conversation"]["kind"], "GROUP")

    def test_authenticated_private_creation_requires_exactly_two_members(self):
        status, result = self.post("/v1/conversations", {
            "conversationId": "private-alpha",
            "kind": "PRIVATE",
            "memberAiIds": ["AI-ALPHA", "AI-BRAVO"]
        }, "secret-alpha")
        self.assertEqual(status, 201)
        self.assertEqual(result["conversation"]["memberCount"], 2)
        self.assertEqual(result["conversation"]["kind"], "PRIVATE")

    def test_private_creation_rejects_more_than_two_members(self):
        tokens = {"secret-alpha": "AI-ALPHA", "secret-bravo": "AI-BRAVO",
                  "secret-charlie": "AI-CHARLIE"}
        self.auth = Authenticator(tokens)
        self.backend.close()
        self.store = SQLiteMessengerStore(self.temp.name + "/private.sqlite")
        self.backend = MessengerBackend(tokens, {"default": set(tokens.values())},
                                        self.store, authenticator=self.auth)
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        status, result = self.post("/v1/conversations", {
            "conversationId": "private-invalid",
            "kind": "PRIVATE",
            "memberAiIds": ["AI-ALPHA", "AI-BRAVO", "AI-CHARLIE"]
        }, "secret-alpha")
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "invalid_conversation")

    def test_conversation_creation_requires_authentication(self):
        status, result = self.post("/v1/conversations", {
            "conversationId": "private-alpha",
            "kind": "PRIVATE",
            "memberAiIds": ["AI-ALPHA", "AI-BRAVO"]
        })
        self.assertEqual(status, 401)
        self.assertEqual(result["error"], "authentication_required")

    def test_conversation_creation_rejects_unknown_ai(self):
        status, result = self.post("/v1/conversations", {
            "conversationId": "team-unknown",
            "kind": "GROUP",
            "memberAiIds": ["AI-ALPHA", "AI-UNKNOWN"]
        }, "secret-alpha")
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "invalid_conversation")

    def test_legacy_phone_self_registration_is_disabled(self):
        status, result = self.request("/v1/me/phone", "secret-alpha")
        self.assertEqual(status, 404)
        self.assertEqual(result["error"], "not_found")

    def test_legacy_phone_lookup_is_disabled(self):
        status, result = self.request("/v1/phones/AI-PHONE-000001", "secret-bravo")
        self.assertEqual(status, 404)
        self.assertEqual(result["error"], "not_found")

    def test_legacy_phone_route_does_not_require_or_accept_identity(self):
        status, result = self.request("/v1/me/phone")
        self.assertEqual(status, 404)
        self.assertEqual(result["error"], "not_found")

    def test_authenticated_internal_identity_contains_only_ai_id(self):
        status, result = self.request("/v1/me/identity", "secret-alpha")
        self.assertEqual(status, 200)
        self.assertEqual(result["identity"], {"aiId": "AI-ALPHA"})
        self.assertNotIn("phone", result)
        self.assertNotIn("displayNumber", result)

    def test_internal_identity_requires_authentication(self):
        status, result = self.request("/v1/me/identity")
        self.assertEqual(status, 401)
        self.assertEqual(result["error"], "authentication_required")



    def test_conversation_history_endpoint_returns_acknowledged_messages(self):
        message = self.backend.submit("secret-alpha", "http-history-1", "default",
                                      ["AI-BRAVO"], "history body", "http-history-req")
        self.backend.acknowledge("secret-bravo", message.message_id)
        status, result = self.request("/v1/conversations/default/history?before=0&limit=10",
                                      "secret-bravo")
        self.assertEqual(status, 200)
        self.assertEqual([item["messageId"] for item in result["messages"]],
                         [message.message_id])
        self.assertEqual(result["messages"][0]["body"], "history body")
        self.assertEqual(self.backend.pending("secret-bravo", "default"), [])

    def test_conversation_history_endpoint_rejects_non_members_and_bad_query(self):
        status, result = self.request("/v1/conversations/default/history", "unknown-token")
        self.assertEqual(status, 401)
        status, result = self.request("/v1/conversations/default/history?before=-1",
                                      "secret-bravo")
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "invalid_history_query")


    def test_conversation_list_returns_server_authoritative_preview_and_unread_count(self):
        self.backend.submit("secret-alpha", "inbox-http-1", "default",
                            ["AI-BRAVO"], "mensagem pendente", "inbox-http-req-1")
        status, result = self.request("/v1/conversations?limit=100&after=", "secret-bravo")
        self.assertEqual(status, 200)
        room = next(item for item in result["conversations"]
                    if item["conversationId"] == "default")
        self.assertEqual(room["unreadCount"], 1)
        self.assertEqual(room["lastMessage"]["messageId"], "inbox-http-1")
        self.assertEqual(room["lastMessage"]["body"], "mensagem pendente")

        self.backend.acknowledge("secret-bravo", "inbox-http-1")
        status, refreshed = self.request("/v1/conversations?limit=100&after=", "secret-bravo")
        self.assertEqual(status, 200)
        room = next(item for item in refreshed["conversations"]
                    if item["conversationId"] == "default")
        self.assertEqual(room["unreadCount"], 0)

    def test_conversation_list_requires_authentication_for_previews(self):
        status, result = self.request("/v1/conversations?limit=100&after=")
        self.assertEqual(status, 401)

if __name__ == "__main__":
    unittest.main()
