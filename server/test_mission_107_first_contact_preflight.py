import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_first_contact_config as preflight


class FirstContactPreflightTest(unittest.TestCase):
    def test_valid_configuration_passes_without_network(self):
        result = preflight.validate(
            "https://stage.example/", "room-01", "secret-a", "secret-b"
        )
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["network"], "NOT_CONTACTED")
        self.assertEqual(result["baseUrl"], "https://stage.example")

    def test_rejects_non_https_or_credentials_in_url(self):
        for value in (
            "http://stage.example", "https://user:secret@stage.example",
            "https://stage.example/path", "https://stage.example/?x=1",
        ):
            with self.subTest(value=value), self.assertRaisesRegex(
                ValueError, "invalid_staging_url"
            ):
                preflight.validate(value, "room", "a", "b")

    def test_rejects_missing_or_duplicate_credentials(self):
        for a, b in (("", "b"), ("a", ""), ("same", "same")):
            with self.subTest(a=a, b=b), self.assertRaisesRegex(
                ValueError, "distinct_ai_credentials_required"
            ):
                preflight.validate("https://stage.example", "room", a, b)

    def test_requires_fixed_ai_identities(self):
        with self.assertRaisesRegex(ValueError, "fixed_ai_identity_required"):
            preflight.validate(
                "https://stage.example", "room", "a", "b", "AI-A", "AI-B"
            )

    def test_rejects_empty_or_oversized_conversation_id(self):
        for conversation in ("", "x" * 201):
            with self.subTest(conversation=conversation), self.assertRaisesRegex(
                ValueError, "invalid_conversation_id"
            ):
                preflight.validate("https://stage.example", conversation, "a", "b")


if __name__ == "__main__":
    unittest.main()
