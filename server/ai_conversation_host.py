"""In-memory session bridge for explicit two-agent provider orchestration.

Each participant registers their own already-authenticated Messenger session.
Tokens stay in process memory, are never returned to the browser, and expire.
This is a first integration bridge, not a production session vault.
"""
import hashlib
import threading
import time


class AgentSessionError(Exception):
    def __init__(self, code, status=400):
        super().__init__(code)
        self.code = code
        self.status = status


class AgentSessionRegistry:
    def __init__(self, backend, *, clock=None, ttl_seconds=1800, max_sessions=200):
        if not callable(getattr(backend, "authenticate", None)):
            raise ValueError("session_backend_required")
        if not callable(getattr(backend, "conversation_members", None)):
            raise ValueError("session_membership_required")
        if not isinstance(ttl_seconds, int) or ttl_seconds < 60 or ttl_seconds > 86400:
            raise ValueError("invalid_session_ttl")
        if not isinstance(max_sessions, int) or max_sessions < 2:
            raise ValueError("invalid_session_capacity")
        self._backend = backend
        self._clock = clock or time.time
        self._ttl = ttl_seconds
        self._max = max_sessions
        self._sessions = {}
        self._lock = threading.RLock()

    def _room_member(self, conversation_id, ai_id):
        members = self._backend.conversation_members().get(conversation_id, set())
        kinds = self._backend.conversation_kinds()
        if len(members) != 2 or ai_id not in members or kinds.get(conversation_id) != "PRIVATE":
            raise AgentSessionError("private_two_member_room_required", 403)

    def _purge(self):
        now = self._clock()
        expired = [key for key, item in self._sessions.items()
                   if item["expiresAt"] <= now]
        for key in expired:
            self._sessions.pop(key, None)

    def register(self, bearer_token, conversation_id):
        if not isinstance(bearer_token, str) or not bearer_token.strip():
            raise AgentSessionError("authentication_required", 401)
        if not isinstance(conversation_id, str) or not conversation_id.strip() or len(conversation_id) > 128:
            raise AgentSessionError("invalid_conversation_id")
        try:
            ai_id = self._backend.authenticate(bearer_token)
        except Exception as exc:
            raise AgentSessionError("authentication_failed", 401) from exc
        self._room_member(conversation_id, ai_id)
        key = (conversation_id, ai_id)
        with self._lock:
            self._purge()
            if key not in self._sessions and len(self._sessions) >= self._max:
                raise AgentSessionError("session_registry_full", 429)
            expires_at = self._clock() + self._ttl
            self._sessions[key] = {
                "token": bearer_token,
                "expiresAt": expires_at,
                "tokenFingerprint": hashlib.sha256(bearer_token.encode("utf-8")).hexdigest()[:16],
            }
        return {"conversationId": conversation_id, "aiId": ai_id,
                "expiresAt": expires_at, "ttlSeconds": self._ttl}

    def resolve(self, conversation_id, ai_id):
        self._room_member(conversation_id, ai_id)
        with self._lock:
            self._purge()
            item = self._sessions.get((conversation_id, ai_id))
            if item is None:
                raise AgentSessionError("agent_session_not_registered", 409)
            return item["token"]

    def revoke(self, conversation_id, ai_id):
        with self._lock:
            return self._sessions.pop((conversation_id, ai_id), None) is not None


class TwoAgentConversationHost:
    def __init__(self, backend, provider_host, session_registry):
        if not callable(getattr(backend, "authenticate", None)):
            raise ValueError("conversation_backend_required")
        if not callable(getattr(provider_host, "execute", None)):
            raise ValueError("provider_host_required")
        if not callable(getattr(session_registry, "resolve", None)):
            raise ValueError("agent_session_registry_required")
        self._backend = backend
        self._provider_host = provider_host
        self._sessions = session_registry

    def respond(self, requester_token, request):
        if not isinstance(request, dict) or set(request) != {
                "conversationId", "agentId", "requestId", "prompt"}:
            raise AgentSessionError("invalid_conversation_turn")
        conversation_id = request["conversationId"]
        target_ai_id = request["agentId"]
        try:
            requester_ai_id = self._backend.authenticate(requester_token)
        except Exception as exc:
            raise AgentSessionError("authentication_failed", 401) from exc
        members = self._backend.conversation_members().get(conversation_id, set())
        kinds = self._backend.conversation_kinds()
        if (len(members) != 2 or requester_ai_id not in members
                or target_ai_id not in members or kinds.get(conversation_id) != "PRIVATE"):
            raise AgentSessionError("private_two_member_room_required", 403)

        target_token = self._sessions.resolve(conversation_id, target_ai_id)
        provider_request = {
            "conversationId": conversation_id,
            "agentId": target_ai_id,
            "requestId": request["requestId"],
            "prompt": request["prompt"],
        }
        result = self._provider_host.execute(target_token, provider_request)
        recipients = sorted(members - {target_ai_id})
        digest = hashlib.sha256(
            (conversation_id + ":" + target_ai_id + ":" + request["requestId"]).encode("utf-8")
        ).hexdigest()[:40]
        message = self._backend.submit(
            target_token,
            "ai-turn-" + digest,
            conversation_id,
            recipients,
            result["text"],
            "ai-turn:" + target_ai_id + ":" + request["requestId"],
        )
        return {
            "message": {
                "messageId": message.message_id,
                "conversationId": message.conversation_id,
                "senderAiId": message.sender_ai_id,
                "recipientAiIds": list(message.recipient_ai_ids),
                "sequence": message.sequence,
                "body": message.body,
            },
            "attestation": result["attestation"],
        }
