import sys
import unittest
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
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

    def test_rejects_missing_host_invalid_port_and_control_whitespace(self):
        for value in ("https:///missing-host", "https://stage.example:bad", "https://stage.example:",
                      "https://stage.example\n.evil", " https://stage.example"):
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

    def test_invalid_utf8_and_invalid_json_are_rejected_without_exception(self):
        self.assertEqual(verifier._json_object(b"\xff"), {"error": "invalid_json_response"})
        self.assertEqual(verifier._json_object(b"{broken"), {"error": "invalid_json_response"})

    def test_non_object_json_is_rejected(self):
        self.assertEqual(verifier._json_object(b"[]"), {"error": "json_object_required"})

    def test_health_response_redacts_arbitrary_fields(self):
        with patch.object(verifier, "urlopen") as mocked:
            mocked.return_value.__enter__.return_value.status = 200
            mocked.return_value.__enter__.return_value.read.return_value = (
                b'{"status":"ok","token":"secret-value","debug":"private"}'
            )
            status, body = verifier.check("https://stage.example", "/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"status": "ok"})
        self.assertNotIn("secret-value", str(body))

    def test_http_error_body_is_never_returned(self):
        error = HTTPError("https://stage.example/readyz", 502, "Bad Gateway", {},
                          BytesIO(b'{"token":"secret-value"}'))
        with patch.object(verifier, "urlopen", side_effect=error):
            status, body = verifier.check("https://stage.example", "/readyz")
        self.assertEqual(status, 502)
        self.assertEqual(body, {"error": "http_error"})
        self.assertNotIn("secret-value", str(body))

    def test_http_error_with_invalid_utf8_returns_sanitized_body(self):
        error = HTTPError("https://stage.example/healthz", 502, "Bad Gateway", {}, BytesIO(b"\xff"))
        with patch.object(verifier, "urlopen", side_effect=error):
            status, body = verifier.check("https://stage.example", "/healthz")
        self.assertEqual(status, 502)
        self.assertEqual(body, {"error": "invalid_json_response"})


if __name__ == "__main__":
    unittest.main()
