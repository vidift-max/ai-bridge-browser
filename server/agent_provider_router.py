"""Explicit server-side provider assignment and readiness for Messenger AI identities."""
import json
import os


class AgentProviderRouter:
    ALLOWED_PROVIDERS = {"openai", "anthropic", "google_gemini"}

    def __init__(self, adapters, assignments=None):
        self._adapters = dict(adapters)
        raw = os.environ.get("MESSENGER_AI_PROVIDER_MAP", "") if assignments is None else assignments
        if isinstance(raw, str):
            try:
                raw = json.loads(raw) if raw.strip() else {}
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid_runtime_config:MESSENGER_AI_PROVIDER_MAP") from exc
        if not isinstance(raw, dict):
            raise ValueError("invalid_runtime_config:MESSENGER_AI_PROVIDER_MAP")
        for ai_id, provider_id in raw.items():
            if (not isinstance(ai_id, str) or not ai_id.startswith("AI-")
                    or len(ai_id) > 66 or not isinstance(provider_id, str)
                    or provider_id not in self.ALLOWED_PROVIDERS):
                raise ValueError("invalid_runtime_config:MESSENGER_AI_PROVIDER_MAP")
        self._assignments = dict(raw)

    def assignment(self, ai_id):
        return self._assignments.get(ai_id)

    def resolve(self, ai_id):
        provider_id = self.assignment(ai_id)
        if provider_id is None:
            return None
        adapter = self._adapters.get(provider_id)
        if adapter is None or not adapter.enabled() or not adapter.api_calls_enabled():
            return None

        def invoke(prompt):
            result = adapter.respond(prompt)
            return {
                "text": result.get("text", ""),
                "providerId": provider_id,
                "model": result.get("model") or getattr(adapter, "model", provider_id),
            }
        return invoke

    def readiness(self, ai_ids):
        result = []
        for ai_id in ai_ids:
            provider_id = self.assignment(ai_id)
            adapter = self._adapters.get(provider_id) if provider_id else None
            configured = bool(adapter is not None and adapter.enabled())
            enabled = bool(configured and adapter.api_calls_enabled())
            result.append({
                "aiId": ai_id,
                "providerId": provider_id,
                "implementation": "AVAILABLE" if adapter is not None else (
                    "NOT_ASSIGNED" if provider_id is None else "NOT_IMPLEMENTED"),
                "configured": configured,
                "apiCallsEnabled": enabled,
                "state": "READY" if enabled else (
                    "DISABLED_BY_POLICY" if configured else "NOT_CONFIGURED"),
            })
        return result
