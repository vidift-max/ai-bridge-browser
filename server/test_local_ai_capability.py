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

    def test_wifi_policy_fails_closed_for_unknown_or_non_wifi_networks(self):
        policy = (Path(__file__).resolve().parent.parent / "web" / "wifi-only.js").read_text(encoding="utf-8")
        self.assertIn("var allowed = online && type === \"wifi\"", policy)
        self.assertIn('"unknown"', policy)
        self.assertIn('"WIFI_STATUS_UNAVAILABLE"', policy)
        self.assertIn("function assertAllowed()", policy)
        self.assertNotIn("fetch(", policy)

    def test_probe_checks_wifi_and_secure_context(self):
        self.assertIn("AIBridgeWifiOnly.readState()", self.script)
        self.assertIn("root.isSecureContext === true", self.script)
        self.assertIn("network.allowed", self.script)

    def test_probe_checks_webgpu_adapter(self):
        self.assertIn("nav.gpu.requestAdapter", self.script)
        self.assertIn("WEBGPU_ADAPTER_UNAVAILABLE", self.script)

    def test_probe_never_downloads_or_contacts_external_model_services(self):
        self.assertNotIn("fetch(", self.script)
        self.assertNotIn("XMLHttpRequest", self.script)
        self.assertNotIn("WebSocket", self.script)
        self.assertNotIn("SpeechRecognition.install(", self.script)

    def test_probe_never_claims_model_loaded_or_inference(self):
        self.assertIn("modelLoaded: false", self.script)
        self.assertIn("downloadStarted: false", self.script)
        self.assertIn("inferenceStarted: false", self.script)

    def test_messenger_guards_api_and_microphone_with_wifi_gate(self):
        page = (Path(__file__).resolve().parent.parent / "web" / "gpt6-messenger.html").read_text(encoding="utf-8")
        api_start = page.index("async function api(")
        fetch_call = page.index("await fetch(path", api_start)
        self.assertLess(page.index("window.AIBridgeWifiOnly.assertAllowed()", api_start), fetch_call)
        microphone_start = page.index("micEl.onclick=")
        microphone_end = page.index("stopVoiceEl.onclick=", microphone_start)
        microphone_handler = page[microphone_start:microphone_end]
        self.assertIn("window.AIBridgeWifiOnly.assertAllowed()", microphone_handler)
        self.assertIn("recognition.start()", microphone_handler)
        self.assertLess(
            microphone_handler.index("window.AIBridgeWifiOnly.assertAllowed()"),
            microphone_handler.index("recognition.start()"))

    def test_microphone_requires_verified_on_device_recognition(self):
        page = (Path(__file__).resolve().parent.parent / "web" / "gpt6-messenger.html").read_text(encoding="utf-8")
        self.assertIn("recognition.processLocally=true", page)
        self.assertIn("SpeechRecognition.available({langs:['pt-BR'],processLocally:true})", page)
        self.assertIn("recognition.processLocally!==true", page)
        self.assertIn("!localSpeechReady", page)
        self.assertNotIn("SpeechRecognition.install(", page)


if __name__ == "__main__":
    unittest.main()
