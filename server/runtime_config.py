import os
from pathlib import Path

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
    def storage_mode() -> str:
        value = RuntimeConfig.optional("MESSENGER_STORAGE_MODE", "local")
        if value not in ("local", "persistent", "ephemeral"):
            raise RuntimeError("invalid_runtime_config:MESSENGER_STORAGE_MODE")
        return value

    @staticmethod
    def persistent_storage_root() -> str:
        value = RuntimeConfig.require("MESSENGER_PERSISTENT_STORAGE_ROOT")
        if value.strip() != value or not Path(value).is_absolute():
            raise RuntimeError("invalid_runtime_config:MESSENGER_PERSISTENT_STORAGE_ROOT")
        return value

    @staticmethod
    def validate_storage_contract() -> str:
        mode = RuntimeConfig.storage_mode()
        db_path = Path(RuntimeConfig.storage_path()).resolve()
        if mode == "ephemeral":
            raise RuntimeError("storage_not_durable:ephemeral")
        if mode == "persistent":
            root = Path(RuntimeConfig.persistent_storage_root()).resolve()
            if not root.is_dir() or not os.access(str(root), os.W_OK):
                raise RuntimeError("invalid_runtime_config:persistent_storage_root_unavailable")
            try:
                relative = db_path.relative_to(root)
            except ValueError:
                raise RuntimeError("invalid_runtime_config:database_outside_persistent_root")
            if not relative.parts:
                raise RuntimeError("invalid_runtime_config:database_path_must_be_file")
        return mode

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
        token_a = RuntimeConfig.require("MESSENGER_TOKEN_AI_A")
        token_b = RuntimeConfig.require("MESSENGER_TOKEN_AI_B")
        ai_a = RuntimeConfig.require("MESSENGER_AI_ID_A")
        ai_b = RuntimeConfig.require("MESSENGER_AI_ID_B")
        if token_a == token_b:
            raise RuntimeError("invalid_runtime_config:duplicate_ai_tokens")
        if ai_a == ai_b:
            raise RuntimeError("invalid_runtime_config:duplicate_ai_ids")
        for ai_id in (ai_a, ai_b):
            if ai_id.strip() != ai_id or not ai_id.startswith("AI-") or len(ai_id) > 66:
                raise RuntimeError("invalid_runtime_config:invalid_ai_id")
        return {token_a: ai_a, token_b: ai_b}
