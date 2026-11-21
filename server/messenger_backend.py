from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

@dataclass(frozen=True)
class Message:
    message_id: str
    conversation_id: str
    sender_ai_id: str
    recipient_ai_ids: Tuple[str, ...]
    body: str
    client_request_id: str
    sequence: int
    acknowledged_by: Set[str]

class MessengerBackend:
    """Small in-memory backend; authentication is delegated to opaque token lookup."""
    def __init__(self, tokens: Dict[str, str], conversations: Dict[str, Set[str]]):
        self._tokens = dict(tokens)
        self._conversations = {k: set(v) for k, v in conversations.items()}
        self._messages: Dict[str, Message] = {}
        self._idempotency: Dict[Tuple[str, str], str] = {}
        self._next_sequence: Dict[str, int] = {}

    def authenticate(self, bearer_token: str) -> str:
        if not bearer_token or bearer_token not in self._tokens:
            raise PermissionError("authentication_required")
        return self._tokens[bearer_token]

    def submit(self, bearer_token: str, message_id: str, conversation_id: str,
               recipient_ai_ids: List[str], body: str, client_request_id: str) -> Message:
        sender = self.authenticate(bearer_token)
        members = self._conversations.get(conversation_id)
        if not members or sender not in members or not set(recipient_ai_ids).issubset(members):
            raise PermissionError("authorization_denied")
        if not message_id or not body or not client_request_id:
            raise ValueError("invalid_message")
        key = (sender, client_request_id)
        existing_id = self._idempotency.get(key)
        if existing_id:
            existing = self._messages[existing_id]
            same = (existing.message_id, existing.conversation_id, existing.body, existing.recipient_ai_ids) == (message_id, conversation_id, body, tuple(recipient_ai_ids))
            if same:
                return existing
            raise ValueError("idempotency_conflict")
        sequence = self._next_sequence.get(conversation_id, 0) + 1
        message = Message(message_id, conversation_id, sender, tuple(recipient_ai_ids), body, client_request_id, sequence, set())
        self._messages[message_id] = message
        self._idempotency[key] = message_id
        self._next_sequence[conversation_id] = sequence
        return message

    def pending(self, bearer_token: str, conversation_id: str) -> List[Message]:
        ai_id = self.authenticate(bearer_token)
        members = self._conversations.get(conversation_id)
        if not members or ai_id not in members:
            raise PermissionError("authorization_denied")
        return [m for m in self._messages.values() if m.conversation_id == conversation_id and ai_id in m.recipient_ai_ids and ai_id not in m.acknowledged_by]

    def acknowledge(self, bearer_token: str, message_id: str) -> Message:
        ai_id = self.authenticate(bearer_token)
        message = self._messages.get(message_id)
        if message is None or ai_id not in message.recipient_ai_ids:
            raise PermissionError("authorization_denied")
        message.acknowledged_by.add(ai_id)
        return message
