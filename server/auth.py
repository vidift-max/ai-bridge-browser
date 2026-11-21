from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from server.credential_registry import CredentialRegistry
from server.audit import AuditLog


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    ai_id: str


class Authenticator:
    def __init__(self, token_to_ai_id: Dict[str, str], audit_log: Optional[AuditLog] = None):
        self._registry = CredentialRegistry(token_to_ai_id)
        self.audit_log = audit_log or AuditLog()

    def authenticate(self, bearer_token: str, now: Optional[datetime] = None) -> AuthenticatedPrincipal:
        if not bearer_token:
            raise PermissionError("authentication_required")
        ai_id = self._registry.authenticate(bearer_token, now)
        self.audit_log.record("AUTHENTICATED", "credential", ai_id=ai_id)
        return AuthenticatedPrincipal(ai_id=ai_id)

    def revoke(self, bearer_token: str) -> None:
        self._registry.revoke(bearer_token)
        self.audit_log.record("CREDENTIAL_REVOKED", "credential")

    def expire(self, bearer_token: str) -> None:
        self._registry.expire(bearer_token)
        self.audit_log.record("CREDENTIAL_EXPIRED", "credential")

    def rotate(self, old_bearer_token: str, new_bearer_token: str) -> None:
        self._registry.rotate(old_bearer_token, new_bearer_token)
        self.audit_log.record("CREDENTIAL_ROTATED", "credential")

    def credential_generation(self, bearer_token: str) -> int:
        return self._registry.generation(bearer_token)

    def credential_status(self, bearer_token: str) -> str:
        return self._registry.status(bearer_token)
