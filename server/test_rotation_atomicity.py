import unittest

from server.credential_registry import CredentialRegistry
from server.session_registry import SessionRegistry


class RotationAtomicityTests(unittest.TestCase):
    def test_credential_rotation_collision_does_not_mutate_old(self):
        registry = CredentialRegistry({"old": "ai-a", "taken": "ai-b"})
        with self.assertRaises(ValueError):
            registry.rotate("old", "taken")
        self.assertEqual(registry.status("old"), "ACTIVE")
        self.assertEqual(registry.authenticate("old"), "ai-a")

    def test_session_rotation_collision_does_not_mutate_old(self):
        registry = SessionRegistry()
        registry.create("old-session", "ai-a")
        registry.create("taken-session", "ai-b")
        with self.assertRaises(ValueError):
            registry.rotate("old-session", "taken-session")
        self.assertEqual(registry.status("old-session"), "ACTIVE")
        self.assertEqual(registry.authenticate("old-session").ai_id, "ai-a")


if __name__ == "__main__":
    unittest.main()
