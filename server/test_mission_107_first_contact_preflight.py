import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_first_contact_config as preflight


class FirstContactPreflightTest(unittest.TestCase):
    def test_valid_configuration_passes_without_network(self):
        result = preflight.validate("https://stage.example/", "room-01", "secret-a", "secret-b")
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["network"], "NOT_CONTACTED")
        self.assertEqual(result["baseUrl"], "https://stage.example")

    def test_rejects_non_https_or_unsafe_url_components(self):
        for value in ("http://stage.example", "https://user:secret@stage.example",
                      "https://stage.example/path", "https://stage.example/?x=1",
                      "https://stage.example/#fragment", "https://stage.example:",
                      "https://stage.example:99999", "https://stage.example:abc",
                      " https://stage.example", "https://stage.example ",
                      "https://stage.example" + chr(10) + ".evil", "https://stage.example/%2f"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "invalid_staging_url"):
                preflight.validate(value, "room", "a", "b")

    def test_rejects_missing_or_duplicate_credentials(self):
        for a, b in (("", "b"), ("a", ""), ("same", "same"), ("   ", "b"), ("a", "  ")):
            with self.subTest(a=a, b=b), self.assertRaisesRegex(ValueError, "distinct_ai_credentials_required"):
                preflight.validate("https://stage.example", "room", a, b)

    def test_requires_fixed_ai_identities(self):
        with self.assertRaisesRegex(ValueError, "fixed_ai_identity_required"):
            preflight.validate("https://stage.example", "room", "a", "b", "AI-A", "AI-B")

    def test_rejects_empty_oversized_or_control_character_conversation_id(self):
        for conversation in ("", "  ", "x" * 201, "room" + chr(10) + "forged"):
            with self.subTest(conversation=conversation), self.assertRaisesRegex(ValueError, "invalid_conversation_id"):
                preflight.validate("https://stage.example", conversation, "a", "b")

    def test_rejects_non_string_values(self):
        with self.assertRaisesRegex(ValueError, "invalid_staging_url"):
            preflight.validate(None, "room", "a", "b")
        with self.assertRaisesRegex(ValueError, "invalid_conversation_id"):
            preflight.validate("https://stage.example", None, "a", "b")

    def test_success_shape_contains_no_credential_material(self):
        result = preflight.validate("https://stage.example", "room", "very-secret-a", "very-secret-b")
        self.assertNotIn("very-secret", str(result))
        self.assertEqual(set(result), {"result","network","ai01Identity","ai02Identity","credentials","conversation","baseUrl"})


if __name__ == "__main__":
    unittest.main()
