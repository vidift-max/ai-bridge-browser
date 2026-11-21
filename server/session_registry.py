from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class SessionRecord:
    session_id: str
    ai_id: str
    status: str
    expires_at: Optional[datetime] = None
    credential_generation: int = 1

    def effective_status(self, now: Optional[datetime] = None) -> str:
        if self.status != "ACTIVE":
            return self.status
        if self.expires_at is not None and (now or datetime.now(timezone.utc)) >= self.expires_at:
            return "EXPIRED"
        return "ACTIVE"


class SessionRegistry:
    """Experimental runtime-only session registry; no plaintext secret persistence."""

    def __init__(self):
        self._sessions = {}
        self._next_generation = {}

    def create(self, session_id: str, ai_id: str, expires_at: Optional[datetime] = None, credential_generation: int = 1) -> SessionRecord:
        if not session_id or not ai_id:
            raise ValueError("session_identity_required")
        if session_id in self._sessions:
            raise ValueError("session_already_exists")
        if credential_generation < 1:
            raise ValueError("credential_generation_invalid")
        generation = self._next_generation.get(ai_id, credential_generation)
        if generation < credential_generation:
            generation = credential_generation
        record = SessionRecord(session_id, ai_id, "ACTIVE", expires_at, generation)
        self._sessions[session_id] = record
        self._next_generation[ai_id] = generation
        return record

    def authenticate(self, session_id: str, now: Optional[datetime] = None) -> SessionRecord:
        record = self._sessions.get(session_id)
        if record is None:
            raise PermissionError("session_unknown")
        status = record.effective_status(now)
        if status != "ACTIVE":
            if status == "EXPIRED":
                self._sessions[session_id] = SessionRecord(record.session_id, record.ai_id, "EXPIRED", record.expires_at, record.credential_generation)
            raise PermissionError("session_not_active")
        return record

    def authenticate_bound(self, session_id: str, credential_generation: int, now: Optional[datetime] = None) -> SessionRecord:
        record = self.authenticate(session_id, now)
        if credential_generation != record.credential_generation:
            raise PermissionError("credential_generation_mismatch")
        return record

    def revoke(self, session_id: str) -> None:
        record = self._sessions.get(session_id)
        if record is None:
            raise KeyError("session_unknown")
        self._sessions[session_id] = SessionRecord(record.session_id, record.ai_id, "REVOKED", record.expires_at, record.credential_generation)

    def rotate(self, old_session_id: str, new_session_id: str, expires_at: Optional[datetime] = None) -> SessionRecord:
        old = self._sessions.get(old_session_id)
        if old is None:
            raise KeyError("session_unknown")
        if old.effective_status() != "ACTIVE":
            raise PermissionError("session_not_active")
        if new_session_id in self._sessions:
            raise ValueError("session_already_exists")
        self._sessions[old_session_id] = SessionRecord(old.session_id, old.ai_id, "ROTATED", old.expires_at, old.credential_generation)
        generation = old.credential_generation + 1
        record = SessionRecord(new_session_id, old.ai_id, "ACTIVE", expires_at, generation)
        self._sessions[new_session_id] = record
        self._next_generation[old.ai_id] = generation
        return record

    def status(self, session_id: str, now: Optional[datetime] = None) -> str:
        record = self._sessions.get(session_id)
        return "UNKNOWN" if record is None else record.effective_status(now)
