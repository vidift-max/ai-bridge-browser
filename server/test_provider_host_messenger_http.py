import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.ai_provider_host import AuthenticatedProviderHost
from server.agent_provider_router import AgentProviderRouter
from server.ai_conversation_host import AgentSessionRegistry, TwoAgentConversationHost
from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.rate_limit import SlidingWindowRateLimiter
from server.sqlite_store import SQLiteMessengerStore
from server.two_agent_runtime import build_two_agent_runtime


class FakeProvider:
    model = "fake-messenger-model"

    def __init__(self):
        self.calls = []

    def respond(self, prompt):
        self.calls.append(prompt)
        return {
            "responseId": "fake-response-" + str(len(self.calls)),
            "model": self.model,
            "text": "Resposta simulada: " + prompt,
        }


class ProviderHostMessengerHttpTest(unittest.TestCase):
    def setUp(self):
        self.tokens = {"user-token": "AI-USER", "peer-token": "AI-PEER"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(":memory:")
        self.backend = MessengerBackend(
            self.tokens, {"default-room": {"AI-USER", "AI-PEER"}},
            store=self.store, authenticator=self.auth,
        )
        self.backend.create_conversation(
            "user-token", "private-room", ["AI-USER", "AI-PEER"], "PRIVATE")
        self.provider = FakeProvider()
        self.peer_provider = FakeProvider()

        def authorize(principal, conversation_id, agent_id):
            members = self.backend.conversation_members().get(conversation_id, set())
            kinds = self.backend.conversation_kinds()
            return (principal == agent_id and len(members) == 2
                    and agent_id in members and kinds.get(conversation_id) == "PRIVATE")

        def resolve(agent_id):
            if agent_id not in self.tokens.values():
                return None
            provider = self.provider if agent_id == "AI-USER" else self.peer_provider
            def invoke(prompt):
                response = provider.respond(prompt)
                return {
                    "text": response["text"],
                    "providerId": "fake-test-provider-" + agent_id,
                    "model": response["model"],
                }
            return invoke

        self.host = AuthenticatedProviderHost(
            authenticate=self.backend.authenticate,
            authorize_agent=authorize,
            resolve_provider=resolve,
            attestation_key=b"m" * 32,
            server_identity="AI-BRIDGE-MESSENGER-TEST",
        )
        self.sessions = AgentSessionRegistry(self.backend, ttl_seconds=60)
        self.conversation_host = TwoAgentConversationHost(self.backend, self.host, self.sessions)
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.provider_host = self.host
        MessengerHandler.agent_session_registry = self.sessions
        MessengerHandler.conversation_host = self.conversation_host
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.backend.close()
        MessengerHandler.provider_host = None
        MessengerHandler.agent_session_registry = None
        MessengerHandler.conversation_host = None
        MessengerHandler.agent_provider_router = None
        MessengerHandler.backend = None
        MessengerHandler.authenticator = None

    def request_path(self, token, path, payload):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        connection.request("POST", path, body=json.dumps(payload), headers=headers)
        response = connection.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, data


    def request_get(self, token, path):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {}
        if token:
            headers["Authorization"] = "Bearer " + token
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, data

    def request(self, token, payload):
        return self.request_path(token, "/v1/ai/provider/respond", payload)

    def payload(self, **overrides):
        value = {
            "conversationId": "private-room",
            "agentId": "AI-USER",
            "requestId": "provider-req-001",
            "prompt": "Diga olá para a outra IA.",
        }
        value.update(overrides)
        return value

    def test_provider_reply_is_authenticated_persisted_and_delivered_to_peer(self):
        status, data = self.request("user-token", self.payload())
        self.assertEqual(status, 201)
        message = data["message"]
        self.assertEqual(message["senderAiId"], "AI-USER")
        self.assertEqual(message["recipientAiIds"], ["AI-PEER"])
        self.assertEqual(message["body"], "Resposta simulada: Diga olá para a outra IA.")
        peer_history = self.backend.history("peer-token", "private-room")
        self.assertEqual([item.message_id for item in peer_history], [message["messageId"]])
        self.assertTrue(self.host.verify_attestation(data["attestation"], message["body"]))
        self.assertEqual(self.provider.calls, ["Diga olá para a outra IA."])

    def test_missing_authentication_is_rejected_before_provider(self):
        status, data = self.request(None, self.payload())
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "authentication_required")
        self.assertEqual(self.provider.calls, [])

    def test_client_cannot_impersonate_peer_agent(self):
        status, data = self.request("user-token", self.payload(agentId="AI-PEER"))
        self.assertEqual(status, 403)
        self.assertEqual(data["error"], "agent_not_authorized_for_private_room")
        self.assertEqual(self.provider.calls, [])

    def test_group_room_is_not_eligible_for_two_agent_provider_route(self):
        self.backend.create_conversation(
            "user-token", "group-room", ["AI-USER", "AI-PEER"], "GROUP")
        status, data = self.request("user-token", self.payload(conversationId="group-room",
                                                               requestId="provider-req-002"))
        self.assertEqual(status, 403)
        self.assertEqual(self.provider.calls, [])

    def test_unknown_client_fields_are_rejected(self):
        status, data = self.request("user-token", self.payload(senderAiId="AI-PEER"))
        self.assertEqual(status, 400)
        self.assertEqual(self.provider.calls, [])

    def test_missing_host_fails_closed(self):
        MessengerHandler.provider_host = None
        status, data = self.request("user-token", self.payload())
        self.assertEqual(status, 503)
        self.assertEqual(data["error"], "provider_host_not_configured")
        self.assertEqual(self.provider.calls, [])

    def test_response_too_large_is_not_persisted(self):
        self.provider.respond = lambda prompt: {
            "text": "x" * 5001, "providerId": "fake-test-provider",
            "model": "fake-model",
        }
        status, data = self.request("user-token", self.payload(requestId="provider-req-003"))
        self.assertEqual(status, 400)
        self.assertEqual(self.backend.history("peer-token", "private-room"), [])


    def test_replayed_provider_request_is_rejected_without_second_provider_call(self):
        first_status, first = self.request("user-token", self.payload())
        second_status, second = self.request("user-token", self.payload())
        self.assertEqual(first_status, 201)
        self.assertEqual(second_status, 409)
        self.assertEqual(second["error"], "duplicate_request")
        self.assertEqual(len(self.provider.calls), 1)
        peer_history = self.backend.history("peer-token", "private-room")
        self.assertEqual(len(peer_history), 1)
        self.assertEqual(peer_history[0].message_id, first["message"]["messageId"])

    def test_provider_error_does_not_create_room_message(self):
        self.provider.respond = lambda _prompt: (_ for _ in ()).throw(
            RuntimeError("simulated_provider_failure"))
        status, data = self.request("user-token", self.payload(requestId="provider-req-004"))
        self.assertEqual(status, 502)
        self.assertEqual(self.backend.history("peer-token", "private-room"), [])


    def test_two_independent_ai_identities_complete_a_to_b_to_a_round_trip(self):
        first_status, first = self.request(
            "user-token",
            self.payload(requestId="m176-a-001",
                         prompt="IA-A: apresente-se para IA-B."),
        )
        self.assertEqual(first_status, 201)
        first_message = first["message"]
        self.assertEqual(first_message["senderAiId"], "AI-USER")
        self.assertEqual(first_message["recipientAiIds"], ["AI-PEER"])

        second_status, second = self.request(
            "peer-token",
            self.payload(agentId="AI-PEER", requestId="m176-b-001",
                         prompt=first_message["body"]),
        )
        self.assertEqual(second_status, 201)
        second_message = second["message"]
        self.assertEqual(second_message["senderAiId"], "AI-PEER")
        self.assertEqual(second_message["recipientAiIds"], ["AI-USER"])

        third_status, third = self.request(
            "user-token",
            self.payload(requestId="m176-a-002",
                         prompt=second_message["body"]),
        )
        self.assertEqual(third_status, 201)
        third_message = third["message"]
        self.assertEqual(third_message["senderAiId"], "AI-USER")
        self.assertEqual(third_message["recipientAiIds"], ["AI-PEER"])

        peer_history = self.backend.history("peer-token", "private-room")
        user_history = self.backend.history("user-token", "private-room")
        expected_history = [
            first_message["messageId"],
            second_message["messageId"],
            third_message["messageId"],
        ]
        self.assertEqual([item.message_id for item in peer_history], expected_history)
        self.assertEqual([item.message_id for item in user_history], expected_history)
        self.assertEqual(self.provider.calls, [
            "IA-A: apresente-se para IA-B.",
            second_message["body"],
        ])
        self.assertEqual(self.peer_provider.calls, [first_message["body"]])
        self.assertTrue(self.host.verify_attestation(first["attestation"],
                                                     first_message["body"]))
        self.assertTrue(self.host.verify_attestation(second["attestation"],
                                                     second_message["body"]))
        self.assertTrue(self.host.verify_attestation(third["attestation"],
                                                     third_message["body"]))


    def test_two_agent_session_registration_and_coordinated_turn_endpoint(self):
        status_a, session_a = self.request_path(
            "user-token", "/v1/ai/conversation/session/register",
            {"conversationId": "private-room"})
        status_b, session_b = self.request_path(
            "peer-token", "/v1/ai/conversation/session/register",
            {"conversationId": "private-room"})
        self.assertEqual(status_a, 201)
        self.assertEqual(status_b, 201)
        self.assertEqual(session_a["session"]["aiId"], "AI-USER")
        self.assertEqual(session_b["session"]["aiId"], "AI-PEER")

        status, result = self.request_path(
            "user-token", "/v1/ai/conversation/turn",
            {"conversationId": "private-room", "agentId": "AI-PEER",
             "requestId": "m177-http-b", "prompt": "Olá, IA parceira."})
        self.assertEqual(status, 201)
        self.assertEqual(result["message"]["senderAiId"], "AI-PEER")
        self.assertEqual(result["message"]["recipientAiIds"], ["AI-USER"])
        self.assertEqual(self.peer_provider.calls, ["Olá, IA parceira."])

        verify_status, verified = self.request_path(
            "user-token", "/v1/ai/provider/attestation/verify",
            {"conversationId": "private-room", "agentId": "AI-PEER",
             "attestation": result["attestation"],
             "responseText": result["message"]["body"]})
        self.assertEqual(verify_status, 200)
        self.assertTrue(verified["valid"])
        mismatch_status, mismatch = self.request_path(
            "user-token", "/v1/ai/provider/attestation/verify",
            {"conversationId": "private-room", "agentId": "AI-USER",
             "attestation": result["attestation"],
             "responseText": result["message"]["body"]})
        self.assertEqual(mismatch_status, 200)
        self.assertFalse(mismatch["valid"])


    def test_production_runtime_factory_completes_http_round_trip_and_persists_authorship(self):
        class Adapter:
            def __init__(self, provider_id):
                self.provider_id = provider_id
                self.calls = []
            def enabled(self): return True
            def api_calls_enabled(self): return True
            def respond(self, prompt):
                self.calls.append(prompt)
                return {"text": self.provider_id + " reply: " + prompt,
                        "providerId": self.provider_id, "model": self.provider_id + "-test"}

        openai = Adapter("openai")
        claude = Adapter("anthropic")
        runtime = build_two_agent_runtime(
            self.backend, self.tokens,
            {"openai": openai, "anthropic": claude},
            host_key_hex="6d" * 32,
            assignments={"AI-USER": "openai", "AI-PEER": "anthropic"},
        )
        MessengerHandler.provider_host = runtime.provider_host
        MessengerHandler.agent_session_registry = runtime.session_registry
        MessengerHandler.conversation_host = runtime.conversation_host
        MessengerHandler.agent_provider_router = runtime.router

        for token, expected_ai in (("user-token", "AI-USER"), ("peer-token", "AI-PEER")):
            status, data = self.request_path(
                token, "/v1/ai/conversation/session/register",
                {"conversationId": "private-room"})
            self.assertEqual(status, 201)
            self.assertEqual(data["session"]["aiId"], expected_ai)

        status_a, first = self.request_path(
            "user-token", "/v1/ai/conversation/turn",
            {"conversationId": "private-room", "agentId": "AI-PEER",
             "requestId": "m179-roundtrip-a", "prompt": "Olá, IA-B"})
        self.assertEqual(status_a, 201)
        self.assertEqual(first["message"]["senderAiId"], "AI-PEER")
        self.assertEqual(first["attestation"]["statement"]["providerId"], "anthropic")
        self.assertTrue(runtime.provider_host.verify_attestation(
            first["attestation"], first["message"]["body"]))
        first_delivery_status, first_delivery = self.request_get(
            "user-token",
            "/v1/conversations/private-room/messages/wait?after=0&limit=10&timeout=1")
        self.assertEqual(first_delivery_status, 200)
        self.assertIn(first["message"]["messageId"],
                      [item["messageId"] for item in first_delivery["messages"]])

        status_b, second = self.request_path(
            "user-token", "/v1/ai/conversation/turn",
            {"conversationId": "private-room", "agentId": "AI-USER",
             "requestId": "m179-roundtrip-b", "prompt": first["message"]["body"]})
        self.assertEqual(status_b, 201)
        self.assertEqual(second["message"]["senderAiId"], "AI-USER")
        self.assertEqual(second["attestation"]["statement"]["providerId"], "openai")
        self.assertTrue(runtime.provider_host.verify_attestation(
            second["attestation"], second["message"]["body"]))
        second_delivery_status, second_delivery = self.request_get(
            "peer-token",
            "/v1/conversations/private-room/messages/wait?after=1&limit=10&timeout=1")
        self.assertEqual(second_delivery_status, 200)
        self.assertIn(second["message"]["messageId"],
                      [item["messageId"] for item in second_delivery["messages"]])

        expected = [first["message"]["messageId"], second["message"]["messageId"]]
        self.assertEqual([m.message_id for m in self.backend.history(
            "user-token", "private-room")], expected)
        self.assertEqual([m.message_id for m in self.backend.history(
            "peer-token", "private-room")], expected)
        self.assertEqual(claude.calls, ["Olá, IA-B"])
        self.assertEqual(openai.calls, [first["message"]["body"]])

        ready_status, ready = self.request_get("user-token", "/v1/ai/provider/readiness")
        self.assertEqual(ready_status, 200)
        readiness = {item["aiId"]: item for item in ready["assignments"]}
        self.assertEqual(readiness["AI-USER"]["providerId"], "openai")
        self.assertEqual(readiness["AI-PEER"]["providerId"], "anthropic")
        self.assertTrue(readiness["AI-USER"]["apiCallsEnabled"])
        self.assertTrue(readiness["AI-PEER"]["apiCallsEnabled"])

    def test_coordinated_turn_requires_peer_to_register_first(self):
        self.request_path("user-token", "/v1/ai/conversation/session/register",
                          {"conversationId": "private-room"})
        status, result = self.request_path(
            "user-token", "/v1/ai/conversation/turn",
            {"conversationId": "private-room", "agentId": "AI-PEER",
             "requestId": "m177-http-missing", "prompt": "Olá"})
        self.assertEqual(status, 409)
        self.assertEqual(result["error"], "agent_session_not_registered")
        self.assertEqual(self.peer_provider.calls, [])

    def test_session_registration_rejects_non_private_room(self):
        self.backend.create_conversation(
            "user-token", "group-room", ["AI-USER", "AI-PEER"], "GROUP")
        status, result = self.request_path(
            "user-token", "/v1/ai/conversation/session/register",
            {"conversationId": "group-room"})
        self.assertEqual(status, 403)
        self.assertEqual(result["error"], "private_two_member_room_required")


if __name__ == "__main__":
    unittest.main()
