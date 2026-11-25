"""Offline operator-readiness audit for the isolated first-contact staging Blueprint."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


REQUIRED_ENV = (
    "MESSENGER_TOKEN_AI_A",
    "MESSENGER_TOKEN_AI_B",
    "MESSENGER_AI_ID_A",
    "MESSENGER_AI_ID_B",
    "MESSENGER_ENVIRONMENT",
    "MESSENGER_ALLOW_EPHEMERAL_STAGING",
    "MESSENGER_STORAGE_MODE",
    "MESSENGER_DB_PATH",
)


def audit_blueprint(source: str) -> list[str]:
    failures = []
    checks = (
        ("service_name", r"name:\s*ai-bridge-browser-staging(?:\s|$)"),
        ("free_plan", r"plan:\s*free(?:\s|$)"),
        ("oregon_region", r"region:\s*oregon(?:\s|$)"),
        ("manual_deploy", r"autoDeployTrigger:\s*off(?:\s|$)"),
        ("ephemeral_storage", r"value:\s*ephemeral(?:\s|$)"),
        ("memory_database", r"value:\s*':memory:'"),
        ("staging_environment", r"value:\s*staging(?:\s|$)"),
        ("ephemeral_opt_in", r"value:\s*'true'"),
        ("ai01_identity", r"value:\s*AI-01(?:\s|$)"),
        ("ai02_identity", r"value:\s*AI-02(?:\s|$)"),
        ("health_check", r"healthCheckPath:\s*/healthz(?:\s|$)"),
    )
    for name, pattern in checks:
        if not re.search(pattern, source):
            failures.append(name)
    if re.search(r"(?im)^\s*type:\s*disk\s*$", source):
        failures.append("persistent_disk_absent")
    if re.search(r"(?im)^\s*mountPath:", source):
        failures.append("persistent_mount_absent")
    for key in ("MESSENGER_TOKEN_AI_A", "MESSENGER_TOKEN_AI_B"):
        block = re.search(rf"- key:\s*{key}\s*\n(?P<body>(?:\s+.*\n)*)", source)
        if not block or not re.search(r"sync:\s*false", block.group("body")):
            failures.append(key.lower() + "_manual_secret")
    return failures


def audit_environment(env: dict[str, str]) -> list[str]:
    failures = []
    for key in REQUIRED_ENV:
        if not env.get(key, "").strip():
            failures.append("missing_" + key.lower())
    expected = {
        "MESSENGER_AI_ID_A": "AI-01",
        "MESSENGER_AI_ID_B": "AI-02",
        "MESSENGER_ENVIRONMENT": "staging",
        "MESSENGER_ALLOW_EPHEMERAL_STAGING": "true",
        "MESSENGER_STORAGE_MODE": "ephemeral",
        "MESSENGER_DB_PATH": ":memory:",
    }
    for key, value in expected.items():
        if env.get(key) != value:
            failures.append("invalid_" + key.lower())
    token_a, token_b = env.get("MESSENGER_TOKEN_AI_A", ""), env.get("MESSENGER_TOKEN_AI_B", "")
    if token_a and token_b and token_a == token_b:
        failures.append("credentials_must_be_distinct")
    if any(char in token_a + token_b for char in "\r\n"):
        failures.append("credential_format_invalid")
    for key in (
        "MESSENGER_FIRST_CONTACT_STAGING_AUTHORIZED",
        "MESSENGER_FIRST_CONTACT_EXECUTE",
        "MESSENGER_FIRST_CONTACT_APPROVED_ORIGIN",
        "MESSENGER_FIRST_CONTACT_APPROVED_CONVERSATION_ID",
        "MESSENGER_FIRST_CONTACT_APPROVED_OPERATION_ID",
    ):
        if env.get(key, "").lower() == "true" or env.get(key):
            failures.append("execution_authorization_must_remain_unset")
            break
    return failures


def audit(blueprint_path: str | Path, env: dict[str, str]) -> dict:
    source = Path(blueprint_path).read_text(encoding="utf-8")
    blueprint_failures = audit_blueprint(source)
    environment_failures = audit_environment(env)
    failures = blueprint_failures + environment_failures
    return {
        "result": "PASS" if not failures else "NO_GO",
        "blueprint": "valid" if not blueprint_failures else "invalid",
        "operatorEnvironment": "valid" if not environment_failures else "incomplete_or_invalid",
        "authorization": "NOT_GRANTED",
        "network": "NOT_CONTACTED",
        "deployment": "NOT_PERFORMED",
        "realContact": "NOT_STARTED",
        "failures": failures,
    }


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) == 2 else Path("render.staging.yaml")
    try:
        result = audit(path, os.environ)
    except (OSError, UnicodeError):
        result = {
            "result": "NO_GO", "blueprint": "unreadable",
            "authorization": "NOT_GRANTED", "network": "NOT_CONTACTED",
            "deployment": "NOT_PERFORMED", "realContact": "NOT_STARTED",
            "failures": ["blueprint_unreadable"],
        }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
