"""Short-lived, in-memory web sessions for provisioned guest identities."""
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock


@dataclass(frozen=True)
class GuestWebSession:
    token_hash: str
    ai_id: str
    parent_credential: str
    created_at: datetime
    expires_at: datetime
    status: str = "ACTIVE"


class GuestWebSessionService:
    DEFAULT_TTL = timedelta(hours=12)
    MAX_TTL = timedelta(hours=12)

    def __init__(self, authenticator, ttl=DEFAULT_TTL):
        if not isinstance(ttl, timedelta) or ttl <= timedelta(0) or ttl > self.MAX_TTL:
            raise ValueError("guest_session_ttl_invalid")
        self._authenticator = authenticator
        self._ttl = ttl
        self._sessions = {}
        self._lock = RLock()

    @staticmethod
    def _hash(token):
        if not isinstance(token, str) or not token:
            return ""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def exchange(self, guest_credential):
        principal = self._authenticator.authenticate(guest_credential)
        if not principal.ai_id.startswith("AI-GUEST-"):
            raise PermissionError("guest_credential_required")
        now = datetime.now(timezone.utc)
        expires_at = now + self._ttl
        token = secrets.token_urlsafe(32)
        token_hash = self._hash(token)
        with self._lock:
            self._sessions[token_hash] = GuestWebSession(
                token_hash, principal.ai_id, guest_credential, now, expires_at)
        try:
            self._authenticator.provision_ephemeral_credential(
                token, principal.ai_id, expires_at, guest_credential)
        except Exception:
            with self._lock:
                self._sessions.pop(token_hash, None)
            try:
                self._authenticator.revoke(token)
            except (KeyError, PermissionError):
                pass
            raise
        return {"sessionToken": token, "aiId": principal.ai_id,
                "expiresAt": int(expires_at.timestamp()), "expiresInSeconds": int(self._ttl.total_seconds())}

    def authenticate(self, session_token):
        token_hash = self._hash(session_token)
        with self._lock:
            record = self._sessions.get(token_hash)
            if record is None or record.status != "ACTIVE":
                raise PermissionError("guest_session_not_active")
            if datetime.now(timezone.utc) >= record.expires_at:
                self._sessions[token_hash] = GuestWebSession(
                    record.token_hash, record.ai_id, record.parent_credential,
                    record.created_at, record.expires_at, "EXPIRED")
                raise PermissionError("guest_session_not_active")
            try:
                parent = self._authenticator.authenticate(record.parent_credential)
            except PermissionError:
                self._sessions[token_hash] = GuestWebSession(
                    record.token_hash, record.ai_id, record.parent_credential,
                    record.created_at, record.expires_at, "REVOKED")
                raise PermissionError("guest_session_not_active")
            if parent.ai_id != record.ai_id:
                raise PermissionError("guest_session_not_active")
            return {"aiId": record.ai_id, "expiresAt": int(record.expires_at.timestamp())}

    def revoke(self, session_token):
        token_hash = self._hash(session_token)
        with self._lock:
            record = self._sessions.get(token_hash)
            if record is None or record.status != "ACTIVE":
                return False
            # Revoke the credential before changing the local state. If the
            # persistent revocation fails, retain ACTIVE so a caller can
            # safely retry instead of creating an in-memory/persistent split.
            self._authenticator.revoke(session_token)
            self._sessions[token_hash] = GuestWebSession(
                record.token_hash, record.ai_id, record.parent_credential,
                record.created_at, record.expires_at, "REVOKED")
            return True
