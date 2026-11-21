import os
import unittest
from server.runtime_config import RuntimeConfig

class RuntimeConfigTest(unittest.TestCase):
    def test_required_config(self):
        old = os.environ.get("TEST_RUNTIME_CONFIG")
        os.environ["TEST_RUNTIME_CONFIG"] = "value"
        try:
            self.assertEqual(RuntimeConfig.require("TEST_RUNTIME_CONFIG"), "value")
        finally:
            if old is None:
                os.environ.pop("TEST_RUNTIME_CONFIG", None)
            else:
                os.environ["TEST_RUNTIME_CONFIG"] = old

    def test_missing_required_config_rejected(self):
        os.environ.pop("TEST_RUNTIME_MISSING", None)
        with self.assertRaises(RuntimeError):
            RuntimeConfig.require("TEST_RUNTIME_MISSING")

if __name__ == "__main__":
    unittest.main()
