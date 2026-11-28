"""Separate administrative authentication for Tool Hub permission management."""
import hmac
import os


ADMIN_PRINCIPAL = "tool-hub-admin"


def configured_admin_token():
    token = os.environ.get("TOOL_HUB_ADMIN_TOKEN", "")
    if len(token) < 32:
        return None
    return token


def authenticate_tool_admin(headers, expected_token=None):
    expected = expected_token if expected_token is not None else configured_admin_token()
    if not expected or len(expected) < 32:
        raise PermissionError("tool_admin_not_configured")
    authorization = headers.get("Authorization", "")
    scheme, separator, supplied = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not supplied:
        raise PermissionError("authentication_required")
    if not hmac.compare_digest(supplied, expected):
        raise PermissionError("tool_admin_forbidden")
    return ADMIN_PRINCIPAL
