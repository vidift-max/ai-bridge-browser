import unittest

from server.staging_config_validator import validate_staging_environment, assert_staging_environment

class StagingConfigValidatorTest(unittest.TestCase):
    def valid(self):
        return {
            "MESSENGER_TOKEN_AI_A": "a",
            "MESSENGER_TOKEN_AI_B": "b",
            "MESSENGER_AI_ID_A": "AI-A",
            "MESSENGER_AI_ID_B": "AI-B",
            "MESSENGER_DB_PATH": "server/data/messenger.sqlite",
            "MESSENGER_REQUEST_TIMEOUT_SECONDS": "10",
            "MESSENGER_RETRY_LIMIT": "2",
        }

    def test_valid_configuration(self):
        env = self.valid()
        self.assertEqual(validate_staging_environment(env), ())
        self.assertTrue(assert_staging_environment(env))

    def test_missing_secret_is_rejected(self):
        env = self.valid()
        del env["MESSENGER_TOKEN_AI_A"]
        self.assertIn("missing:MESSENGER_TOKEN_AI_A", validate_staging_environment(env))

    def test_invalid_timeout_is_rejected(self):
        env = self.valid()
        env["MESSENGER_REQUEST_TIMEOUT_SECONDS"] = "121"
        self.assertIn("invalid:MESSENGER_REQUEST_TIMEOUT_SECONDS", validate_staging_environment(env))

    def test_invalid_retry_is_rejected(self):
        env = self.valid()
        env["MESSENGER_RETRY_LIMIT"] = "-1"
        self.assertIn("invalid:MESSENGER_RETRY_LIMIT", validate_staging_environment(env))

    def test_invalid_storage_path_is_rejected(self):
        env = self.valid()
        env["MESSENGER_DB_PATH"] = " server/data/messenger.sqlite"
        self.assertIn("invalid:MESSENGER_DB_PATH", validate_staging_environment(env))

    def test_assertion_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "staging_configuration_invalid"):
            assert_staging_environment({})

if __name__ == "__main__":
    unittest.main()
