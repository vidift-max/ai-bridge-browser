"""Safe provider catalog: configuration is not proof of live connectivity."""


class ProviderRegistry:
    def __init__(self, openai_adapter=None):
        self._openai = openai_adapter

    def list_providers(self):
        openai_configured = bool(self._openai is not None and self._openai.enabled())
        status = {}
        if self._openai is not None and hasattr(self._openai, "connection_status"):
            status = self._openai.connection_status()
        api_calls_enabled = bool(
            self._openai is not None
            and hasattr(self._openai, "api_calls_enabled")
            and self._openai.api_calls_enabled()
        )
        openai_state = status.get(
            "connectionState",
            "DISABLED_BY_POLICY" if not api_calls_enabled else (
                "CONFIGURED_UNVERIFIED" if openai_configured else "NOT_CONFIGURED"
            ),
        )
        return [
            {
                "providerId": "openai",
                "displayName": "OpenAI API",
                "integrationType": "official_api",
                "implementation": "AVAILABLE",
                "identityType": "project_api_credential",
                "credentialSource": "OPENAI_API_KEY",
                "configured": openai_configured,
                "apiCallsEnabled": api_calls_enabled,
                "connectionState": openai_state,
                "lastSuccessfulRequestAt": status.get("lastSuccessfulRequestAt"),
                "lastResponseId": status.get("lastResponseId"),
                "lastSuccessfulModel": status.get("lastSuccessfulModel"),
                "online": False,
                "accountSessionConnected": False,
                "capabilities": ["text_response", "realtime_client_secret"] if api_calls_enabled else [],
            },
            {
                "providerId": "anthropic",
                "displayName": "Anthropic Claude API",
                "integrationType": "official_api",
                "implementation": "NOT_IMPLEMENTED",
                "identityType": "console_api_credential",
                "credentialSource": "ANTHROPIC_API_KEY",
                "configured": False,
                "connectionState": "NOT_IMPLEMENTED",
                "online": False,
                "accountSessionConnected": False,
                "capabilities": [],
            },
            {
                "providerId": "google_gemini",
                "displayName": "Google Gemini API",
                "integrationType": "official_api",
                "implementation": "NOT_IMPLEMENTED",
                "identityType": "developer_api_credential",
                "credentialSource": "GEMINI_API_KEY",
                "configured": False,
                "connectionState": "NOT_IMPLEMENTED",
                "online": False,
                "accountSessionConnected": False,
                "capabilities": [],
            },
        ]

    def get_provider(self, provider_id):
        for provider in self.list_providers():
            if provider["providerId"] == provider_id:
                return dict(provider)
        raise ValueError("provider_not_supported")
