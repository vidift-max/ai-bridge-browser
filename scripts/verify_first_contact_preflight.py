"""Offline final preflight; validates readiness without authorizing or contacting staging."""
from __future__ import annotations

import json
import os
import re
import sys

from verify_first_contact_config import validate
from verify_staging_http import normalize_base_url


def preflight(base_url: str, conversation_id: str, env: dict[str, str]) -> dict:
    normalized = normalize_base_url(base_url)
    validate(
        normalized,
        conversation_id,
        env.get("MESSENGER_TOKEN_AI_A", ""),
        env.get("MESSENGER_TOKEN_AI_B", ""),
        env.get("MESSENGER_AI_ID_A", "AI-01"),
        env.get("MESSENGER_AI_ID_B", "AI-02"),
    )
    required = {
        "MESSENGER_ENVIRONMENT": "staging",
        "MESSENGER_ALLOW_EPHEMERAL_STAGING": "true",
        "MESSENGER_STORAGE_MODE": "ephemeral",
        "MESSENGER_DB_PATH": ":memory:",
    }
    for key, expected in required.items():
        if env.get(key) != expected:
            raise ValueError("staging_configuration_invalid:" + key)
    operation_id = env.get("MESSENGER_FIRST_CONTACT_OPERATION_ID", "")
    if not re.fullmatch(r"[A-Za-z0-9._-]{16,128}", operation_id):
        raise ValueError("valid_operation_id_required")
    return {
        "result": "PASS",
        "checks": {
            "httpsOrigin": "valid",
            "conversation": "configured",
            "identities": ["AI-01", "AI-02"],
            "credentials": "present_and_distinct",
            "storage": "ephemeral_in_memory",
            "operationId": "valid",
        },
        "network": "NOT_CONTACTED",
        "realContact": "NOT_AUTHORIZED",
        "execution": "NOT_STARTED",
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: verify_first_contact_preflight.py https://staging.example CONVERSATION_ID")
        return 2
    try:
        result = preflight(sys.argv[1], sys.argv[2], os.environ)
    except ValueError as exc:
        print(json.dumps({"result": "NO_GO", "reason": str(exc),
                          "network": "NOT_CONTACTED", "execution": "NOT_STARTED"}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
