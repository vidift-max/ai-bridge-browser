"""Offline authorization and ephemeral-staging boundary for first-contact execution."""
from __future__ import annotations


def validate_environment(env: dict[str, str]) -> dict:
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
    return {
        "result": "PASS",
        "authorization": "explicit_staging_and_execution_gates_present",
        "environment": "staging",
        "storage": "ephemeral_in_memory",
        "identities": ["AI-01", "AI-02"],
        "credentials": "present_and_distinct",
        "network": "NOT_CONTACTED",
    }
