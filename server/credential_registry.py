from dataclasses import dataclass
from functools import wraps
from threading import RLock
from datetime import datetime, timezone
from typing import Dict, Optional


def _synchronized(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapped


@dataclass(frozen=True)
class CredentialRecord:
    token: str
    ai_id: str
    status: str = "ACTIVE"
    expires_at: Optional[datetime] = None
    generation: int = 1

    def effective_status(self, now: Optional[datetime] = None) -> str:
        if self.status != "ACTIVE":
            return self.status
        if self.expires_at is not None and (now or datetime.now(timezone.utc)) >= self.expires_at:
            return "EXPIRED"
        return "ACTIVE"


class CredentialRegistry:
    """Experimental runtime-only credential lifecycle registry."""

    def __init__(self, token_to_ai_id: Dict[str, str], token_expiry: Optional[Dict[str, datetime]] = None):
        self._lock = RLock()
        expiry = token_expiry or {}
        self._records = {
            token: CredentialRecord(token=token, ai_id=ai_id, expires_at=expiry.get(token))
            for token, ai_id in token_to_ai_id.items()
        }

    @_synchronized
    def authenticate(self, token: str, now: Optional[datetime] = None) -> str:
        record = self._records.get(token)
        if record is None or record.effective_status(now) != "ACTIVE":
            raise PermissionError("authentication_required")
        return record.ai_id

    @_synchronized
    def revoke(self, token: str) -> None:
        record = self._records.get(token)
        if record is None:
            raise KeyError("credential_unknown")
        self._records[token] = CredentialRecord(record.token, record.ai_id, "REVOKED", record.expires_at, record.generation)

    @_synchronized
    def expire(self, token: str) -> None:
        record = self._records.get(token)
        if record is None:
            raise KeyError("credential_unknown")
        self._records[token] = CredentialRecord(record.token, record.ai_id, "EXPIRED", record.expires_at, record.generation)

    @_synchronized
    def rotate(self, old_token: str, new_token: str) -> None:
        old = self._records.get(old_token)
        if old is None:
            raise KeyError("credential_unknown")
        if old.effective_status() != "ACTIVE":
            raise PermissionError("credential_not_active")
        if new_token in self._records:
            raise ValueError("credential_already_exists")
        self._records[old_token] = CredentialRecord(old.token, old.ai_id, "ROTATED", old.expires_at, old.generation)
        self._records[new_token] = CredentialRecord(new_token, old.ai_id, "ACTIVE", None, old.generation + 1)

    @_synchronized
    def generation(self, token: str) -> int:
        record = self._records.get(token)
        if record is None:
            raise PermissionError("authentication_required")
        return record.generation

    @_synchronized
    def status(self, token: str, now: Optional[datetime] = None) -> str:
        record = self._records.get(token)
        return "UNKNOWN" if record is None else record.effective_status(now)
