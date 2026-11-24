import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_staging_http as verifier


class StagingVerifierTest(unittest.TestCase):
    def test_accepts_https_origin_and_normalizes_trailing_slash(self):
        self.assertEqual(verifier.normalize_base_url("https://stage.example/"),
                         "https://stage.example")

    def test_rejects_http_and_non_http_schemes(self):
        for value in ("http://stage.example", "file:///etc/passwd", "ftp://stage.example"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                verifier.normalize_base_url(value)

    def test_rejects_embedded_credentials(self):
        with self.assertRaises(ValueError):
            verifier.normalize_base_url("https://user:secret@stage.example")

    def test_rejects_path_query_and_fragment(self):
        for value in ("https://stage.example/path", "https://stage.example/?token=x",
                      "https://stage.example/#secret"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                verifier.normalize_base_url(value)

    def test_rejects_missing_host_and_invalid_port(self):
        for value in ("https:///missing-host", "https://stage.example:bad"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                verifier.normalize_base_url(value)

    def test_success_requires_both_health_and_readiness(self):
        with patch.object(verifier, "check", side_effect=[
            (200, {"status": "ok"}), (200, {"status": "ready"})
        ]) as mocked:
            code, result = verifier.verify("https://stage.example")
        self.assertEqual(code, 0)
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(result["baseUrl"], "https://stage.example")

    def test_unready_service_fails(self):
        with patch.object(verifier, "check", side_effect=[
            (200, {"status": "ok"}), (503, {"status": "starting"})
        ]):
            code, _ = verifier.verify("https://stage.example")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
