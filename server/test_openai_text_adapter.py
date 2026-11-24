import json
import unittest
from unittest.mock import patch

from server.openai_text_adapter import OpenAITextAdapter


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class OpenAITextAdapterTest(unittest.TestCase):
    def test_paid_api_calls_are_blocked_by_default_before_network(self):
        adapter = OpenAITextAdapter(api_key="unit-secret")
        with patch("server.openai_text_adapter.urllib.request.urlopen") as urlopen:
            with self.assertRaisesRegex(RuntimeError, "openai_api_calls_disabled"):
                adapter.respond("hello")
            with self.assertRaisesRegex(RuntimeError, "openai_api_calls_disabled"):
                adapter.create_realtime_client_secret()
            urlopen.assert_not_called()

    def test_disabled_without_key(self):
        self.assertFalse(OpenAITextAdapter(api_key="").enabled())

    def test_configured_key_is_not_a_verified_request(self):
        state = OpenAITextAdapter(api_key="unit-secret").connection_status()
        self.assertEqual(state["connectionState"], "DISABLED_BY_POLICY")
        self.assertFalse(state["online"])
        self.assertFalse(state["accountSessionConnected"])

    @patch("server.openai_text_adapter.urllib.request.urlopen")
    def test_successful_response_records_request_proof_without_online_claim(self, urlopen):
        urlopen.return_value = FakeResponse({
            "id": "resp_test_123", "model": "test-model",
            "status": "completed", "output_text": "Resposta de teste",
        })
        adapter = OpenAITextAdapter(api_key="unit-secret", model="test-model")
        with patch("server.openai_text_adapter.RuntimeConfig.openai_api_calls_enabled", return_value=True):
            result = adapter.respond("Responda apenas teste")
        self.assertEqual(result["text"], "Resposta de teste")
        self.assertEqual(result["responseId"], "resp_test_123")
        state = adapter.connection_status()
        self.assertEqual(state["connectionState"], "REQUEST_SUCCEEDED")
        self.assertEqual(state["lastResponseId"], "resp_test_123")
        self.assertTrue(state["lastSuccessfulRequestAt"])
        self.assertFalse(state["online"])
        self.assertFalse(state["accountSessionConnected"])

    @patch("server.openai_text_adapter.urllib.request.urlopen")
    def test_request_uses_server_side_bearer_and_responses_endpoint(self, urlopen):
        urlopen.return_value = FakeResponse({
            "id": "resp_test_456", "model": "test-model",
            "status": "completed", "output_text": "ok",
        })
        with patch("server.openai_text_adapter.RuntimeConfig.openai_api_calls_enabled", return_value=True):
            OpenAITextAdapter(api_key="unit-secret", model="test-model").respond("hello")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(request.get_header("Authorization"), "Bearer unit-secret")
        self.assertEqual(json.loads(request.data)["input"], "hello")

    def test_empty_message_is_rejected_before_network(self):
        adapter = OpenAITextAdapter(api_key="unit-secret")
        with patch("server.openai_text_adapter.urllib.request.urlopen") as urlopen:
            with patch("server.openai_text_adapter.RuntimeConfig.openai_api_calls_enabled", return_value=True):
                with self.assertRaisesRegex(ValueError, "message_required"):
                    adapter.respond("  ")
            urlopen.assert_not_called()

    def test_oversized_message_is_rejected_before_network(self):
        adapter = OpenAITextAdapter(api_key="unit-secret")
        with patch("server.openai_text_adapter.RuntimeConfig.openai_max_input_chars", return_value=100):
            with patch("server.openai_text_adapter.urllib.request.urlopen") as urlopen:
                with patch("server.openai_text_adapter.RuntimeConfig.openai_api_calls_enabled", return_value=True):
                    with self.assertRaisesRegex(ValueError, "message_too_large"):
                        adapter.respond("x" * 101)
                urlopen.assert_not_called()

    def test_invalid_previous_response_id_is_rejected(self):
        adapter = OpenAITextAdapter(api_key="unit-secret")
        with self.assertRaisesRegex(ValueError, "invalid_previous_response_id"):
            with patch("server.openai_text_adapter.RuntimeConfig.openai_api_calls_enabled", return_value=True):
                adapter.respond("hello", " ")

    @patch("server.openai_text_adapter.urllib.request.urlopen")
    def test_incomplete_upstream_response_does_not_record_success(self, urlopen):
        urlopen.return_value = FakeResponse({
            "id": "resp_incomplete", "status": "in_progress", "output_text": "",
        })
        adapter = OpenAITextAdapter(api_key="unit-secret")
        with self.assertRaisesRegex(RuntimeError, "openai_response_not_completed"):
            with patch("server.openai_text_adapter.RuntimeConfig.openai_api_calls_enabled", return_value=True):
                adapter.respond("hello")
        self.assertEqual(adapter.connection_status()["connectionState"], "DISABLED_BY_POLICY")


if __name__ == "__main__":
    unittest.main()
