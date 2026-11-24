"""Safe provider catalog: configuration is not proof of live connectivity."""

class ProviderRegistry:
    def __init__(self, openai_adapter=None):
        self._openai = openai_adapter

    def list_providers(self):
        openai_configured = bool(self._openai is not None and self._openai.enabled())
        return [
            {
                "providerId": "openai",
                "displayName": "OpenAI API",
                "integrationType": "official_api",
                "implementation": "AVAILABLE",
                "identityType": "project_api_credential",
                "credentialSource": "OPENAI_API_KEY",
                "configured": openai_configured,
                "connectionState": "CONFIGURED_UNVERIFIED" if openai_configured else "NOT_CONFIGURED",
                "online": False,
                "accountSessionConnected": False,
                "capabilities": ["text_response", "realtime_client_secret"],
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
