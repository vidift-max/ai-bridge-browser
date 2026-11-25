"""Offline release-readiness gate; never grants authorization or contacts staging."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from verify_first_contact_preflight import preflight
from verify_staging_operator_readiness import audit


DEFAULT_CONVERSATION_ID = "default"


def release_readiness(blueprint_path: str | Path, origin: str,
                      conversation_id: str, env: dict[str, str]) -> dict:
    """Combine static Blueprint, operator environment, and first-contact preflight."""
    try:
        operator = audit(blueprint_path, env)
        if operator["result"] != "PASS":
            return {
                "result": "NO_GO",
                "blueprint": operator["blueprint"],
                "operatorEnvironment": operator["operatorEnvironment"],
                "conversation": "not_verified",
                "authorization": "NOT_GRANTED",
                "network": "NOT_CONTACTED",
                "deployment": "NOT_PERFORMED",
                "realContact": "NOT_STARTED",
                "failures": operator["failures"],
            }
        if conversation_id != DEFAULT_CONVERSATION_ID:
            raise ValueError("current_bootstrap_requires_default_conversation")
        checked = preflight(origin, conversation_id, env)
    except (OSError, UnicodeError):
        return {
            "result": "NO_GO", "blueprint": "unreadable",
            "operatorEnvironment": "not_verified",
            "authorization": "NOT_GRANTED", "network": "NOT_CONTACTED",
            "deployment": "NOT_PERFORMED", "realContact": "NOT_STARTED",
            "failures": ["blueprint_unreadable"],
        }
    except ValueError as exc:
        reason = str(exc)
        allowed = {
            "current_bootstrap_requires_default_conversation",
            "valid_operation_id_required",
            "distinct_ai_credentials_required",
            "https_origin_required",
        }
        if not (reason in allowed or reason.startswith(
                ("invalid_", "staging_configuration_invalid:", "https_"))):
            reason = "preflight_validation_failed"
        return {
            "result": "NO_GO", "blueprint": "valid",
            "operatorEnvironment": "valid",
            "conversation": "not_verified",
            "authorization": "NOT_GRANTED", "network": "NOT_CONTACTED",
            "deployment": "NOT_PERFORMED", "realContact": "NOT_STARTED",
            "failures": [reason],
        }

    return {
        "result": "PASS",
        "blueprint": "valid",
        "operatorEnvironment": "valid",
        "origin": "valid_https",
        "conversation": "default_verified",
        "identities": checked["checks"]["identities"],
        "credentials": "present_and_distinct",
        "storage": "ephemeral_in_memory",
        "operationId": "valid",
        "authorization": "NOT_GRANTED",
        "network": "NOT_CONTACTED",
        "deployment": "NOT_PERFORMED",
        "realContact": "NOT_STARTED",
        "failures": [],
    }


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("usage: verify_first_contact_release_readiness.py "
              "https://staging.example default [render.staging.yaml]")
        return 2
    blueprint = sys.argv[3] if len(sys.argv) == 4 else "render.staging.yaml"
    result = release_readiness(blueprint, sys.argv[1], sys.argv[2], os.environ)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
