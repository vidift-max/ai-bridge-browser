from dataclasses import dataclass
from typing import Dict

from server.credential_registry import CredentialRegistry


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    ai_id: str


class Authenticator:
    def __init__(self, token_to_ai_id: Dict[str, str]):
        self._registry = CredentialRegistry(token_to_ai_id)

    def authenticate(self, bearer_token: str) -> AuthenticatedPrincipal:
        if not bearer_token:
            raise PermissionError("authentication_required")
        return AuthenticatedPrincipal(ai_id=self._registry.authenticate(bearer_token))

    def revoke(self, bearer_token: str) -> None:
        self._registry.revoke(bearer_token)

    def credential_status(self, bearer_token: str) -> str:
        return self._registry.status(bearer_token)
