"""Explicit per-agent provider identity bindings without storing provider secrets.

This registry is a configuration contract only. It never contains API keys,
browser cookies, provider account sessions, or proof of live connectivity.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentProviderBinding:
    ai_id: str
    provider_id: str
    credential_ref: str
    model: str | None = None
    enabled: bool = False


class AgentProviderBindingRegistry:
    def __init__(self, supported_provider_ids=None):
        self._supported = set(supported_provider_ids or ())
        self._bindings = {}

    def bind(self, ai_id, provider_id, credential_ref, model=None, enabled=False):
        if not isinstance(ai_id, str) or not ai_id.startswith("AI-"):
            raise ValueError("invalid_ai_id")
        if provider_id not in self._supported:
            raise ValueError("provider_not_supported")
        if not isinstance(credential_ref, str) or not credential_ref.strip():
            raise ValueError("credential_reference_required")
        if not isinstance(enabled, bool):
            raise ValueError("invalid_enabled")
        binding = AgentProviderBinding(ai_id, provider_id, credential_ref.strip(), model, enabled)
        self._bindings[ai_id] = binding
        return binding

    def unbind(self, ai_id):
        return self._bindings.pop(ai_id, None)

    def get(self, ai_id):
        return self._bindings.get(ai_id)

    def list(self):
        return [self._bindings[key] for key in sorted(self._bindings)]

    def resolve_enabled(self, ai_id):
        binding = self.get(ai_id)
        if binding is None or not binding.enabled:
            return None
        return binding
