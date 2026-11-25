import unittest

from server.ai_provider_host import AuthenticatedProviderHost, ProviderHostError


class AuthenticatedProviderHostTest(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.host = AuthenticatedProviderHost(
            authenticate=lambda token: {"good-token": "AI-ALPHA", "peer-token": "AI-BETA"}.get(token),
            authorize_agent=lambda principal, room, agent: (
                room == "private-1" and
                (principal == "AI-ALPHA" and agent == "AI-ALPHA" or
                 principal == "AI-BETA" and agent == "AI-BETA")
            ),
            resolve_provider=lambda agent: lambda prompt: (
                self.calls.append((agent, prompt)) or
                {"text": "Resposta de " + agent, "providerId": "local-test",
                 "model": "fake-v1"}
            ),
            attestation_key=b"k" * 32,
            clock=lambda: 1800000000,
        )
        self.request = {
            "conversationId": "private-1",
            "agentId": "AI-ALPHA",
            "requestId": "req-001",
            "prompt": "Olá, IA.",
        }

    def test_verify_attestation_accepts_expected_context_and_rejects_mismatch(self):
        result = self.host.execute("good-token", self.request)
        statement = result["attestation"]["statement"]
        expected = {key: statement[key] for key in (
            "conversationId", "agentId", "requestId", "principal",
            "serverIdentity", "providerId", "model",
        )}
        self.assertTrue(self.host.verify_attestation(result["attestation"], result["text"], expected=expected))
        expected["requestId"] = "wrong"
        self.assertFalse(self.host.verify_attestation(result["attestation"], result["text"], expected=expected))

    def test_missing_bearer_is_rejected_before_provider(self):
        with self.assertRaisesRegex(ProviderHostError, "authentication_required") as error:
            self.host.execute(None, self.request)
        self.assertEqual(error.exception.status, 401)
        self.assertEqual(self.calls, [])

    def test_invalid_token_is_rejected(self):
        with self.assertRaisesRegex(ProviderHostError, "authentication_failed"):
            self.host.execute("invalid", self.request)
        self.assertEqual(self.calls, [])

    def test_authenticated_agent_can_only_invoke_own_identity(self):
        with self.assertRaisesRegex(ProviderHostError, "agent_not_authorized_for_private_room"):
            self.host.execute("peer-token", self.request)
        self.assertEqual(self.calls, [])

    def test_server_resolves_provider_and_returns_signed_attestation(self):
        result = self.host.execute("good-token", self.request)
        self.assertEqual(self.calls, [("AI-ALPHA", "Olá, IA.")])
        self.assertEqual(result["text"], "Resposta de AI-ALPHA")
        self.assertTrue(self.host.verify_attestation(result["attestation"], result["text"]))
        statement = result["attestation"]["statement"]
        self.assertEqual(statement["principal"], "AI-ALPHA")
        self.assertEqual(statement["agentId"], "AI-ALPHA")
        self.assertEqual(statement["conversationId"], "private-1")
        self.assertEqual(statement["serverIdentity"], "AI-BRIDGE-HOST")

    def test_response_body_is_cryptographically_bound(self):
        result = self.host.execute("good-token", self.request)
        self.assertFalse(self.host.verify_attestation(result["attestation"], "alterado"))

    def test_attestation_statement_tampering_is_rejected(self):
        result = self.host.execute("good-token", self.request)
        altered = dict(result["attestation"])
        altered["statement"] = dict(altered["statement"], agentId="AI-BETA")
        self.assertFalse(self.host.verify_attestation(altered, result["text"]))

    def test_replayed_request_id_is_rejected(self):
        self.host.execute("good-token", self.request)
        with self.assertRaisesRegex(ProviderHostError, "duplicate_request") as error:
            self.host.execute("good-token", self.request)
        self.assertEqual(error.exception.status, 409)
        self.assertEqual(len(self.calls), 1)

    def test_replay_guard_expires_and_allows_new_attempt(self):
        now = [100.0]
        host = AuthenticatedProviderHost(
            authenticate=lambda token: "AI-ALPHA" if token == "good-token" else None,
            authorize_agent=lambda *_args: True,
            resolve_provider=lambda _agent: lambda _prompt: {"text": "ok", "providerId": "fake", "model": "v1"},
            attestation_key=b"r" * 32,
            clock=lambda: now[0],
            replay_ttl_seconds=10,
        )
        host.execute("good-token", self.request)
        with self.assertRaisesRegex(ProviderHostError, "duplicate_request"):
            host.execute("good-token", self.request)
        now[0] = 110.0
        result = host.execute("good-token", self.request)
        self.assertEqual(result["text"], "ok")

    def test_replay_capacity_ignores_expired_entries(self):
        now = [100.0]
        host = AuthenticatedProviderHost(
            authenticate=lambda _token: "AI-ALPHA",
            authorize_agent=lambda *_args: True,
            resolve_provider=lambda _agent: lambda _prompt: {"text": "ok", "providerId": "fake", "model": "v1"},
            attestation_key=b"c" * 32,
            clock=lambda: now[0],
            max_requests=1,
            replay_ttl_seconds=5,
        )
        host.execute("good-token", self.request)
        other = dict(self.request, requestId="req-002")
        with self.assertRaisesRegex(ProviderHostError, "host_capacity_reached"):
            host.execute("good-token", other)
        now[0] = 105.0
        host.execute("good-token", other)

    def test_extra_client_fields_are_rejected(self):
        request = dict(self.request, senderAiId="AI-BETA")
        with self.assertRaisesRegex(ProviderHostError, "invalid_provider_host_request"):
            self.host.execute("good-token", request)

    def test_oversized_prompt_is_rejected(self):
        request = dict(self.request, prompt="x" * 5001)
        with self.assertRaisesRegex(ProviderHostError, "prompt_too_large"):
            self.host.execute("good-token", request)
        self.assertEqual(self.calls, [])

    def test_unavailable_provider_fails_closed(self):
        host = AuthenticatedProviderHost(
            authenticate=lambda _token: "AI-ALPHA",
            authorize_agent=lambda *_args: True,
            resolve_provider=lambda _agent: None,
            attestation_key=b"z" * 32,
        )
        with self.assertRaisesRegex(ProviderHostError, "provider_unavailable") as error:
            host.execute("token", self.request)
        self.assertEqual(error.exception.status, 503)

    def test_invalid_replay_configuration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "max_requests_must_be_positive"):
            AuthenticatedProviderHost(
                authenticate=lambda _token: "AI-ALPHA",
                authorize_agent=lambda *_args: True,
                resolve_provider=lambda _agent: None,
                attestation_key=b"x" * 32,
                max_requests=0,
            )
        with self.assertRaisesRegex(ValueError, "replay_ttl_seconds_must_be_positive"):
            AuthenticatedProviderHost(
                authenticate=lambda _token: "AI-ALPHA",
                authorize_agent=lambda *_args: True,
                resolve_provider=lambda _agent: None,
                attestation_key=b"x" * 32,
                replay_ttl_seconds=0,
            )

    def test_short_attestation_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "attestation_key_must_be_at_least_32_bytes"):
            AuthenticatedProviderHost(
                authenticate=lambda _token: "AI-ALPHA",
                authorize_agent=lambda *_args: True,
                resolve_provider=lambda _agent: None,
                attestation_key=b"short",
            )


if __name__ == "__main__":
    unittest.main()
