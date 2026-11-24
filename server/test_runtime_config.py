import os
import unittest

from server.runtime_config import RuntimeConfig

class RuntimeConfigTest(unittest.TestCase):
    def test_required_config(self):
        old = os.environ.get("TEST_RUNTIME_CONFIG")
        os.environ["TEST_RUNTIME_CONFIG"] = "value"
        try:
            self.assertEqual(RuntimeConfig.require("TEST_RUNTIME_CONFIG"), "value")
        finally:
            if old is None:
                os.environ.pop("TEST_RUNTIME_CONFIG", None)
            else:
                os.environ["TEST_RUNTIME_CONFIG"] = old

    def test_missing_required_config_rejected(self):
        os.environ.pop("TEST_RUNTIME_MISSING", None)
        with self.assertRaises(RuntimeError):
            RuntimeConfig.require("TEST_RUNTIME_MISSING")

    def test_defaults_are_bounded(self):
        self.assertEqual(RuntimeConfig.request_timeout_seconds(), 10)
        self.assertEqual(RuntimeConfig.retry_limit(), 2)

    def test_timeout_rejects_invalid_values(self):
        os.environ["MESSENGER_REQUEST_TIMEOUT_SECONDS"] = "0"
        with self.assertRaisesRegex(RuntimeError, "invalid_runtime_config"):
            RuntimeConfig.request_timeout_seconds()

    def test_retry_rejects_invalid_values(self):
        os.environ["MESSENGER_RETRY_LIMIT"] = "6"
        with self.assertRaisesRegex(RuntimeError, "invalid_runtime_config"):
            RuntimeConfig.retry_limit()

    def test_storage_path_rejects_surrounding_whitespace(self):
        os.environ["MESSENGER_DB_PATH"] = " server/data/messenger.sqlite"
        with self.assertRaisesRegex(RuntimeError, "invalid_runtime_config"):
            RuntimeConfig.storage_path()

    def test_auth_tokens_reject_duplicate_credentials_and_identities(self):
        keys = ["MESSENGER_TOKEN_AI_A", "MESSENGER_TOKEN_AI_B",
                "MESSENGER_AI_ID_A", "MESSENGER_AI_ID_B"]
        old = {key: os.environ.get(key) for key in keys}
        try:
            os.environ.update({
                "MESSENGER_TOKEN_AI_A": "secret-a",
                "MESSENGER_TOKEN_AI_B": "secret-b",
                "MESSENGER_AI_ID_A": "AI-A",
                "MESSENGER_AI_ID_B": "AI-B"})
            self.assertEqual(RuntimeConfig.auth_tokens(), {"secret-a": "AI-A", "secret-b": "AI-B"})
            os.environ["MESSENGER_TOKEN_AI_B"] = "secret-a"
            with self.assertRaisesRegex(RuntimeError, "duplicate_ai_tokens"):
                RuntimeConfig.auth_tokens()
            os.environ["MESSENGER_TOKEN_AI_B"] = "secret-b"
            os.environ["MESSENGER_AI_ID_B"] = "AI-A"
            with self.assertRaisesRegex(RuntimeError, "duplicate_ai_ids"):
                RuntimeConfig.auth_tokens()
            os.environ["MESSENGER_AI_ID_B"] = " AI-B"
            with self.assertRaisesRegex(RuntimeError, "invalid_ai_id"):
                RuntimeConfig.auth_tokens()
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_voice_admin_ids_are_optional_and_validated_against_known_ai_ids(self):
        keys = ["MESSENGER_VOICE_ADMIN_AI_IDS"]
        old = {key: os.environ.get(key) for key in keys}
        try:
            os.environ.pop("MESSENGER_VOICE_ADMIN_AI_IDS", None)
            tokens = {"secret-a": "AI-A", "secret-b": "AI-B"}
            self.assertEqual(RuntimeConfig.voice_admin_ids(tokens), frozenset())
            os.environ["MESSENGER_VOICE_ADMIN_AI_IDS"] = "AI-A,AI-B"
            self.assertEqual(RuntimeConfig.voice_admin_ids(tokens), {"AI-A", "AI-B"})
            os.environ["MESSENGER_VOICE_ADMIN_AI_IDS"] = "AI-A,AI-A"
            with self.assertRaisesRegex(RuntimeError, "duplicate_voice_admin_ai_ids"):
                RuntimeConfig.voice_admin_ids(tokens)
            os.environ["MESSENGER_VOICE_ADMIN_AI_IDS"] = "AI-UNKNOWN"
            with self.assertRaisesRegex(RuntimeError, "unknown_voice_admin_ai_id"):
                RuntimeConfig.voice_admin_ids(tokens)
            os.environ["MESSENGER_VOICE_ADMIN_AI_IDS"] = " AI-A"
            with self.assertRaisesRegex(RuntimeError, "MESSENGER_VOICE_ADMIN_AI_IDS"):
                RuntimeConfig.voice_admin_ids(tokens)
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_paid_openai_api_calls_are_disabled_by_default(self):
        old = os.environ.get("OPENAI_API_CALLS_ENABLED")
        try:
            os.environ.pop("OPENAI_API_CALLS_ENABLED", None)
            self.assertFalse(RuntimeConfig.openai_api_calls_enabled())
            os.environ["OPENAI_API_CALLS_ENABLED"] = "true"
            self.assertTrue(RuntimeConfig.openai_api_calls_enabled())
            os.environ["OPENAI_API_CALLS_ENABLED"] = "false"
            self.assertFalse(RuntimeConfig.openai_api_calls_enabled())
            os.environ["OPENAI_API_CALLS_ENABLED"] = "yes"
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_CALLS_ENABLED"):
                RuntimeConfig.openai_api_calls_enabled()
        finally:
            if old is None:
                os.environ.pop("OPENAI_API_CALLS_ENABLED", None)
            else:
                os.environ["OPENAI_API_CALLS_ENABLED"] = old

    def test_openai_defaults_are_present_and_bounded(self):
        self.assertEqual(RuntimeConfig.openai_text_model(), "gpt-6.2-astra")
        self.assertEqual(RuntimeConfig.openai_realtime_model(), "gpt-realtime-2.1")
        self.assertEqual(RuntimeConfig.openai_timeout_seconds(), 45)
        self.assertEqual(RuntimeConfig.openai_max_input_chars(), 12000)
        self.assertIn("GPT-6", RuntimeConfig.openai_instructions())

    def test_openai_timeout_rejects_out_of_range_values(self):
        old = os.environ.get("OPENAI_TIMEOUT_SECONDS")
        try:
            os.environ["OPENAI_TIMEOUT_SECONDS"] = "121"
            with self.assertRaisesRegex(RuntimeError, "OPENAI_TIMEOUT_SECONDS"):
                RuntimeConfig.openai_timeout_seconds()
        finally:
            if old is None:
                os.environ.pop("OPENAI_TIMEOUT_SECONDS", None)
            else:
                os.environ["OPENAI_TIMEOUT_SECONDS"] = old

    def test_openai_input_limit_rejects_out_of_range_values(self):
        old = os.environ.get("OPENAI_MAX_INPUT_CHARS")
        try:
            os.environ["OPENAI_MAX_INPUT_CHARS"] = "99"
            with self.assertRaisesRegex(RuntimeError, "OPENAI_MAX_INPUT_CHARS"):
                RuntimeConfig.openai_max_input_chars()
        finally:
            if old is None:
                os.environ.pop("OPENAI_MAX_INPUT_CHARS", None)
            else:
                os.environ["OPENAI_MAX_INPUT_CHARS"] = old

    def test_auth_tokens_require_all_identity_pairs(self):
        keys = ["MESSENGER_TOKEN_AI_A", "MESSENGER_TOKEN_AI_B", "MESSENGER_AI_ID_A", "MESSENGER_AI_ID_B"]
        old = {key: os.environ.get(key) for key in keys}
        for key in keys:
            os.environ.pop(key, None)
        try:
            with self.assertRaisesRegex(RuntimeError, "missing_runtime_config"):
                RuntimeConfig.auth_tokens()
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


    def test_storage_mode_rejects_unknown_values(self):
        old = os.environ.get("MESSENGER_STORAGE_MODE")
        try:
            os.environ["MESSENGER_STORAGE_MODE"] = "cloud-ish"
            with self.assertRaisesRegex(RuntimeError, "MESSENGER_STORAGE_MODE"):
                RuntimeConfig.storage_mode()
        finally:
            if old is None:
                os.environ.pop("MESSENGER_STORAGE_MODE", None)
            else:
                os.environ["MESSENGER_STORAGE_MODE"] = old

    def test_ephemeral_storage_requires_explicit_staging_opt_in(self):
        keys = ["MESSENGER_STORAGE_MODE", "MESSENGER_DB_PATH",
                "MESSENGER_ENVIRONMENT", "MESSENGER_ALLOW_EPHEMERAL_STAGING"]
        old = {key: os.environ.get(key) for key in keys}
        try:
            os.environ["MESSENGER_STORAGE_MODE"] = "ephemeral"
            os.environ["MESSENGER_DB_PATH"] = ":memory:"
            os.environ.pop("MESSENGER_ENVIRONMENT", None)
            os.environ.pop("MESSENGER_ALLOW_EPHEMERAL_STAGING", None)
            with self.assertRaisesRegex(RuntimeError, "storage_not_durable"):
                RuntimeConfig.validate_storage_contract()
            os.environ["MESSENGER_ENVIRONMENT"] = "production"
            os.environ["MESSENGER_ALLOW_EPHEMERAL_STAGING"] = "true"
            with self.assertRaisesRegex(RuntimeError, "storage_not_durable"):
                RuntimeConfig.validate_storage_contract()
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_ephemeral_storage_allowed_only_with_explicit_staging_opt_in(self):
        keys = ["MESSENGER_STORAGE_MODE", "MESSENGER_DB_PATH",
                "MESSENGER_ENVIRONMENT", "MESSENGER_ALLOW_EPHEMERAL_STAGING"]
        old = {key: os.environ.get(key) for key in keys}
        try:
            os.environ["MESSENGER_STORAGE_MODE"] = "ephemeral"
            os.environ["MESSENGER_DB_PATH"] = ":memory:"
            os.environ["MESSENGER_ENVIRONMENT"] = "staging"
            os.environ["MESSENGER_ALLOW_EPHEMERAL_STAGING"] = "true"
            self.assertEqual(RuntimeConfig.validate_storage_contract(), "ephemeral")
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_ephemeral_staging_opt_in_rejects_invalid_flag(self):
        keys = ["MESSENGER_STORAGE_MODE", "MESSENGER_DB_PATH",
                "MESSENGER_ENVIRONMENT", "MESSENGER_ALLOW_EPHEMERAL_STAGING"]
        old = {key: os.environ.get(key) for key in keys}
        try:
            os.environ["MESSENGER_STORAGE_MODE"] = "ephemeral"
            os.environ["MESSENGER_DB_PATH"] = ":memory:"
            os.environ["MESSENGER_ENVIRONMENT"] = "staging"
            os.environ["MESSENGER_ALLOW_EPHEMERAL_STAGING"] = "yes"
            with self.assertRaisesRegex(RuntimeError, "ALLOW_EPHEMERAL_STAGING"):
                RuntimeConfig.validate_storage_contract()
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_persistent_storage_requires_absolute_root_and_database_inside_it(self):
        import tempfile
        from pathlib import Path
        keys = ["MESSENGER_STORAGE_MODE", "MESSENGER_PERSISTENT_STORAGE_ROOT", "MESSENGER_DB_PATH"]
        old = {key: os.environ.get(key) for key in keys}
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.environ["MESSENGER_STORAGE_MODE"] = "persistent"
                os.environ["MESSENGER_PERSISTENT_STORAGE_ROOT"] = directory
                os.environ["MESSENGER_DB_PATH"] = str(Path(directory) / "messenger.sqlite")
                self.assertEqual(RuntimeConfig.validate_storage_contract(), "persistent")
                os.environ["MESSENGER_DB_PATH"] = str(Path(directory).parent / "outside.sqlite")
                with self.assertRaisesRegex(RuntimeError, "database_outside_persistent_root"):
                    RuntimeConfig.validate_storage_contract()
                os.environ["MESSENGER_PERSISTENT_STORAGE_ROOT"] = "relative/path"
                with self.assertRaisesRegex(RuntimeError, "PERSISTENT_STORAGE_ROOT"):
                    RuntimeConfig.validate_storage_contract()
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

if __name__ == "__main__":
    unittest.main()

# Mission 17 Round 10 verification marker: final Backend Test must run on this HEAD.
