from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from server.auth import AuthenticatedPrincipal, Authenticator


@dataclass(frozen=True)
class RequestIdentity:
    principal: AuthenticatedPrincipal
    correlation_id: str


def bearer_token(headers) -> str:
    header = headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return ""
    return header[7:].strip()


def request_correlation_id(headers) -> str:
    supplied = headers.get("X-Correlation-Id", "").strip()
    return supplied[:128] if supplied else str(uuid4())


def authenticate_request(authenticator: Authenticator, headers) -> RequestIdentity:
    token = bearer_token(headers)
    principal = authenticator.authenticate(token)
    return RequestIdentity(principal=principal, correlation_id=request_correlation_id(headers))
