import os

class RuntimeConfig:
    @staticmethod
    def require(name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise RuntimeError(f"missing_runtime_config:{name}")
        return value

    @staticmethod
    def optional(name: str, default=None):
        return os.environ.get(name, default)

    @staticmethod
    def storage_path() -> str:
        value = RuntimeConfig.optional("MESSENGER_DB_PATH", "server/data/messenger.sqlite")
        if not value or value.strip() != value:
            raise RuntimeError("invalid_runtime_config:MESSENGER_DB_PATH")
        return value

    @staticmethod
    def request_timeout_seconds() -> int:
        raw = RuntimeConfig.optional("MESSENGER_REQUEST_TIMEOUT_SECONDS", "10")
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise RuntimeError("invalid_runtime_config:MESSENGER_REQUEST_TIMEOUT_SECONDS")
        if value < 1 or value > 120:
            raise RuntimeError("invalid_runtime_config:MESSENGER_REQUEST_TIMEOUT_SECONDS")
        return value

    @staticmethod
    def retry_limit() -> int:
        raw = RuntimeConfig.optional("MESSENGER_RETRY_LIMIT", "2")
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise RuntimeError("invalid_runtime_config:MESSENGER_RETRY_LIMIT")
        if value < 0 or value > 5:
            raise RuntimeError("invalid_runtime_config:MESSENGER_RETRY_LIMIT")
        return value

    @staticmethod
    def auth_tokens():
        return {
            RuntimeConfig.require("MESSENGER_TOKEN_AI_A"): RuntimeConfig.require("MESSENGER_AI_ID_A"),
            RuntimeConfig.require("MESSENGER_TOKEN_AI_B"): RuntimeConfig.require("MESSENGER_AI_ID_B"),
        }
