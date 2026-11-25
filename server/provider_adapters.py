"""Independent server-side Anthropic and Gemini text adapters.

All credentials remain in process environment; calls are disabled unless each
provider's explicit policy switch is true. No browser credential path exists.
"""
import json
import os
import urllib.error
import urllib.request
from urllib.parse import quote


class _JsonTextAdapter:
    provider_id = ""

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key if api_key is not None else os.environ.get(self.key_env, "").strip()
        self.model = model or os.environ.get(self.model_env, self.default_model)

    def enabled(self):
        return bool(self.api_key)

    def api_calls_enabled(self):
        return os.environ.get(self.policy_env, "false") == "true"

    def _post(self, url, payload, headers):
        if not self.api_calls_enabled():
            raise RuntimeError(self.provider_id + "_api_calls_disabled")
        if not self.enabled():
            raise RuntimeError(self.provider_id + "_api_not_configured")
        request = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json", "Accept": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(self.provider_id + "_http_" + str(exc.code)) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(self.provider_id + "_transport_error") from exc
        except (ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError(self.provider_id + "_invalid_response") from exc
        text = self._extract_text(data)
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError(self.provider_id + "_empty_output")
        return {"responseId": data.get("id"), "model": data.get("model", self.model),
                "text": text.strip()}

    def _extract_text(self, data):
        raise NotImplementedError


class AnthropicTextAdapter(_JsonTextAdapter):
    provider_id = "anthropic"
    key_env = "ANTHROPIC_API_KEY"
    model_env = "ANTHROPIC_TEXT_MODEL"
    policy_env = "ANTHROPIC_API_CALLS_ENABLED"
    default_model = "claude-sonnet-4-5"

    def respond(self, prompt):
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 5000:
            raise ValueError("invalid_prompt")
        return self._post(
            "https://api.anthropic.com/v1/messages",
            {"model": self.model, "max_tokens": 2048,
             "messages": [{"role": "user", "content": prompt.strip()}]},
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"})

    def _extract_text(self, data):
        blocks = data.get("content", [])
        return "\\n".join(item.get("text", "") for item in blocks
                           if isinstance(item, dict) and item.get("type") == "text")


class GeminiTextAdapter(_JsonTextAdapter):
    provider_id = "google_gemini"
    key_env = "GEMINI_API_KEY"
    model_env = "GEMINI_TEXT_MODEL"
    policy_env = "GEMINI_API_CALLS_ENABLED"
    default_model = "gemini-2.5-flash"

    def respond(self, prompt):
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 5000:
            raise ValueError("invalid_prompt")
        return self._post(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + quote(self.model, safe="") + ":generateContent",
            {"contents": [{"parts": [{"text": prompt.strip()}]}]},
            {"x-goog-api-key": self.api_key})

    def _extract_text(self, data):
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "\\n".join(item.get("text", "") for item in parts
                           if isinstance(item, dict) and isinstance(item.get("text"), str))
