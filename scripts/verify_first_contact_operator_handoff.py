"""Generate a redacted, offline operator handoff for first-contact staging."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from verify_staging_operator_readiness import audit_blueprint


def build_handoff(blueprint_path: str | Path) -> dict:
    try:
        source = Path(blueprint_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {
            "result": "NO_GO", "blueprint": "unreadable",
            "authorization": "NOT_GRANTED", "network": "NOT_CONTACTED",
            "deployment": "NOT_PERFORMED", "realContact": "NOT_STARTED",
            "failures": ["blueprint_unreadable"], "steps": [],
        }
    failures = audit_blueprint(source)
    if failures:
        return {
            "result": "NO_GO", "blueprint": "invalid",
            "authorization": "NOT_GRANTED", "network": "NOT_CONTACTED",
            "deployment": "NOT_PERFORMED", "realContact": "NOT_STARTED",
            "failures": failures, "steps": [],
        }
    steps = [
        {"id": "create_free_staging", "action": "Operator creates the isolated Free staging service from render.staging.yaml in Render Dashboard.", "requires": "operator_action", "complete": False},
        {"id": "configure_private_credentials", "action": "Operator privately configures two distinct bearer secrets for AI-01 and AI-02; never commit, paste into chat, or log their values.", "requires": "operator_action", "complete": False},
        {"id": "manual_deploy", "action": "Operator manually deploys the staging service; automatic deploy remains disabled.", "requires": "operator_action", "complete": False},
        {"id": "health_readiness", "action": "After deployment, verify /healthz and /readyz with scripts/verify_staging_http.py.", "requires": "operator_action_and_network", "complete": False},
        {"id": "offline_release_preflight", "action": "Run scripts/verify_first_contact_release_readiness.py with the staging HTTPS origin and conversation default; execution approval variables must remain unset.", "requires": "operator_action", "complete": False},
        {"id": "explicit_user_approval", "action": "Obtain a separate, explicit user approval in the conversation for this exact origin, conversation default, and one operation ID before setting execution gates.", "requires": "explicit_user_approval", "complete": False},
        {"id": "first_contact_and_ack", "action": "Only after approval, configure exact operation-bound gates locally and run scripts/verify_first_contact.py --execute; verify AI-01 send, AI-02 receive, ACK, and pending removal.", "requires": "explicit_user_approval_and_operator_action", "complete": False},
    ]
    return {
        "result": "PASS",
        "blueprint": "valid",
        "authorization": "NOT_GRANTED",
        "network": "NOT_CONTACTED",
        "deployment": "NOT_PERFORMED",
        "realContact": "NOT_STARTED",
        "failures": [],
        "steps": steps,
        "constraints": {
            "plan": "free", "region": "oregon", "deploy": "manual_only",
            "storage": "ephemeral_in_memory", "persistentDisk": False,
            "transport": "HTTP_LONG_POLL",
            "conversationId": "default",
        },
    }


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) == 2 else Path("render.staging.yaml")
    result = build_handoff(path)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
