"""Fail-closed contract for optional local model inference.

This module never discovers, downloads, starts, or contacts an engine. A concrete
adapter must be injected by trusted application code and must declare its local
execution boundary before it can be used.
"""
from dataclasses import dataclass


class LocalInferenceError(RuntimeError):
    """Stable, non-sensitive local inference error."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class LocalInferencePolicy:
    enabled: bool = False
    allow_network: bool = False
    allow_model_downloads: bool = False
    max_prompt_chars: int = 8000
    max_output_chars: int = 12000
    max_output_tokens: int = 512


class LocalInferenceController:
    def __init__(self, engine=None, policy: LocalInferencePolicy | None = None):
        self._engine = engine
        self._policy = policy or LocalInferencePolicy()

    def status(self) -> dict:
        engine = self._engine
        eligible = bool(
            self._policy.enabled
            and engine is not None
            and getattr(engine, "runtime_scope", None) == "server_host"
            and getattr(engine, "local_only", False) is True
            and getattr(engine, "network_access", None) == "NONE"
            and getattr(engine, "downloads_allowed", None) is False
            and callable(getattr(engine, "generate", None))
        )
        return {
            "state": "READY_FOR_EXPLICIT_OPT_IN" if eligible else "NOT_CONFIGURED",
            "runtimeScope": "server_host",
            "engineId": getattr(engine, "engine_id", None) if eligible else None,
            "inferenceAvailable": eligible,
            "networkAccess": "NONE",
            "downloadsAllowed": False,
            "policyEnabled": self._policy.enabled,
        }

    def execute(self, prompt: str, *, user_opt_in: bool = False,
                max_output_tokens: int = 256) -> str:
        if not self._policy.enabled:
            raise LocalInferenceError("LOCAL_INFERENCE_DISABLED_BY_POLICY")
        if not user_opt_in:
            raise LocalInferenceError("EXPLICIT_OPT_IN_REQUIRED")
        status = self.status()
        if not status["inferenceAvailable"]:
            raise LocalInferenceError("LOCAL_ENGINE_NOT_CONFIGURED")
        if not isinstance(prompt, str) or not prompt.strip():
            raise LocalInferenceError("PROMPT_REQUIRED")
        if len(prompt) > self._policy.max_prompt_chars:
            raise LocalInferenceError("PROMPT_TOO_LARGE")
        if (not isinstance(max_output_tokens, int) or isinstance(max_output_tokens, bool)
                or not 1 <= max_output_tokens <= self._policy.max_output_tokens):
            raise LocalInferenceError("OUTPUT_LIMIT_INVALID")
        try:
            result = self._engine.generate(
                prompt,
                max_output_tokens=max_output_tokens,
            )
        except Exception:
            raise LocalInferenceError("LOCAL_ENGINE_EXECUTION_FAILED") from None
        if not isinstance(result, str):
            raise LocalInferenceError("LOCAL_ENGINE_INVALID_RESULT")
        if len(result) > self._policy.max_output_chars:
            raise LocalInferenceError("LOCAL_ENGINE_OUTPUT_TOO_LARGE")
        return result
