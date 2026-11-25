"""Offline, operation-bound authorization boundary for first-contact execution."""
from __future__ import annotations

import re


def validate_environment(env: dict[str, str], base_url: str | None = None,
                         conversation_id: str | None = None,
                         operation_id: str | None = None) -> dict:
    if env.get("MESSENGER_FIRST_CONTACT_STAGING_AUTHORIZED") != "true":
        raise ValueError("explicit_staging_authorization_required")
    if env.get("MESSENGER_FIRST_CONTACT_EXECUTE") != "true":
        raise ValueError("explicit_execution_gate_required")
    if env.get("MESSENGER_ENVIRONMENT") != "staging":
        raise ValueError("staging_environment_required")
    if env.get("MESSENGER_ALLOW_EPHEMERAL_STAGING") != "true":
        raise ValueError("ephemeral_staging_opt_in_required")
    if env.get("MESSENGER_STORAGE_MODE") != "ephemeral":
        raise ValueError("ephemeral_storage_required")
    if env.get("MESSENGER_DB_PATH") != ":memory:":
        raise ValueError("in_memory_database_required")
    if env.get("MESSENGER_AI_ID_A", "AI-01") != "AI-01" or env.get("MESSENGER_AI_ID_B", "AI-02") != "AI-02":
        raise ValueError("fixed_ai_identity_required")
    token_a, token_b = env.get("MESSENGER_TOKEN_AI_A", ""), env.get("MESSENGER_TOKEN_AI_B", "")
    if not token_a.strip() or not token_b.strip() or token_a == token_b:
        raise ValueError("distinct_ai_credentials_required")

    if not isinstance(base_url, str) or not base_url.startswith("https://"):
        raise ValueError("approved_origin_binding_required")
    if not isinstance(conversation_id, str) or not conversation_id:
        raise ValueError("approved_conversation_binding_required")
    if (not isinstance(operation_id, str)
            or not re.fullmatch(r"[A-Za-z0-9._-]{16,128}", operation_id)):
        raise ValueError("approved_operation_binding_required")
    bindings = (
        ("MESSENGER_FIRST_CONTACT_APPROVED_ORIGIN", base_url, "approved_origin_mismatch"),
        ("MESSENGER_FIRST_CONTACT_APPROVED_CONVERSATION_ID", conversation_id,
         "approved_conversation_mismatch"),
        ("MESSENGER_FIRST_CONTACT_APPROVED_OPERATION_ID", operation_id,
         "approved_operation_mismatch"),
    )
    for key, expected, error in bindings:
        if env.get(key) != expected:
            raise ValueError(error)

    return {
        "result": "PASS",
        "authorization": "explicit_gates_and_exact_operation_bindings_present",
        "environment": "staging",
        "storage": "ephemeral_in_memory",
        "identities": ["AI-01", "AI-02"],
        "credentials": "present_and_distinct",
        "network": "NOT_CONTACTED",
    }
