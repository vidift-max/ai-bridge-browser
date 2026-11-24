"""Validation primitives for untrusted public guest applications.

Provider names are claims supplied by the visitor; this module never verifies them.
"""
import re
import unicodedata

_ALLOWED_PROVIDER_CLAIMS = frozenset({"CHATGPT", "GEMINI", "CLAUDE", "KIMI", "OTHER"})
_CONTROL = re.compile(r"[\\x00-\\x1f\\x7f]")
_SPACE = re.compile(r"\\s+")


def validate_guest_application(payload):
    if not isinstance(payload, dict):
        raise ValueError("invalid_guest_application")
    if set(payload) - {"inviteToken", "displayName", "providerClaim"}:
        raise ValueError("invalid_guest_application")
    token = payload.get("inviteToken")
    if not isinstance(token, str) or not 40 <= len(token) <= 200:
        raise ValueError("invalid_guest_application")
    if any(ord(char) < 33 or ord(char) > 126 for char in token):
        raise ValueError("invalid_guest_application")
    display_name = payload.get("displayName")
    if not isinstance(display_name, str):
        raise ValueError("invalid_guest_application")
    display_name = unicodedata.normalize("NFKC", display_name)
    display_name = _SPACE.sub(" ", _CONTROL.sub("", display_name)).strip()
    if not display_name or len(display_name) > 60:
        raise ValueError("invalid_guest_application")
    provider = payload.get("providerClaim")
    if not isinstance(provider, str):
        raise ValueError("invalid_guest_application")
    provider = provider.strip().upper()
    if provider not in _ALLOWED_PROVIDER_CLAIMS:
        raise ValueError("invalid_guest_application")
    return {
        "inviteToken": token,
        "displayName": display_name,
        "providerClaim": provider,
        "providerVerified": False,
    }
