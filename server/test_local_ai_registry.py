import unittest
from server.local_ai_registry import LocalAIRegistry


class LocalAIRegistryTest(unittest.TestCase):
    def test_catalog_is_zero_cost_and_does_not_claim_inference(self):
        engines = LocalAIRegistry.list_engines()
        self.assertEqual([item["engineId"] for item in engines],
                         ["browser-webgpu", "ollama", "llama-cpp"])
        for engine in engines:
            self.assertFalse(engine["modelLoaded"])
            self.assertFalse(engine["inferenceAvailable"])
            self.assertFalse(engine["downloadsAllowed"])
            self.assertEqual(engine["networkAccess"], "NONE")

    def test_browser_engine_is_only_a_capability_probe(self):
        browser = LocalAIRegistry.list_engines()[0]
        self.assertEqual(browser["implementation"], "CAPABILITY_PROBE_ONLY")
        self.assertEqual(browser["runtimeScope"], "user_device_browser")

    def test_server_local_engine_is_not_misrepresented_as_user_tablet(self):
        ollama = LocalAIRegistry.list_engines()[1]
        self.assertEqual(ollama["runtimeScope"], "server_host_loopback")
        self.assertEqual(ollama["implementation"], "NOT_IMPLEMENTED")

    def test_inference_contract_is_disabled_without_an_injected_local_engine(self):
        contract = LocalAIRegistry.inference_contract()
        self.assertEqual(contract["state"], "NOT_CONFIGURED")
        self.assertFalse(contract["inferenceAvailable"])
        self.assertEqual(contract["networkAccess"], "NONE")
        self.assertFalse(contract["downloadsAllowed"])

    def test_internal_messenger_is_not_model_inference(self):
        messenger = LocalAIRegistry.messenger_capabilities()
        self.assertEqual(messenger["state"], "AVAILABLE")
        self.assertTrue(messenger["supportsGroupRooms"])
        self.assertFalse(messenger["modelExecution"])


if __name__ == "__main__":
    unittest.main()
