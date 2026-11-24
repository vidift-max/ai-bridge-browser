import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from threading import Lock
from typing import Optional

from server.runtime_config import RuntimeConfig


class OpenAITextAdapter:
    """Server-side OpenAI Responses adapter with request-scoped proof metadata."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else RuntimeConfig.openai_api_key()
        self.model = model or RuntimeConfig.openai_text_model()
        self._state_lock = Lock()
        self._last_success_at = None
        self._last_response_id = None
        self._last_model = None

    def enabled(self) -> bool:
        return bool(self.api_key)

    def api_calls_enabled(self) -> bool:
        return RuntimeConfig.openai_api_calls_enabled()

    def connection_status(self) -> dict:
        """Return metadata for the most recent successful request, never a live-session claim."""
        with self._state_lock:
            verified = self._last_success_at is not None
            return {
                "connectionState": "REQUEST_SUCCEEDED" if verified else (
                    "DISABLED_BY_POLICY" if not self.api_calls_enabled() else (
                        "CONFIGURED_UNVERIFIED" if self.enabled() else "NOT_CONFIGURED"
                    )
                ),
                "lastSuccessfulRequestAt": self._last_success_at,
                "lastResponseId": self._last_response_id,
                "lastSuccessfulModel": self._last_model,
                "online": False,
                "accountSessionConnected": False,
            }

    def _record_success(self, response_id, model):
        with self._state_lock:
            self._last_success_at = datetime.now(timezone.utc).isoformat()
            self._last_response_id = response_id
            self._last_model = model

    def create_realtime_client_secret(self) -> dict:
        if not self.api_calls_enabled():
            raise RuntimeError("openai_api_calls_disabled")
        if not self.enabled():
            raise RuntimeError("openai_api_not_configured")
        payload = {
            "expires_after": {"seconds": 600},
            "session": {
                "type": "realtime",
                "model": RuntimeConfig.openai_realtime_model(),
                "instructions": RuntimeConfig.openai_instructions(),
                "output_modalities": ["audio"],
            },
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/realtime/client_secrets",
            data=body,
            headers={
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=RuntimeConfig.openai_timeout_seconds()) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError("openai_http_" + str(exc.code)) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError("openai_transport_error") from exc
        if not data.get("value"):
            raise RuntimeError("openai_client_secret_missing")
        return {
            "clientSecret": data["value"],
            "expiresAt": data.get("expires_at"),
            "session": data.get("session"),
        }

    def respond(self, user_text: str, previous_response_id: Optional[str] = None) -> dict:
        if not self.api_calls_enabled():
            raise RuntimeError("openai_api_calls_disabled")
        if not self.enabled():
            raise RuntimeError("openai_api_not_configured")
        if not isinstance(user_text, str) or not user_text.strip():
            raise ValueError("message_required")
        if len(user_text) > RuntimeConfig.openai_max_input_chars():
            raise ValueError("message_too_large")
        if previous_response_id is not None:
            if (not isinstance(previous_response_id, str)
                    or not previous_response_id.strip()
                    or len(previous_response_id) > 256):
                raise ValueError("invalid_previous_response_id")

        payload = {
            "model": self.model,
            "instructions": RuntimeConfig.openai_instructions(),
            "input": user_text.strip(),
            "store": True,
        }
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id

        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            headers={
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=RuntimeConfig.openai_timeout_seconds()) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError("openai_http_" + str(exc.code)) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError("openai_transport_error") from exc
        except (ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("openai_invalid_response") from exc

        if data.get("status") not in (None, "completed"):
            raise RuntimeError("openai_response_not_completed")
        text = data.get("output_text")
        if not isinstance(text, str) or not text.strip():
            for item in data.get("output", []):
                if item.get("type") == "message":
                    for content in item.get("content", []):
                        if content.get("type") == "output_text" and content.get("text"):
                            text = content["text"]
                            break
                if isinstance(text, str) and text.strip():
                    break
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("openai_empty_output")
        result = {
            "responseId": data.get("id"),
            "model": data.get("model", self.model),
            "text": text.strip(),
        }
        self._record_success(result["responseId"], result["model"])
        return result
