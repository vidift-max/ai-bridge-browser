import unittest
from pathlib import Path


class WifiOnlyPolicyContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = (Path(__file__).resolve().parent.parent / "web" / "wifi-only.js").read_text(encoding="utf-8")

    def test_gate_requires_online_and_explicit_wifi(self):
        self.assertIn('nav.onLine === true', self.script)
        self.assertIn('type === "wifi"', self.script)
        self.assertIn('var allowed = online && type === "wifi"', self.script)

    def test_unknown_connection_fails_closed(self):
        self.assertIn('"unknown"', self.script)
        self.assertIn('"WIFI_STATUS_UNAVAILABLE"', self.script)
        self.assertIn('throw error', self.script)

    def test_gate_does_not_make_requests_or_persist_data(self):
        self.assertNotIn("fetch(", self.script)
        self.assertNotIn("localStorage", self.script)
        self.assertNotIn("sessionStorage", self.script)

    def test_network_changes_can_be_observed(self):
        self.assertIn('addEventListener("online"', self.script)
        self.assertIn('addEventListener("offline"', self.script)
        self.assertIn('connection.addEventListener("change"', self.script)


if __name__ == "__main__":
    unittest.main()
