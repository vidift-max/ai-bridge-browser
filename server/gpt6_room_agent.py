"""GPT-6 API-backed participant for authorized collective Messenger rooms.

The assistant is a server-owned identity. Its provider credential never reaches
the browser, and no provider request is made unless the paid-API gate is enabled.
"""
from hashlib import sha256
from threading import Lock


class GPT6RoomAgent:
    ASSISTANT_ID = "AI-GPT6"

    def __init__(self, backend, adapter):
        self._backend = backend
        self._adapter = adapter
        # Serialize requests in this process so a client retry cannot race a
        # second provider call before the first assistant message is persisted.
        self._request_lock = Lock()

    @staticmethod
    def _message_view(message):
        return {
            "messageId": message.message_id,
            "conversationId": message.conversation_id,
            "senderAiId": message.sender_ai_id,
            "recipientAiIds": list(message.recipient_ai_ids),
            "body": message.body,
            "sequence": message.sequence,
        }

    def respond(self, bearer_token, conversation_id, message, client_request_id):
        if self._adapter is None:
            raise RuntimeError("openai_api_not_configured")
        if not self._adapter.api_calls_enabled():
            raise RuntimeError("openai_api_calls_disabled")
        if not self._adapter.enabled():
            raise RuntimeError("openai_api_not_configured")
        if (not isinstance(conversation_id, str) or not conversation_id.strip()
                or len(conversation_id) > self._backend.MAX_ID_LENGTH):
            raise ValueError("invalid_conversation_id")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message_required")
        if (not isinstance(client_request_id, str)
                or len(client_request_id) < 8
                or len(client_request_id) > 128
                or any(ord(char) < 33 or ord(char) > 126 for char in client_request_id)):
            raise ValueError("invalid_client_request_id")

        sender_ai_id = self._backend.authenticate(bearer_token)
        members = self._backend.conversation_members().get(conversation_id)
        if not members or sender_ai_id not in members:
            raise PermissionError("authorization_denied")
        if self.ASSISTANT_ID not in members:
            raise ValueError("gpt6_not_room_member")
        if sender_ai_id == self.ASSISTANT_ID:
            raise PermissionError("assistant_cannot_impersonate_user")

        request_digest = sha256(client_request_id.encode("ascii")).hexdigest()[:40]
        user_message_id = "gpt6-user-" + request_digest
        reply_message_id = "gpt6-reply-" + request_digest
        user_request_key = "gpt6-user:" + request_digest
        reply_request_key = "gpt6-reply:" + request_digest

        with self._request_lock:
            recipients = sorted(members - {sender_ai_id})
            user_message = self._backend.submit(
                bearer_token, user_message_id, conversation_id, recipients,
                message.strip(), user_request_key)

            # A completed retry returns the durable room reply without making
            # another provider request.
            visible_history = self._backend.history(
                bearer_token, conversation_id, before_sequence=0, limit=100)
            existing_reply = next(
                (item for item in visible_history if item.message_id == reply_message_id),
                None)
            if existing_reply is not None:
                return {
                    "userMessage": self._message_view(user_message),
                    "assistantMessage": self._message_view(existing_reply),
                    "assistant": {"id": self.ASSISTANT_ID, "displayName": "GPT-6"},
                    "model": None,
                    "responseId": None,
                    "idempotentReplay": True,
                }

            result = self._adapter.respond(user_message.body)
            answer = result.get("text") if isinstance(result, dict) else None
            if not isinstance(answer, str) or not answer.strip():
                raise RuntimeError("openai_empty_output")

            assistant_recipients = sorted(members - {self.ASSISTANT_ID})
            assistant_message = self._backend.submit_internal(
                self.ASSISTANT_ID, reply_message_id, conversation_id,
                assistant_recipients, answer.strip(), reply_request_key)
            return {
                "userMessage": self._message_view(user_message),
                "assistantMessage": self._message_view(assistant_message),
                "assistant": {"id": self.ASSISTANT_ID, "displayName": "GPT-6"},
                "model": result.get("model"),
                "responseId": result.get("responseId"),
                "idempotentReplay": False,
            }
