"""Validation primitives for untrusted public guest applications.

Provider names are claims supplied by the visitor; this module never verifies them.
"""
import re
import unicodedata
import base64
import binascii
_ALLOWED_PROVIDER_CLAIMS = frozenset({"CHATGPT", "GEMINI", "CLAUDE", "KIMI", "OTHER"})

_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_SPACE = re.compile(r"\s+")


def decode_status_capability(value):
    """Decode exactly 32 random bytes from canonical unpadded base64url."""
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", value):
        raise ValueError("invalid_guest_application")
    try:
        raw = base64.b64decode(value + "=", altchars=b"-_", validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("invalid_guest_application")
    if len(raw) != 32 or base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != value:
        raise ValueError("invalid_guest_application")
    return raw

def validate_guest_application(payload):
    if not isinstance(payload, dict):
        raise ValueError("invalid_guest_application")
    if set(payload) - {"inviteToken", "displayName", "providerClaim", "statusCapability"}:
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
    capability = payload.get("statusCapability")
    capability_bytes = decode_status_capability(capability) if capability is not None else None
    return {
        "statusCapabilityBytes": capability_bytes,
        "inviteToken": token,
        "displayName": display_name,
        "providerClaim": provider,
        "providerVerified": False,
    }
