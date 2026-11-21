import unittest
from server.http_server import MessengerHandler

class HttpContractTest(unittest.TestCase):
    def test_routes_are_defined(self):
        self.assertTrue(hasattr(MessengerHandler, "do_GET"))
        self.assertTrue(hasattr(MessengerHandler, "do_POST"))
        self.assertIn("/v1/messages", MessengerHandler.do_POST.__code__.co_consts)

if __name__ == "__main__":
    unittest.main()
