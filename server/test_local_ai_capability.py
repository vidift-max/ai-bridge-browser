import unittest
from pathlib import Path


class LocalAICapabilityContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = (Path(__file__).resolve().parent.parent / "web" / "local-ai-capability.js").read_text(encoding="utf-8")

    def test_probe_is_read_only_and_has_no_network_calls(self):
        self.assertNotIn("fetch(", self.script)
        self.assertNotIn("XMLHttpRequest", self.script)
        self.assertNotIn("localStorage", self.script)
        self.assertNotIn("sessionStorage", self.script)

    def test_probe_checks_wifi_and_secure_context(self):
        self.assertIn("AIBridgeWifiOnly.readState()", self.script)
        self.assertIn("root.isSecureContext === true", self.script)
        self.assertIn("network.allowed", self.script)

    def test_probe_checks_webgpu_adapter(self):
        self.assertIn("nav.gpu.requestAdapter", self.script)
        self.assertIn("WEBGPU_ADAPTER_UNAVAILABLE", self.script)

    def test_probe_never_claims_model_loaded_or_inference(self):
        self.assertIn("modelLoaded: false", self.script)
        self.assertIn("downloadStarted: false", self.script)
        self.assertIn("inferenceStarted: false", self.script)


if __name__ == "__main__":
    unittest.main()
