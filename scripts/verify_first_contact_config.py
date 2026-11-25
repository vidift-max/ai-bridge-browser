#!/usr/bin/env python3
"""Validate first-contact configuration locally without making network requests."""
from __future__ import annotations
import json
import os
import sys
from urllib.parse import urlsplit


def validate(base_url: str, conversation_id: str, token_a: str, token_b: str,
             ai_id_a: str = "AI-01", ai_id_b: str = "AI-02") -> dict:
    if (not isinstance(base_url, str) or not base_url
            or base_url != base_url.strip() or any(ch.isspace() for ch in base_url)
            or "?" in base_url or "#" in base_url):
        raise ValueError("invalid_staging_url")
    try:
        parsed = urlsplit(base_url)
        port = parsed.port
    except ValueError:
        raise ValueError("invalid_staging_url") from None
    if (parsed.scheme.lower() != "https" or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment
            or "%" in parsed.netloc or "@" in parsed.netloc):
        raise ValueError("invalid_staging_url")
    hostname = parsed.hostname
    if not hostname or hostname.startswith(".") or hostname.endswith("."):
        raise ValueError("invalid_staging_url")
    if port is not None and not (1 <= port <= 65535):
        raise ValueError("invalid_staging_url")
    if (not isinstance(conversation_id, str) or not conversation_id.strip()
            or len(conversation_id) > 200
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in conversation_id)):
        raise ValueError("invalid_conversation_id")
    if ai_id_a != "AI-01" or ai_id_b != "AI-02":
        raise ValueError("fixed_ai_identity_required")
    if (not isinstance(token_a, str) or not token_a.strip()
            or not isinstance(token_b, str) or not token_b.strip()
            or token_a == token_b):
        raise ValueError("distinct_ai_credentials_required")
    return {"result":"PASS","network":"NOT_CONTACTED","ai01Identity":"configured",
            "ai02Identity":"configured","credentials":"distinct_and_present",
            "conversation":"configured","baseUrl":f"https://{parsed.netloc}"}


def main() -> int:
    if len(sys.argv) != 3:
        print(json.dumps({"result":"NO_GO","reason":"usage: verify_first_contact_config.py https://staging.example CONVERSATION_ID"}, sort_keys=True))
        return 2
    try:
        result = validate(sys.argv[1], sys.argv[2],
            os.environ.get("MESSENGER_TOKEN_AI_A", ""),
            os.environ.get("MESSENGER_TOKEN_AI_B", ""),
            os.environ.get("MESSENGER_AI_ID_A", "AI-01"),
            os.environ.get("MESSENGER_AI_ID_B", "AI-02"))
    except ValueError as exc:
        print(json.dumps({"result":"NO_GO","reason":str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
