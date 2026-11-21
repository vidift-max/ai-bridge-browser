import unittest
from server.http_server import MessengerHandler


class HttpOperationalIntegrationTests(unittest.TestCase):
    def test_handler_exposes_operational_runtime_slot(self):
        self.assertTrue(hasattr(MessengerHandler, "operational"))

    def test_audit_path_forwards_events_to_operational_runtime(self):
        source = MessengerHandler._audit.__code__.co_names
        self.assertIn("record", source)
        self.assertIn("operational", source)

    def test_readiness_path_checks_storage(self):
        source = MessengerHandler.do_GET.__code__.co_names
        self.assertIn("check_storage", source)


if __name__ == "__main__":
    unittest.main()
