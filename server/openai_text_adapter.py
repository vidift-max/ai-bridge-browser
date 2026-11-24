import json
import urllib.error
import urllib.request
from typing import Optional

from server.runtime_config import RuntimeConfig


class OpenAITextAdapter:
    """Server-side OpenAI Responses adapter. Disabled until an API key is configured."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else RuntimeConfig.openai_api_key()
        self.model = model or RuntimeConfig.openai_text_model()

    def enabled(self) -> bool:
        return bool(self.api_key)

    def respond(self, user_text: str, previous_response_id: Optional[str] = None) -> dict:
        if not self.enabled():
            raise RuntimeError("openai_api_not_configured")
        if not isinstance(user_text, str) or not user_text.strip():
            raise ValueError("message_required")
        if len(user_text) > RuntimeConfig.openai_max_input_chars():
            raise ValueError("message_too_large")

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
            detail = exc.read().decode("utf-8", errors="replace")[:2000]
            raise RuntimeError("openai_http_" + str(exc.code) + ":" + detail) from exc
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
        return {"responseId": data.get("id"), "model": data.get("model", self.model), "text": text.strip()}
