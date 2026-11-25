"""Safe provider catalog: configuration is not proof of live connectivity."""


class ProviderRegistry:
    METADATA = {
        "openai": ("OpenAI API", "project_api_credential", "OPENAI_API_KEY"),
        "anthropic": ("Anthropic Claude API", "console_api_credential", "ANTHROPIC_API_KEY"),
        "google_gemini": ("Google Gemini API", "developer_api_credential", "GEMINI_API_KEY"),
    }

    def __init__(self, openai_adapter=None, adapters=None):
        self._adapters = dict(adapters or {})
        if openai_adapter is not None:
            self._adapters["openai"] = openai_adapter

    def list_providers(self):
        providers = []
        for provider_id, (name, identity_type, credential_source) in self.METADATA.items():
            adapter = self._adapters.get(provider_id)
            configured = bool(adapter is not None and adapter.enabled())
            enabled = bool(configured and adapter.api_calls_enabled())
            status = (adapter.connection_status()
                      if adapter is not None and hasattr(adapter, "connection_status") else {})
            state = status.get("connectionState") or (
                "NOT_CONFIGURED" if not configured else (
                    "CONFIGURED_UNVERIFIED" if enabled else "DISABLED_BY_POLICY"))
            providers.append({
                "providerId": provider_id, "displayName": name,
                "integrationType": "official_api", "implementation": "AVAILABLE" if adapter is not None else "NOT_IMPLEMENTED",
                "identityType": identity_type, "credentialSource": credential_source,
                "configured": configured, "apiCallsEnabled": enabled,
                "connectionState": state,
                "lastSuccessfulRequestAt": status.get("lastSuccessfulRequestAt"),
                "lastResponseId": status.get("lastResponseId"),
                "lastSuccessfulModel": status.get("lastSuccessfulModel"),
                "online": False, "accountSessionConnected": False,
                "capabilities": (["text_response", "realtime_client_secret"] if provider_id == "openai" else ["text_response"]) if enabled else [],
            })
        return providers

    def get_provider(self, provider_id):
        for provider in self.list_providers():
            if provider["providerId"] == provider_id:
                return dict(provider)
        raise ValueError("provider_not_supported")
