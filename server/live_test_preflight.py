"""Non-networking operator preflight for the first controlled two-AI test.

This module only inspects configuration values and injected runtime state. It
never contacts a provider, enables a policy switch, creates a room, registers
a session, or mutates secrets.
"""
import json
import os


PROVIDERS = {"openai", "anthropic", "google_gemini"}
KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google_gemini": "GEMINI_API_KEY",
}
POLICY_ENV = {
    "openai": "OPENAI_API_CALLS_ENABLED",
    "anthropic": "ANTHROPIC_API_CALLS_ENABLED",
    "google_gemini": "GEMINI_API_CALLS_ENABLED",
}


def _duplicate_rejector(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_provider_assignment")
        result[key] = value
    return result


def parse_assignment_map(raw):
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        value = json.loads(raw, object_pairs_hook=_duplicate_rejector)
    except (TypeError, ValueError):
        raise ValueError("invalid_provider_assignment")
    if not isinstance(value, dict):
        raise ValueError("invalid_provider_assignment")
    for ai_id, provider in value.items():
        if (not isinstance(ai_id, str) or not ai_id.startswith("AI-")
                or len(ai_id) > 66 or not isinstance(provider, str)
                or provider not in PROVIDERS):
            raise ValueError("invalid_provider_assignment")
    return value


def build_preflight(env=None, required_ai_ids=("AI-USER", "AI-PEER")):
    """Return safe, machine-readable readiness; performs no network I/O."""
    env = os.environ if env is None else env
    checks = []
    try:
        assignments = parse_assignment_map(env.get("MESSENGER_AI_PROVIDER_MAP", ""))
        checks.append({"id": "provider_assignment", "ok": True,
                       "state": "OK", "detail": f"{len(assignments)} explicit assignment(s)"})
    except ValueError as exc:
        assignments = {}
        checks.append({"id": "provider_assignment", "ok": False,
                       "state": "INVALID", "detail": str(exc)})

    required = tuple(required_ai_ids)
    missing = [ai_id for ai_id in required if ai_id not in assignments]
    duplicates = len(required) != len(set(required))
    checks.append({"id": "two_ai_assignments", "ok": not missing and not duplicates,
                   "state": "OK" if not missing and not duplicates else "BLOCKED",
                   "detail": "both required AI IDs assigned" if not missing and not duplicates
                             else "missing or duplicate required AI IDs"})

    for ai_id in required:
        provider = assignments.get(ai_id)
        if provider is None:
            checks.append({"id": f"credential:{ai_id}", "ok": False,
                           "state": "BLOCKED", "detail": "provider assignment missing"})
            checks.append({"id": f"policy:{ai_id}", "ok": False,
                           "state": "BLOCKED", "detail": "provider assignment missing"})
            continue
        key_present = bool(env.get(KEY_ENV[provider], "").strip())
        policy_enabled = env.get(POLICY_ENV[provider], "false") == "true"
        checks.append({"id": f"credential:{ai_id}", "ok": key_present,
                       "state": "READY" if key_present else "BLOCKED",
                       "detail": "credential present" if key_present else "credential missing"})
        checks.append({"id": f"policy:{ai_id}", "ok": policy_enabled,
                       "state": "READY" if policy_enabled else "BLOCKED",
                       "detail": "explicit provider-call policy enabled"
                                  if policy_enabled else "provider-call policy disabled"})

    host_key = env.get("AI_PROVIDER_HOST_HMAC_KEY_HEX", "").strip()
    valid_host_key = False
    if host_key:
        try:
            key = bytes.fromhex(host_key)
            valid_host_key = len(key) == 32
        except ValueError:
            valid_host_key = False
    checks.append({"id": "host_hmac_key", "ok": valid_host_key,
                   "state": "READY" if valid_host_key else "BLOCKED",
                   "detail": "32-byte host key present" if valid_host_key
                             else "32-byte host key required"})

    ok = all(item["ok"] for item in checks)
    return {
        "state": "READY_FOR_OPERATOR_ACTIVATION" if ok else "BLOCKED",
        "networkCallsPerformed": False,
        "secretsExposed": False,
        "checks": checks,
    }
