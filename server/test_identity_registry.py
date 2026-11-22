import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from server.identity_registry import IdentityRegistry


class IdentityRegistryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = self.temp.name + "/messenger.sqlite"
        self.registry = IdentityRegistry(self.path)

    def tearDown(self):
        self.registry.close()
        self.temp.cleanup()

    def test_authenticated_identity_gets_stable_phone_number_and_serial(self):
        first = self.registry.register_authenticated("AI-ALPHA", "Alpha", "test-provider")
        again = self.registry.register_authenticated("AI-ALPHA", "Renamed", "other-provider")
        self.assertEqual(first, again)
        self.assertEqual(first["displayNumber"], "AI-PHONE-000001")
        self.assertTrue(first["serial"].startswith("AIP-"))
        self.assertEqual(first["status"], "ACTIVE")

    def test_distinct_identities_receive_distinct_non_reused_numbers(self):
        first = self.registry.register_authenticated("AI-ALPHA")
        second = self.registry.register_authenticated("AI-BRAVO")
        self.assertEqual(first["displayNumber"], "AI-PHONE-000001")
        self.assertEqual(second["displayNumber"], "AI-PHONE-000002")
        self.assertNotEqual(first["serial"], second["serial"])

    def test_lookup_by_number_returns_only_public_registry_record(self):
        created = self.registry.register_authenticated("AI-ALPHA", "Alpha")
        found = self.registry.get_by_number(created["displayNumber"])
        self.assertEqual(found["aiId"], "AI-ALPHA")
        self.assertNotIn("token", found)
        self.assertIsNone(self.registry.get_by_number("AI-PHONE-999999"))

    def test_invalid_ai_id_and_number_are_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.register_authenticated("not-an-ai")
        with self.assertRaises(ValueError):
            self.registry.get_by_number("AI-PHONE-1")

    def test_concurrent_registration_of_same_ai_is_idempotent(self):
        def register(_):
            registry = IdentityRegistry(self.path)
            try:
                return registry.register_authenticated("AI-ALPHA")
            finally:
                registry.close()

        with ThreadPoolExecutor(max_workers=8) as pool:
            records = list(pool.map(register, range(16)))
        self.assertEqual(len({r["displayNumber"] for r in records}), 1)
        self.assertEqual(records[0]["displayNumber"], "AI-PHONE-000001")

    def test_concurrent_distinct_registrations_allocate_unique_numbers(self):
        ai_ids = [f"AI-TEAM-{i:02d}" for i in range(1, 13)]

        def register(ai_id):
            registry = IdentityRegistry(self.path)
            try:
                return registry.register_authenticated(ai_id)
            finally:
                registry.close()

        with ThreadPoolExecutor(max_workers=8) as pool:
            records = list(pool.map(register, ai_ids))
        self.assertEqual(len({r["displayNumber"] for r in records}), len(ai_ids))
        self.assertEqual(len({r["serial"] for r in records}), len(ai_ids))
        self.assertEqual(
            {r["displayNumber"] for r in records},
            {f"AI-PHONE-{i:06d}" for i in range(1, 13)},
        )


if __name__ == "__main__":
    unittest.main()
