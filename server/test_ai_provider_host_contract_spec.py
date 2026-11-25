import json
import unittest
from pathlib import Path


class ProviderHostContractSpecTest(unittest.TestCase):
    def test_machine_contract_keeps_route_and_delivery_explicitly_unmounted(self):
        path = Path(__file__).with_name("ai_provider_host_contract.json")
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(contract["route"], "NOT_MOUNTED")
        self.assertEqual(contract["delivery"]["persistence"], "NOT_IMPLEMENTED")
        self.assertEqual(contract["delivery"]["messengerDelivery"], "NOT_IMPLEMENTED")

    def test_contract_forbids_client_sender_identity_and_browser_credentials(self):
        path = Path(__file__).with_name("ai_provider_host_contract.json")
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(contract["authentication"]["clientMayAssertSenderIdentity"])
        self.assertFalse(contract["provider"]["credentialsInBrowser"])
        self.assertFalse(contract["attestation"]["keyExposedToBrowser"])

    def test_contract_does_not_claim_live_or_cross_device_proof(self):
        path = Path(__file__).with_name("ai_provider_host_contract.json")
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(contract["proof"]["unitTestsUseFakes"])
        self.assertFalse(contract["proof"]["liveProviderProven"])
        self.assertFalse(contract["proof"]["crossDeviceDeliveryProven"])


if __name__ == "__main__":
    unittest.main()
