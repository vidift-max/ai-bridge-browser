import os

class RuntimeConfig:
    @staticmethod
    def require(name: str) -> str:
        value=os.environ.get(name)
        if not value:
            raise RuntimeError(f"missing_runtime_config:{name}")
        return value

    @staticmethod
    def optional(name: str, default=None):
        return os.environ.get(name, default)

    @staticmethod
    def storage_path() -> str:
        return RuntimeConfig.optional("MESSENGER_DB_PATH", "server/data/messenger.sqlite")

    @staticmethod
    def auth_tokens():
        return {
            RuntimeConfig.require("MESSENGER_TOKEN_AI_A"): RuntimeConfig.require("MESSENGER_AI_ID_A"),
            RuntimeConfig.require("MESSENGER_TOKEN_AI_B"): RuntimeConfig.require("MESSENGER_AI_ID_B"),
        }
