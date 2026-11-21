from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class CredentialRecord:
    token: str
    ai_id: str
    status: str = "ACTIVE"

    def is_active(self) -> bool:
        return self.status == "ACTIVE"


class CredentialRegistry:
    """Experimental runtime-only credential lifecycle registry.

    Tokens are supplied by the runtime environment and are not persisted here.
    """

    def __init__(self, token_to_ai_id: Dict[str, str]):
        self._records = {
            token: CredentialRecord(token=token, ai_id=ai_id)
            for token, ai_id in token_to_ai_id.items()
        }

    def authenticate(self, token: str) -> str:
        record = self._records.get(token)
        if record is None or not record.is_active():
            raise PermissionError("authentication_required")
        return record.ai_id

    def revoke(self, token: str) -> None:
        record = self._records.get(token)
        if record is None:
            raise KeyError("credential_unknown")
        self._records[token] = CredentialRecord(
            token=record.token, ai_id=record.ai_id, status="REVOKED"
        )

    def status(self, token: str) -> str:
        record = self._records.get(token)
        return "UNKNOWN" if record is None else record.status
