"""Server-owned provider host contract for two-agent private conversations.

This module is deliberately transport/provider-neutral. It never accepts an
AI identity from an unauthenticated browser field and never reads browser
cookies or private web sessions.
"""
import hashlib
import hmac
import json
import re
import threading
import time


class ProviderHostError(Exception):
    def __init__(self, code, status=400):
        super().__init__(code)
        self.code = code
        self.status = status


class AuthenticatedProviderHost:
    REQUIRED_FIELDS = {"conversationId", "agentId", "requestId", "prompt"}
    MAX_PROMPT_CHARS = 5000
    MAX_REQUEST_ID_CHARS = 128

    def __init__(self, *, authenticate, authorize_agent, resolve_provider,
                 attestation_key, server_identity="AI-BRIDGE-HOST",
                 clock=None, max_requests=10000):
        if not callable(authenticate) or not callable(authorize_agent):
            raise ValueError("authentication_and_authorization_required")
        if not callable(resolve_provider):
            raise ValueError("provider_resolver_required")
        if not isinstance(attestation_key, bytes) or len(attestation_key) < 32:
            raise ValueError("attestation_key_must_be_at_least_32_bytes")
        if not isinstance(server_identity, str) or not server_identity.strip():
            raise ValueError("server_identity_required")
        self._authenticate = authenticate
        self._authorize_agent = authorize_agent
        self._resolve_provider = resolve_provider
        self._key = attestation_key
        self.server_identity = server_identity
        self._clock = clock or time.time
        self._max_requests = max_requests
        self._seen = set()
        self._lock = threading.Lock()

    @staticmethod
    def _canonical(payload):
        return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8")

    def _validate(self, request):
        if not isinstance(request, dict) or set(request) != self.REQUIRED_FIELDS:
            raise ProviderHostError("invalid_provider_host_request")
        for field in ("conversationId", "agentId", "requestId", "prompt"):
            value = request[field]
            if not isinstance(value, str) or not value.strip():
                raise ProviderHostError("invalid_" + field)
        if len(request["conversationId"]) > 128 or len(request["agentId"]) > 128:
            raise ProviderHostError("identity_field_too_large")
        if len(request["requestId"]) > self.MAX_REQUEST_ID_CHARS:
            raise ProviderHostError("request_id_too_large")
        if not re.fullmatch(r"[A-Za-z0-9._:-]+", request["requestId"]):
            raise ProviderHostError("invalid_request_id")
        if len(request["prompt"]) > self.MAX_PROMPT_CHARS:
            raise ProviderHostError("prompt_too_large")
        return {key: request[key] for key in sorted(self.REQUIRED_FIELDS)}

    def execute(self, bearer_token, request, *, skip_replay_guard=False):
        if not isinstance(bearer_token, str) or not bearer_token.strip():
            raise ProviderHostError("authentication_required", 401)
        validated = self._validate(request)
        try:
            principal = self._authenticate(bearer_token)
        except Exception as exc:
            raise ProviderHostError("authentication_failed", 401) from exc
        if not principal:
            raise ProviderHostError("authentication_failed", 401)
        try:
            allowed = self._authorize_agent(
                principal, validated["conversationId"], validated["agentId"])
        except Exception as exc:
            raise ProviderHostError("authorization_failed", 403) from exc
        if not allowed:
            raise ProviderHostError("agent_not_authorized_for_private_room", 403)

        if not skip_replay_guard:
            replay_key = (str(principal), validated["requestId"])
            with self._lock:
                if replay_key in self._seen:
                    raise ProviderHostError("duplicate_request", 409)
                if len(self._seen) >= self._max_requests:
                    raise ProviderHostError("host_capacity_reached", 429)
                self._seen.add(replay_key)

        try:
            provider = self._resolve_provider(validated["agentId"])
            if not callable(provider):
                raise ProviderHostError("provider_unavailable", 503)
            result = provider(validated["prompt"])
            if not isinstance(result, dict) or set(result) != {"text", "providerId", "model"}:
                raise ProviderHostError("invalid_provider_response", 502)
            text = result["text"]
            if not isinstance(text, str) or not text.strip() or len(text) > 20000:
                raise ProviderHostError("invalid_provider_text", 502)
            for field in ("providerId", "model"):
                if not isinstance(result[field], str) or not result[field].strip():
                    raise ProviderHostError("invalid_provider_metadata", 502)
        except ProviderHostError:
            raise
        except Exception as exc:
            raise ProviderHostError("provider_execution_failed", 502) from exc

        issued_at = int(self._clock())
        statement = {
            "conversationId": validated["conversationId"],
            "agentId": validated["agentId"],
            "requestId": validated["requestId"],
            "principal": str(principal),
            "serverIdentity": self.server_identity,
            "providerId": result["providerId"],
            "model": result["model"],
            "responseSha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "issuedAt": issued_at,
        }
        signature = hmac.new(self._key, self._canonical(statement),
                              hashlib.sha256).hexdigest()
        return {
            "text": text,
            "attestation": {"statement": statement, "signature": signature,
                            "algorithm": "HMAC-SHA256"},
        }

    def verify_attestation(self, attestation, response_text):
        if not isinstance(attestation, dict) or set(attestation) != {
                "statement", "signature", "algorithm"}:
            return False
        statement = attestation["statement"]
        signature = attestation["signature"]
        if not isinstance(statement, dict) or not isinstance(signature, str):
            return False
        if attestation["algorithm"] != "HMAC-SHA256":
            return False
        if not isinstance(response_text, str):
            return False
        expected_digest = hashlib.sha256(response_text.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(statement.get("responseSha256", ""), expected_digest):
            return False
        expected = hmac.new(self._key, self._canonical(statement),
                            hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
