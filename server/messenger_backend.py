from dataclasses import dataclass
import hashlib
import math
import secrets
from functools import wraps
from threading import Condition, RLock
from typing import Dict, List, Set, Tuple
import time
from datetime import datetime, timedelta, timezone
from server.auth import Authenticator
from server.sqlite_store import SQLiteMessengerStore
from server.audio_blob_store import AudioBlobStore
from server.presence_service import PresenceService
from server.identity_directory import IdentityDirectory
from server.retention_policy import (MESSAGE_NORMAL, MESSAGE_MISSION, CONVERSATION_GROUP,
                                     expires_at, is_expired, normalize_message_kind, normalize_conversation_kind)

def _synchronized(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapped


@dataclass(frozen=True)
class AudioAttachment:
    object_id: str
    message_id: str
    conversation_id: str
    sender_ai_id: str
    content_type: str
    size: int
    sha256: str


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
    kind: str = MESSAGE_NORMAL
    created_at_epoch_seconds: float = 0.0

class MessengerBackend:
    MAX_BODY_LENGTH = 5000
    MAX_ID_LENGTH = 200
    MAX_ROOM_MEMBERS = 20
    TRANSPORT_CONTRACT_VERSION = 1
    LONG_POLL_MAX_WAIT_SECONDS = 25
    LONG_POLL_DEFAULT_WAIT_SECONDS = 20
    LONG_POLL_MAX_BATCH_SIZE = 100
    LONG_POLL_MAX_SEQUENCE = 9007199254740991

    def __init__(self, tokens: Dict[str, str], conversations: Dict[str, Set[str]], store=None, authenticator=None, identity_display_names=None):
        self._lock = RLock()
        self._message_condition = Condition(self._lock)
        self._tokens = dict(tokens)
        self._known_ai_ids = set(tokens.values())
        self._store = store or SQLiteMessengerStore(":memory:")
        self._authenticator = authenticator or Authenticator(tokens, connection=self._store._connection)
        if authenticator is not None:
            self._authenticator.attach_credential_store(self._store._connection)
        self._presence = PresenceService(self._store._connection)
        self._identities = IdentityDirectory(self._store._connection, self._known_ai_ids, identity_display_names)
        self._conversations = self._store.load_conversations()
        self._conversation_kinds = self._store.load_conversation_kinds()
        for conversation_id, members in conversations.items():
            normalized = set(members)
            if not conversation_id or len(normalized) < 2 or len(normalized) > self.MAX_ROOM_MEMBERS:
                raise ValueError("invalid_conversation_members")
            if not normalized.issubset(self._known_ai_ids):
                raise ValueError("unknown_conversation_member")
            self._conversations.setdefault(conversation_id, normalized)
            self._store.save_conversation(conversation_id, sorted(normalized), self._conversation_kinds.get(conversation_id, CONVERSATION_GROUP))
        self._messages: Dict[str, Message] = {}
        self._idempotency: Dict[Tuple[str, str], str] = {}
        self._next_sequence: Dict[str, int] = {}
        acknowledgements = self._store.load_acknowledgements()
        for row in self._store.load_messages():
            ack = acknowledgements.get(row["message_id"], set())
            recipients = tuple(filter(None, row["recipient_ai_ids"].split(",")))
            created = float(row["created_at_epoch_seconds"] or 0.0)
            if created <= 0:
                created = time.time()
            msg = Message(row["message_id"], row["conversation_id"], row["sender_ai_id"], recipients,
                          row["body"], row["client_request_id"], row["sequence"], set(ack),
                          normalize_message_kind(row["kind"] or MESSAGE_NORMAL), created)
            self._messages[msg.message_id] = msg
            self._idempotency[(msg.sender_ai_id, msg.client_request_id)] = msg.message_id
            self._next_sequence[msg.conversation_id] = max(self._next_sequence.get(msg.conversation_id,0), msg.sequence)

    @_synchronized
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

    @_synchronized
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
        self._store.save_conversation(conversation_id, sorted(members), kind)
        self._store.save_conversation_admin(conversation_id, creator)
        self._conversations[conversation_id] = members
        self._conversation_kinds[conversation_id] = normalize_conversation_kind(kind)
        return {"conversationId": conversation_id, "kind": kind,
                "memberAiIds": sorted(members), "memberCount": len(members)}


    @_synchronized
    def create_room_invite(self, bearer_token: str, conversation_id: str,
                           expires_in_seconds: int = 86400, max_uses: int = 5):
        ai_id = self.authenticate(bearer_token)
        if not isinstance(conversation_id, str) or not conversation_id:
            raise ValueError("invalid_conversation_id")
        members = self._conversations.get(conversation_id)
        if not members or ai_id not in members:
            raise PermissionError("authorization_denied")
        if not self._store.is_conversation_admin(conversation_id, ai_id):
            raise PermissionError("room_admin_required")
        if (isinstance(expires_in_seconds, bool) or not isinstance(expires_in_seconds, int)
                or expires_in_seconds < 60 or expires_in_seconds > 604800):
            raise ValueError("invalid_invite_expiry")
        if (isinstance(max_uses, bool) or not isinstance(max_uses, int)
                or max_uses < 1 or max_uses > self.MAX_ROOM_MEMBERS):
            raise ValueError("invalid_invite_max_uses")
        now = time.time()
        token = secrets.token_urlsafe(32)
        invite_id = secrets.token_hex(16)
        self._store.create_room_invite({
            "invite_id": invite_id, "conversation_id": conversation_id,
            "token_hash": hashlib.sha256(token.encode("utf-8")).hexdigest(),
            "created_by_ai_id": ai_id, "created_at": now,
            "expires_at": now + expires_in_seconds, "max_uses": max_uses})
        return {"inviteId": invite_id, "token": token, "conversationId": conversation_id,
                "expiresAt": now + expires_in_seconds, "maxUses": max_uses}

    @_synchronized
    def get_public_invite(self, invite_id: str):
        invite = self._store.get_room_invite(invite_id)
        if invite is None:
            raise ValueError("invite_not_found")
        now = time.time()
        if invite["revoked_at"] is not None:
            status = "REVOKED"
        elif invite["expires_at"] <= now:
            status = "EXPIRED"
        elif invite["uses"] >= invite["max_uses"]:
            status = "EXHAUSTED"
        else:
            status = "ACTIVE"
        return {"inviteId": invite["invite_id"], "status": status,
                "expiresAt": invite["expires_at"],
                "remainingUses": max(0, invite["max_uses"] - invite["uses"])}

    @_synchronized
    def redeem_room_invite(self, bearer_token: str, token: str):
        ai_id = self.authenticate(bearer_token)
        if not isinstance(token, str) or len(token) < 40 or len(token) > 200:
            raise ValueError("invalid_invite_token")
        invite = self._store.find_room_invite_by_hash(
            hashlib.sha256(token.encode("utf-8")).hexdigest())
        if invite is None or invite["conversation_id"] not in self._conversations:
            raise ValueError("invite_unavailable")
        if ai_id in self._conversations[invite["conversation_id"]]:
            raise ValueError("already_room_member")
        now = time.time()
        request = {"request_id": secrets.token_hex(16), "invite_id": invite["invite_id"],
                   "conversation_id": invite["conversation_id"], "ai_id": ai_id,
                   "created_at": now}
        row, outcome = self._store.create_join_request(request)
        if outcome == "invite_unavailable":
            raise ValueError("invite_unavailable")
        if outcome == "request_exists":
            if row["status"] == "PENDING":
                return {"requestId": row["request_id"], "status": row["status"],
                        "conversationId": row["conversation_id"]}
            raise ValueError("join_request_already_decided")
        return {"requestId": row["request_id"], "status": row["status"],
                "conversationId": row["conversation_id"]}


    @_synchronized
    def submit_public_guest_application(self, payload):
        from server.guest_intake import validate_guest_application
        clean = validate_guest_application(payload)
        token_hash = hashlib.sha256(clean["inviteToken"].encode("utf-8")).hexdigest()
        now = time.time()
        application = {
            "application_id": secrets.token_hex(16),
            "display_name": clean["displayName"],
            "provider_claim": clean["providerClaim"],
            "created_at": now,
        }
        row, outcome = self._store.create_guest_application(application, token_hash)
        if outcome == "invite_unavailable" or row["conversation_id"] not in self._conversations:
            raise ValueError("invite_unavailable")
        return {
            "applicationId": row["application_id"],
            "status": row["status"],
            "conversationId": row["conversation_id"],
            "displayName": row["display_name"],
            "providerClaim": row["provider_claim"],
            "providerVerified": False,
            "accessGranted": False,
        }

    @_synchronized
    def list_guest_applications(self, bearer_token: str, conversation_id: str):
        ai_id = self.authenticate(bearer_token)
        if not self._store.is_conversation_admin(conversation_id, ai_id):
            raise PermissionError("room_admin_required")
        return self._store.list_guest_applications(conversation_id)

    @_synchronized
    def decide_guest_application(self, bearer_token: str, conversation_id: str,
                                 application_id: str, decision: str):
        ai_id = self.authenticate(bearer_token)
        if not self._store.is_conversation_admin(conversation_id, ai_id):
            raise PermissionError("room_admin_required")
        if decision not in ("APPROVE", "REJECT"):
            raise ValueError("invalid_guest_decision")
        row = self._store.decide_guest_application(
            conversation_id, application_id, decision, ai_id, time.time())
        if row is None:
            raise ValueError("guest_application_unavailable")
        return row



    @_synchronized
    def provision_guest_application(self, bearer_token: str, conversation_id: str,
                                    application_id: str):
        admin_ai_id = self.authenticate(bearer_token)
        if not self._store.is_conversation_admin(conversation_id, admin_ai_id):
            raise PermissionError("room_admin_required")
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=30)
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        ai_id = "AI-GUEST-" + secrets.token_hex(12)
        result = self._store.provision_guest_application(
            conversation_id, application_id, ai_id, "", token_hash,
            expires_at.timestamp(), now.timestamp())
        if result is None or result["conversation_id"] != conversation_id:
            raise ValueError("guest_application_unavailable")
        try:
            self._authenticator.activate_persisted_credential(token, ai_id, expires_at)
        except Exception:
            # The SQLite transaction has already committed. Fail closed by
            # revoking the persisted provisioning so a registry activation
            # failure cannot leave an apparently active guest credential.
            rollback = self._store.revoke_guest_provisioning(
                conversation_id, application_id, time.time())
            if rollback is not None and rollback["token_hash"]:
                self._authenticator.revoke_credential_hash(rollback["token_hash"])
            raise
        self._known_ai_ids.add(ai_id)
        self._conversations.setdefault(conversation_id, set()).add(ai_id)
        identity = self._identities.get(ai_id)
        return {
            "applicationId": application_id,
            "identity": identity,
            "providerClaim": result["provider_claim"],
            "providerVerified": False,
            "credential": token,
            "credentialExpiresAt": expires_at.isoformat(),
            "credentialShownOnce": True,
            "roomAccess": "INVITED_ROOM_ONLY",
        }

    @_synchronized
    def revoke_guest_provisioning(self, bearer_token: str, conversation_id: str,
                                  application_id: str):
        admin_ai_id = self.authenticate(bearer_token)
        if not self._store.is_conversation_admin(conversation_id, admin_ai_id):
            raise PermissionError("room_admin_required")
        result = self._store.revoke_guest_provisioning(
            conversation_id, application_id, time.time())
        if result is None:
            raise ValueError("guest_credential_unavailable")
        if result["token_hash"]:
            self._authenticator.revoke_credential_hash(result["token_hash"])
        self._conversations.get(conversation_id, set()).discard(result["ai_id"])
        # Wake room-scoped long polls so revoked credentials/membership are revalidated now.
        self._message_condition.notify_all()
        return {"applicationId": application_id, "aiId": result["ai_id"],
                "status": "REVOKED", "roomAccessRemoved": True}

    @_synchronized
    def list_join_requests(self, bearer_token: str, conversation_id: str):
        ai_id = self.authenticate(bearer_token)
        if not self._store.is_conversation_admin(conversation_id, ai_id):
            raise PermissionError("room_admin_required")
        return self._store.list_join_requests(conversation_id)

    @_synchronized
    def decide_join_request(self, bearer_token: str, conversation_id: str,
                            request_id: str, decision: str):
        ai_id = self.authenticate(bearer_token)
        if not self._store.is_conversation_admin(conversation_id, ai_id):
            raise PermissionError("room_admin_required")
        if decision not in ("APPROVE", "REJECT"):
            raise ValueError("invalid_join_request_decision")
        result, outcome = self._store.decide_join_request(
            conversation_id, request_id, decision, ai_id, time.time(),
            self.MAX_ROOM_MEMBERS)
        if outcome == "request_not_found":
            raise ValueError("join_request_not_found")
        if outcome == "request_already_decided":
            raise ValueError("join_request_already_decided")
        if outcome == "conversation_member_limit":
            raise ValueError("conversation_member_limit")
        if decision == "APPROVE":
            self._conversations[conversation_id] = self._store.load_conversations()[conversation_id]
        return {"requestId": result["request_id"], "status": result["status"],
                "aiId": result["ai_id"], "conversationId": conversation_id}

    @_synchronized
    def revoke_room_invite(self, bearer_token: str, conversation_id: str, invite_id: str):
        ai_id = self.authenticate(bearer_token)
        if not self._store.is_conversation_admin(conversation_id, ai_id):
            raise PermissionError("room_admin_required")
        changed = self._store.revoke_room_invite(invite_id, conversation_id, time.time())
        if not changed:
            raise ValueError("invite_not_found_or_revoked")
        return {"inviteId": invite_id, "status": "REVOKED"}

    @_synchronized
    def list_room_invites(self, bearer_token: str, conversation_id: str):
        ai_id = self.authenticate(bearer_token)
        if not self._store.is_conversation_admin(conversation_id, ai_id):
            raise PermissionError("room_admin_required")
        return self._store.list_room_invites(conversation_id)

    @_synchronized
    def list_conversations(self, bearer_token: str, limit: int = 50,
                          after: str = "") -> Dict[str, object]:
        """List only rooms visible to the authenticated participant.

        The opaque cursor is the last conversation ID from the prior page.
        Membership is evaluated from the server-owned conversation registry.
        """
        ai_id = self.authenticate(bearer_token)
        if (isinstance(limit, bool) or not isinstance(limit, int) or
                limit < 1 or limit > 100):
            raise ValueError("invalid_conversation_limit")
        if not isinstance(after, str) or len(after) > self.MAX_ID_LENGTH:
            raise ValueError("invalid_conversation_cursor")
        visible_ids = sorted(
            conversation_id for conversation_id, members in self._conversations.items()
            if ai_id in members and conversation_id > after
        )
        page_ids = visible_ids[:limit]
        items = []
        for conversation_id in page_ids:
            members = sorted(self._conversations[conversation_id])
            items.append({
                "conversationId": conversation_id,
                "kind": self._conversation_kinds.get(conversation_id, CONVERSATION_GROUP),
                "memberAiIds": members,
                "memberCount": len(members),
                "isAdmin": self._store.is_conversation_admin(conversation_id, ai_id),
            })
        next_cursor = page_ids[-1] if len(visible_ids) > len(page_ids) and page_ids else None
        return {"conversations": items, "nextCursor": next_cursor}

    @_synchronized
    def heartbeat_presence(self, bearer_token: str, active_conversation_ids):
        ai_id = self.authenticate(bearer_token)
        allowed = [conversation_id for conversation_id, members in self._conversations.items()
                   if ai_id in members]
        return self._presence.heartbeat(ai_id, active_conversation_ids, allowed)

    @_synchronized
    def leave_presence(self, bearer_token: str):
        ai_id = self.authenticate(bearer_token)
        return self._presence.leave(ai_id)

    @_synchronized
    def list_conversation_presence(self, bearer_token: str, conversation_id: str):
        ai_id = self.authenticate(bearer_token)
        self.authorize_member(ai_id, conversation_id)
        members = sorted(self._conversations.get(conversation_id, set()))
        return self._presence.list_room(conversation_id, members)

    @_synchronized
    def list_conversation_identities(self, bearer_token: str, conversation_id: str):
        ai_id = self.authenticate(bearer_token)
        self.authorize_member(ai_id, conversation_id)
        members = sorted(self._conversations.get(conversation_id, set()))
        identities = self._identities.list_members(members)
        presence = {item["aiId"]: item for item in
                    self._presence.list_room(conversation_id, members)}
        result = []
        for identity in identities:
            state = presence[identity["aiId"]]
            result.append({**identity, "status": state["status"],
                           "activeInRoom": state["activeInRoom"],
                           "lastSeenAt": state["lastSeenAt"]})
        return result

    @_synchronized
    def conversation_members(self):
        """Return a defensive snapshot for server-side room authorization."""
        return {conversation_id: set(members)
                for conversation_id, members in self._conversations.items()}

    @_synchronized
    def conversation_kinds(self):
        """Return a defensive snapshot of conversation kinds for call policy."""
        return dict(self._conversation_kinds)

    def authorize_member(self, ai_id: str, conversation_id: str) -> None:
        members = self._conversations.get(conversation_id)
        if not members or ai_id not in members:
            raise PermissionError("authorization_denied")

    def authorize_recipients(self, sender_ai_id: str, conversation_id: str, recipient_ai_ids: List[str]) -> Tuple[str, ...]:
        if (not isinstance(recipient_ai_ids, list) or not recipient_ai_ids or
                any(not isinstance(item, str) or not item.strip() for item in recipient_ai_ids)):
            raise ValueError("invalid_recipients")
        self.authorize_member(sender_ai_id, conversation_id)
        recipient_ids = tuple(dict.fromkeys(recipient_ai_ids))
        members = self._conversations.get(conversation_id, set())
        if not set(recipient_ids).issubset(members):
            raise PermissionError("recipient_authorization_denied")
        return recipient_ids

    @_synchronized
    def submit(self, bearer_token: str, message_id: str, conversation_id: str,
               recipient_ai_ids: List[str], body: str, client_request_id: str,
               message_kind: str = MESSAGE_NORMAL) -> Message:
        sender = self.authenticate(bearer_token)
        if (not isinstance(message_id, str) or not message_id.strip() or
                not isinstance(conversation_id, str) or not conversation_id.strip() or
                not isinstance(body, str) or not body.strip() or
                not isinstance(client_request_id, str) or not client_request_id.strip() or
                len(message_id) > self.MAX_ID_LENGTH or len(conversation_id) > self.MAX_ID_LENGTH or
                len(client_request_id) > self.MAX_ID_LENGTH or len(body) > self.MAX_BODY_LENGTH):
            raise ValueError("invalid_message")
        recipient_ids = self.authorize_recipients(sender, conversation_id, recipient_ai_ids)
        normalized_kind = normalize_message_kind(message_kind)
        created_at = time.time()
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
        message = Message(message_id, conversation_id, sender, recipient_ids, body, client_request_id, sequence, set(), normalized_kind, created_at)
        self._store.save_message_with_idempotency((message.message_id,message.conversation_id,message.sender_ai_id,message.recipient_ai_ids,message.body,message.client_request_id,message.sequence,message.kind,message.created_at_epoch_seconds))
        self._messages[message_id] = message
        self._message_condition.notify_all()
        self._idempotency[key] = message_id
        self._next_sequence[conversation_id] = sequence
        return message

    def message_expires_at(self, message: Message) -> float:
        return expires_at(message.created_at_epoch_seconds,
                          message.kind,
                          self._conversation_kinds.get(message.conversation_id, CONVERSATION_GROUP))

    def _purge_expired(self):
        now = time.time()
        expired = []
        for message_id, message in list(self._messages.items()):
            conversation_kind = self._conversation_kinds.get(message.conversation_id, CONVERSATION_GROUP)
            if is_expired(message.created_at_epoch_seconds, message.kind, conversation_kind, now):
                expired.append(message_id)
        for message_id in expired:
            message = self._messages.pop(message_id, None)
            if message is None:
                continue
            self._store.delete_message(message_id)
            for key, value in list(self._idempotency.items()):
                if value == message_id:
                    self._idempotency.pop(key, None)

    @_synchronized
    def attach_audio(self, bearer_token: str, message_id: str, audio_store: AudioBlobStore,
                     data: bytes, declared_type: str) -> AudioAttachment:
        self._purge_expired()
        sender = self.authenticate(bearer_token)
        message = self._messages.get(message_id)
        if message is None:
            raise ValueError("message_not_found")
        if message.sender_ai_id != sender:
            raise PermissionError("attachment_sender_only")
        stored = audio_store.save(data, declared_type)
        try:
            self._store.save_audio_attachment((
                stored.object_id, message.message_id, message.conversation_id,
                sender, stored.content_type, stored.size, stored.sha256,
            ))
        except Exception:
            audio_store.delete(stored.object_id)
            raise
        return AudioAttachment(stored.object_id, message.message_id, message.conversation_id,
                               sender, stored.content_type, stored.size, stored.sha256)

    @_synchronized
    def list_audio_attachments(self, bearer_token: str, message_id: str):
        self._purge_expired()
        ai_id = self.authenticate(bearer_token)
        message = self._messages.get(message_id)
        if message is None:
            raise ValueError("message_not_found")
        self.authorize_member(ai_id, message.conversation_id)
        return [AudioAttachment(
            row["object_id"], row["message_id"], row["conversation_id"],
            row["sender_ai_id"], row["content_type"], row["size"], row["sha256"])
            for row in self._store.load_audio_attachments_for_message(message_id)]

    @_synchronized
    def read_audio(self, bearer_token: str, message_id: str, object_id: str,
                   audio_store: AudioBlobStore) -> bytes:
        self._purge_expired()
        ai_id = self.authenticate(bearer_token)
        message = self._messages.get(message_id)
        if message is None:
            raise ValueError("message_not_found")
        self.authorize_member(ai_id, message.conversation_id)
        rows = self._store.load_audio_attachments_for_message(message_id)
        if not any(row["object_id"] == object_id for row in rows):
            raise PermissionError("audio_attachment_not_authorized")
        return audio_store.read(object_id)

    def transport_capabilities(self, bearer_token: str, conversation_id: str) -> dict:
        with self._lock:
            self._purge_expired()
            ai_id = self.authenticate(bearer_token)
            members = self._conversations.get(conversation_id)
            if not members or ai_id not in members:
                raise PermissionError("authorization_denied")
            return {
                "contractVersion": self.TRANSPORT_CONTRACT_VERSION,
                "conversationId": conversation_id,
                "authorized": True,
                "defaultTransport": "HTTP_LONG_POLL",
                "transports": {
                    "httpLongPoll": {
                        "enabled": True,
                        "minWaitSeconds": 0,
                        "maxWaitSeconds": self.LONG_POLL_MAX_WAIT_SECONDS,
                        "defaultWaitSeconds": self.LONG_POLL_DEFAULT_WAIT_SECONDS,
                        "maxBatchSize": self.LONG_POLL_MAX_BATCH_SIZE,
                    },
                    "webSocket": {"enabled": False},
                    "serverPush": {"enabled": False},
                },
                "cursor": {"type": "sequence", "ackRequired": True},
            }

    @classmethod
    def _validate_long_poll_cursor_and_limit(cls, after_sequence, limit):
        if (isinstance(after_sequence, bool) or not isinstance(after_sequence, int)
                or after_sequence < 0 or after_sequence > cls.LONG_POLL_MAX_SEQUENCE):
            raise ValueError("invalid_cursor")
        if (isinstance(limit, bool) or not isinstance(limit, int)
                or limit < 1 or limit > cls.LONG_POLL_MAX_BATCH_SIZE):
            raise ValueError("invalid_cursor")

    @classmethod
    def _validate_long_poll_timeout(cls, timeout_seconds):
        if (isinstance(timeout_seconds, bool)
                or not isinstance(timeout_seconds, (int, float))
                or timeout_seconds < 0
                or timeout_seconds > cls.LONG_POLL_MAX_WAIT_SECONDS
                or not math.isfinite(timeout_seconds)):
            raise ValueError("invalid_wait_timeout")

    def wait_for_messages(self, bearer_token: str, conversation_id: str, after_sequence: int = 0, limit: int = 50, timeout_seconds: float = 20.0) -> List[Message]:
        self._validate_long_poll_cursor_and_limit(after_sequence, limit)
        self._validate_long_poll_timeout(timeout_seconds)
        deadline = time.monotonic() + float(timeout_seconds)
        with self._message_condition:
            self.authenticate(bearer_token)
            while True:
                messages = self.pending(bearer_token, conversation_id, after_sequence=after_sequence, limit=limit)
                if messages:
                    return messages
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return []
                self._message_condition.wait(timeout=remaining)

    @_synchronized
    def pending(self, bearer_token: str, conversation_id: str, after_sequence: int = 0, limit: int = 50) -> List[Message]:
        self._purge_expired()
        ai_id = self.authenticate(bearer_token)
        members = self._conversations.get(conversation_id)
        if not members or ai_id not in members:
            raise PermissionError("authorization_denied")
        self._validate_long_poll_cursor_and_limit(after_sequence, limit)
        pending = [m for m in self._messages.values() if m.conversation_id == conversation_id and m.sequence > after_sequence and ai_id in m.recipient_ai_ids and ai_id not in m.acknowledged_by]
        return sorted(pending, key=lambda m: m.sequence)[:limit]

    @_synchronized
    def history(self, bearer_token: str, conversation_id: str,
                before_sequence: int = 0, limit: int = 50) -> List[Message]:
        """Return authorized, non-expired conversation history without changing ACK state."""
        self._purge_expired()
        ai_id = self.authenticate(bearer_token)
        members = self._conversations.get(conversation_id)
        if not members or ai_id not in members:
            raise PermissionError("authorization_denied")
        if (isinstance(before_sequence, bool) or not isinstance(before_sequence, int)
                or before_sequence < 0 or before_sequence > self.LONG_POLL_MAX_SEQUENCE):
            raise ValueError("invalid_history_cursor")
        self._validate_long_poll_cursor_and_limit(0, limit)
        candidates = [message for message in self._messages.values()
                      if message.conversation_id == conversation_id
                      and (before_sequence == 0 or message.sequence < before_sequence)]
        page = sorted(candidates, key=lambda message: message.sequence, reverse=True)[:limit]
        return list(reversed(page))

    @_synchronized
    def acknowledge(self, bearer_token: str, message_id: str) -> Message:
        self._purge_expired()
        ai_id = self.authenticate(bearer_token)
        message = self._messages.get(message_id)
        members = self._conversations.get(message.conversation_id) if message is not None else None
        if (message is None or not members or ai_id not in members or
                ai_id not in message.recipient_ai_ids):
            raise PermissionError("authorization_denied")
        if ai_id not in message.acknowledged_by:
            self._store.save_ack(message_id, ai_id)
            message.acknowledged_by.add(ai_id)
        return message