import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from server.ai_provider_host import AuthenticatedProviderHost
from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.rate_limit import SlidingWindowRateLimiter
from server.sqlite_store import SQLiteMessengerStore
from server.provider_request_lease import ProviderRequestLeaseKeeper


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

        def authorize(principal, conversation_id, agent_id):
            members = self.backend.conversation_members().get(conversation_id, set())
            kinds = self.backend.conversation_kinds()
            return (principal == agent_id and len(members) == 2
                    and agent_id in members and kinds.get(conversation_id) == "PRIVATE")

        def resolve(agent_id):
            if agent_id not in self.tokens.values():
                return None
            def invoke(prompt):
                response = self.provider.respond(prompt)
                return {
                    "text": response["text"],
                    "providerId": "fake-test-provider",
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
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.provider_host = self.host
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
        MessengerHandler.backend = None
        MessengerHandler.authenticator = None

    def request(self, token, payload):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        connection.request("POST", "/v1/ai/provider/respond",
                           body=json.dumps(payload), headers=headers)
        response = connection.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, data

    def payload(self, **overrides):
        value = {
            "conversationId": "private-room",
            "agentId": "AI-USER",
            "requestId": "provider-req-001",
            "prompt": "Diga olá para a outra IA.",
        }
        value.update(overrides)
        return value

    def test_provider_lease_keeper_marks_lost_claim(self):
        renewed = threading.Event()

        def reject_renewal():
            renewed.set()
            return False

        with ProviderRequestLeaseKeeper(reject_renewal, interval_seconds=0.01) as keeper:
            self.assertTrue(renewed.wait(1.0))
        self.assertTrue(keeper.lost)

    def test_provider_lease_keeper_stops_without_losing_live_claim(self):
        calls = []

        def renew():
            calls.append(True)
            return True

        with ProviderRequestLeaseKeeper(renew, interval_seconds=10.0) as keeper:
            self.assertFalse(keeper.lost)
        self.assertFalse(keeper.lost)
        self.assertEqual(calls, [])

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

    def test_attestation_is_bound_to_request_identity_and_response(self):
        status, data = self.request("user-token", self.payload())
        self.assertEqual(status, 201)
        statement = data["attestation"]["statement"]
        expected = {
            "conversationId": "private-room",
            "agentId": "AI-USER",
            "requestId": "provider-req-001",
            "principal": "AI-USER",
            "serverIdentity": "AI-BRIDGE-MESSENGER-TEST",
            "providerId": "fake-test-provider",
            "model": "fake-messenger-model",
        }
        self.assertTrue(self.host.verify_attestation(
            data["attestation"], data["message"]["body"], expected=expected))
        tampered = dict(data["attestation"])
        tampered["statement"] = dict(statement, requestId="other-request")
        self.assertFalse(self.host.verify_attestation(
            tampered, data["message"]["body"], expected=expected))
        self.assertFalse(self.host.verify_attestation(
            data["attestation"], data["message"]["body"] + " alterado", expected=expected))

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


    def test_replayed_provider_request_returns_durable_cached_response(self):
        first_status, first = self.request("user-token", self.payload())
        second_status, second = self.request("user-token", self.payload())
        self.assertEqual(first_status, 201)
        self.assertEqual(second_status, 200)
        self.assertTrue(second["idempotentReplay"])
        self.assertEqual(second["message"]["messageId"], first["message"]["messageId"])
        self.assertEqual(second["attestation"], first["attestation"])
        self.assertEqual(len(self.provider.calls), 1)
        peer_history = self.backend.history("peer-token", "private-room")
        self.assertEqual(len(peer_history), 1)

    def test_replay_survives_provider_host_instance_loss(self):
        first_status, first = self.request("user-token", self.payload())
        self.assertEqual(first_status, 201)
        old_host = self.host
        self.host = AuthenticatedProviderHost(
            authenticate=self.backend.authenticate,
            authorize_agent=old_host._authorize_agent,
            resolve_provider=old_host._resolve_provider,
            attestation_key=b"m" * 32,
            server_identity="AI-BRIDGE-MESSENGER-TEST",
        )
        MessengerHandler.provider_host = self.host
        second_status, second = self.request("user-token", self.payload())
        self.assertEqual(second_status, 200)
        self.assertTrue(second["idempotentReplay"])
        self.assertEqual(second["message"]["messageId"], first["message"]["messageId"])
        self.assertEqual(len(self.provider.calls), 1)

    def test_durable_attestation_tampering_fails_closed_on_replay(self):
        first_status, first = self.request("user-token", self.payload())
        self.assertEqual(first_status, 201)
        self.store.connection.execute(
            "UPDATE provider_request_records SET response_text=? WHERE principal_ai_id=? AND request_id=?",
            ("tampered", "AI-USER", "provider-req-001"))
        self.store.connection.commit()
        second_status, second = self.request("user-token", self.payload())
        self.assertEqual(second_status, 500)
        self.assertEqual(second["error"], "provider_attestation_integrity_failure")

    def test_payload_change_for_existing_request_is_conflict(self):
        first_status, _ = self.request("user-token", self.payload())
        second_status, second = self.request("user-token", self.payload(prompt="texto diferente"))
        self.assertEqual(first_status, 201)
        self.assertEqual(second_status, 409)
        self.assertEqual(second["error"], "provider_request_payload_conflict")
        self.assertEqual(len(self.provider.calls), 1)

    def test_provider_error_does_not_create_room_message(self):
        self.provider.respond = lambda _prompt: (_ for _ in ()).throw(
            RuntimeError("simulated_provider_failure"))
        status, data = self.request("user-token", self.payload(requestId="provider-req-004"))
        self.assertEqual(status, 502)
        self.assertEqual(self.backend.history("peer-token", "private-room"), [])


if __name__ == "__main__":
    unittest.main()
