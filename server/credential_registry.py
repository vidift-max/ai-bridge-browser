from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional


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
    """Experimental runtime-only credential lifecycle registry.

    Tokens are supplied by the runtime environment and are not persisted here.
    """

    def __init__(self, token_to_ai_id: Dict[str, str]):
        self._records = {
            token: CredentialRecord(token=token, ai_id=ai_id)
            for token, ai_id in token_to_ai_id.items()
        }

    def authenticate(self, token: str, now: Optional[datetime] = None) -> str:
        record = self._records.get(token)
        if record is None or record.effective_status(now) != "ACTIVE":
            raise PermissionError("authentication_required")
        return record.ai_id

    def revoke(self, token: str) -> None:
        record = self._records.get(token)
        if record is None:
            raise KeyError("credential_unknown")
        self._records[token] = CredentialRecord(record.token, record.ai_id, "REVOKED", record.expires_at, record.generation)

    def expire(self, token: str) -> None:
        record = self._records.get(token)
        if record is None:
            raise KeyError("credential_unknown")
        self._records[token] = CredentialRecord(record.token, record.ai_id, "EXPIRED", record.expires_at, record.generation)

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

    def status(self, token: str) -> str:
        record = self._records.get(token)
        return "UNKNOWN" if record is None else record.effective_status()
