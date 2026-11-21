from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class AuthenticatedPrincipal:
    ai_id: str

class Authenticator:
    def __init__(self, token_to_ai_id: Dict[str, str]):
        self._token_to_ai_id = dict(token_to_ai_id)

    def authenticate(self, bearer_token: str) -> AuthenticatedPrincipal:
        if not bearer_token:
            raise PermissionError("authentication_required")
        ai_id = self._token_to_ai_id.get(bearer_token)
        if not ai_id:
            raise PermissionError("authentication_required")
        return AuthenticatedPrincipal(ai_id=ai_id)
