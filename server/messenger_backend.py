from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
from server.auth import Authenticator
from server.sqlite_store import SQLiteMessengerStore

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
    MAX_BODY_LENGTH = 5000
    MAX_ID_LENGTH = 200
    MAX_ROOM_MEMBERS = 20

    def __init__(self, tokens: Dict[str, str], conversations: Dict[str, Set[str]], store=None, authenticator=None):
        self._tokens = dict(tokens)
        self._known_ai_ids = set(tokens.values())
        self._authenticator = authenticator or Authenticator(tokens)
        self._store = store or SQLiteMessengerStore(":memory:")
        self._conversations = self._store.load_conversations()
        for conversation_id, members in conversations.items():
            normalized = set(members)
            if not conversation_id or len(normalized) < 2 or len(normalized) > self.MAX_ROOM_MEMBERS:
                raise ValueError("invalid_conversation_members")
            if not normalized.issubset(self._known_ai_ids):
                raise ValueError("unknown_conversation_member")
            self._conversations.setdefault(conversation_id, normalized)
            self._store.save_conversation(conversation_id, sorted(normalized))
        self._messages: Dict[str, Message] = {}
        self._idempotency: Dict[Tuple[str, str], str] = {}
        self._next_sequence: Dict[str, int] = {}
        acknowledgements = self._store.load_acknowledgements()
        for row in self._store.load_messages():
            ack = acknowledgements.get(row["message_id"], set())
            recipients = tuple(filter(None, row["recipient_ai_ids"].split(",")))
            msg = Message(row["message_id"], row["conversation_id"], row["sender_ai_id"], recipients,
                          row["body"], row["client_request_id"], row["sequence"], set(ack))
            self._messages[msg.message_id] = msg
            self._idempotency[(msg.sender_ai_id, msg.client_request_id)] = msg.message_id
            self._next_sequence[msg.conversation_id] = max(self._next_sequence.get(msg.conversation_id,0), msg.sequence)

    def close(self):
        self._store.close()

    def authenticate(self, bearer_token: str) -> str:
        return self._authenticator.authenticate(bearer_token).ai_id

    def assert_authenticated_sender(self, bearer_token: str, claimed_ai_id: str) -> str:
        authenticated_ai_id = self.authenticate(bearer_token)
        if claimed_ai_id and claimed_ai_id != authenticated_ai_id:
            raise PermissionError("sender_identity_mismatch")
        return authenticated_ai_id

    def assert_authenticated_principal(self, bearer_token: str, principal) -> str:
        current = self._authenticator.authenticate(bearer_token)
        if current.ai_id != principal.ai_id or current.credential_generation != principal.credential_generation:
            raise PermissionError("stale_authenticated_principal")
        return current.ai_id

    def create_conversation(self, bearer_token: str, conversation_id: str,
                            member_ai_ids: List[str], kind: str = "GROUP") -> Dict[str, object]:
        creator = self.authenticate(bearer_token)
        if (not isinstance(conversation_id, str) or not conversation_id.strip() or
                len(conversation_id) > self.MAX_ID_LENGTH):
            raise ValueError("invalid_conversation_id")
        if kind not in ("PRIVATE", "GROUP"):
            raise ValueError("invalid_conversation_kind")
        if not isinstance(member_ai_ids, list):
            raise ValueError("invalid_conversation_members")
        members = set(member_ai_ids)
        if creator not in members or len(members) != len(member_ai_ids):
            raise ValueError("invalid_conversation_members")
        if len(members) < 2 or len(members) > self.MAX_ROOM_MEMBERS:
            raise ValueError("conversation_member_limit")
        if kind == "PRIVATE" and len(members) != 2:
            raise ValueError("private_conversation_requires_two_members")
        if not members.issubset(self._known_ai_ids):
            raise ValueError("unknown_conversation_member")
        if conversation_id in self._conversations:
            raise ValueError("conversation_id_conflict")
        self._store.save_conversation(conversation_id, sorted(members))
        self._conversations[conversation_id] = members
        return {"conversationId": conversation_id, "kind": kind,
                "memberAiIds": sorted(members), "memberCount": len(members)}

    def authorize_member(self, ai_id: str, conversation_id: str) -> None:
        members = self._conversations.get(conversation_id)
        if not members or ai_id not in members:
            raise PermissionError("authorization_denied")

    def authorize_recipients(self, sender_ai_id: str, conversation_id: str, recipient_ai_ids: List[str]) -> Tuple[str, ...]:
        self.authorize_member(sender_ai_id, conversation_id)
        recipient_ids = tuple(dict.fromkeys(recipient_ai_ids))
        members = self._conversations.get(conversation_id, set())
        if not recipient_ids or not set(recipient_ids).issubset(members):
            raise PermissionError("recipient_authorization_denied")
        return recipient_ids

    def submit(self, bearer_token: str, message_id: str, conversation_id: str,
               recipient_ai_ids: List[str], body: str, client_request_id: str) -> Message:
        sender = self.authenticate(bearer_token)
        if (not isinstance(message_id, str) or not message_id.strip() or
                not isinstance(conversation_id, str) or not conversation_id.strip() or
                not isinstance(body, str) or not body.strip() or
                not isinstance(client_request_id, str) or not client_request_id.strip() or
                len(message_id) > self.MAX_ID_LENGTH or len(conversation_id) > self.MAX_ID_LENGTH or
                len(client_request_id) > self.MAX_ID_LENGTH or len(body) > self.MAX_BODY_LENGTH):
            raise ValueError("invalid_message")
        recipient_ids = self.authorize_recipients(sender, conversation_id, recipient_ai_ids)
        if message_id in self._messages and not self._idempotency.get((sender, client_request_id)):
            raise ValueError("message_id_conflict")
        key = (sender, client_request_id)
        existing_id = self._idempotency.get(key)
        if existing_id:
            existing = self._messages[existing_id]
            same = (existing.message_id, existing.conversation_id, existing.body, existing.recipient_ai_ids) == (message_id, conversation_id, body, recipient_ids)
            if same:
                return existing
            raise ValueError("idempotency_conflict")
        sequence = self._next_sequence.get(conversation_id, 0) + 1
        message = Message(message_id, conversation_id, sender, recipient_ids, body, client_request_id, sequence, set())
        self._store.save_message_with_idempotency((message.message_id,message.conversation_id,message.sender_ai_id,message.recipient_ai_ids,message.body,message.client_request_id,message.sequence))
        self._messages[message_id] = message
        self._idempotency[key] = message_id
        self._next_sequence[conversation_id] = sequence
        return message

    def pending(self, bearer_token: str, conversation_id: str, after_sequence: int = 0, limit: int = 50) -> List[Message]:
        ai_id = self.authenticate(bearer_token)
        members = self._conversations.get(conversation_id)
        if not members or ai_id not in members:
            raise PermissionError("authorization_denied")
        if after_sequence < 0 or limit < 1 or limit > 100:
            raise ValueError("invalid_cursor")
        pending = [m for m in self._messages.values() if m.conversation_id == conversation_id and m.sequence > after_sequence and ai_id in m.recipient_ai_ids and ai_id not in m.acknowledged_by]
        return sorted(pending, key=lambda m: m.sequence)[:limit]

    def acknowledge(self, bearer_token: str, message_id: str) -> Message:
        ai_id = self.authenticate(bearer_token)
        message = self._messages.get(message_id)
        if message is None or ai_id not in message.recipient_ai_ids:
            raise PermissionError("authorization_denied")
        message.acknowledged_by.add(ai_id)
        self._store.save_ack(message_id, ai_id)
        return message
