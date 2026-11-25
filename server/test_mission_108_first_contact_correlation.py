import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_first_contact_config as preflight


class Mission108CorrelationBoundaryTest(unittest.TestCase):
    def test_preflight_rejects_non_origin_urls(self):
        for url in ("https://host.example/path", "https://host.example:bad",
                    "https://user@host.example", "https://host.example?x=1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                preflight.validate(url, "room", "a", "b")

    def test_preflight_never_returns_credentials(self):
        result = preflight.validate("https://host.example", "room", "secret-A", "secret-B")
        self.assertNotIn("secret-A", repr(result))
        self.assertNotIn("secret-B", repr(result))
        self.assertEqual(result["network"], "NOT_CONTACTED")


if __name__ == "__main__":
    unittest.main()
