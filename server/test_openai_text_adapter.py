import json
import unittest
from unittest.mock import patch

from server.openai_text_adapter import OpenAITextAdapter


class OpenAITextAdapterTest(unittest.TestCase):
    def test_disabled_without_key(self):
        adapter = OpenAITextAdapter(api_key="")
        self.assertFalse(adapter.enabled())

    @patch("server.openai_text_adapter.urllib.request.urlopen")
    def test_builds_responses_request(self, urlopen):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self): return json.dumps({
                "id": "resp_test",
                "status": "completed",
                "model": "gpt-test",
                "output_text": "Olá, eu estou no Messenger."
            }).encode()

        urlopen.return_value = FakeResponse()
        adapter = OpenAITextAdapter(api_key="test-key", model="gpt-test")
        result = adapter.respond("Olá")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(result["responseId"], "resp_test")
        self.assertEqual(result["text"], "Olá, eu estou no Messenger.")

    @patch("server.openai_text_adapter.urllib.request.urlopen")
    def test_previous_response_is_forwarded(self, urlopen):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self):
                return b'{"id":"resp_2","status":"completed","output_text":"ok"}'

        urlopen.return_value = FakeResponse()
        OpenAITextAdapter(api_key="test-key").respond("continua", "resp_1")
        payload = json.loads(urlopen.call_args.args[0].data.decode())
        self.assertEqual(payload["previous_response_id"], "resp_1")


if __name__ == "__main__":
    unittest.main()
