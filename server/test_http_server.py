import unittest
from server.auth import Authenticator
from server.http_server import MessengerHandler

class HttpContractTest(unittest.TestCase):
    def test_health_and_readiness_routes_are_defined(self):
        self.assertIn("/healthz",MessengerHandler.do_GET.__code__.co_consts)
        self.assertIn("/readyz",MessengerHandler.do_GET.__code__.co_consts)

    def test_gpt6_web_route_is_defined(self):
        self.assertIn("/gpt6",MessengerHandler.do_GET.__code__.co_consts)
        self.assertTrue(hasattr(MessengerHandler,"_gpt6_web"))

    def test_routes_are_defined(self):
        self.assertTrue(hasattr(MessengerHandler,"do_GET"))
        self.assertTrue(hasattr(MessengerHandler,"do_POST"))
        self.assertIn("/v1/messages",MessengerHandler.do_POST.__code__.co_consts)

    def test_authentication_boundary_is_present(self):
        self.assertTrue(hasattr(MessengerHandler,"_principal"))
        self.assertIn("authentication_required",MessengerHandler.do_GET.__code__.co_consts)

    def test_revoked_credential_is_rejected_before_protected_work(self):
        auth=Authenticator({"token-a":"AI-A"})
        auth.revoke("token-a")
        with self.assertRaises(PermissionError):
            auth.authenticate("token-a")

if __name__=="__main__":
    unittest.main()
