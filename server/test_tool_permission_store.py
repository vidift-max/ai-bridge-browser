import tempfile
import unittest
from pathlib import Path

from server.sqlite_store import SQLiteMessengerStore
from server.recovery import verify_messenger_schema
from server.tool_permissions import ToolPermissionRegistry


class DurableToolPermissionStoreTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = str(Path(self.directory.name) / "permissions.sqlite")
        self.store = SQLiteMessengerStore(self.path)

    def tearDown(self):
        self.store.close()
        self.directory.cleanup()

    def test_grant_survives_store_and_registry_recreation(self):
        registry = ToolPermissionRegistry(store=self.store)
        grant = registry.grant("AI-01", "duration_timer", "tool-hub-admin")
        self.assertEqual(grant["principalAiId"], "AI-01")
        self.assertTrue(registry.can_use("AI-01", "duration_timer"))
        self.store.close()
        self.store = SQLiteMessengerStore(self.path)
        restarted = ToolPermissionRegistry(store=self.store)
        self.assertTrue(restarted.can_use("AI-01", "duration_timer"))
        self.assertEqual(restarted.list_grants()[0]["grantedBy"], "tool-hub-admin")

    def test_revoke_survives_store_and_registry_recreation(self):
        registry = ToolPermissionRegistry(store=self.store)
        registry.grant("AI-01", "duration_timer", "tool-hub-admin")
        self.assertTrue(registry.revoke("AI-01", "duration_timer"))
        self.assertFalse(registry.revoke("AI-01", "duration_timer"))
        self.store.close()
        self.store = SQLiteMessengerStore(self.path)
        restarted = ToolPermissionRegistry(store=self.store)
        self.assertFalse(restarted.can_use("AI-01", "duration_timer"))
        self.assertEqual(restarted.list_grants(), [])

    def test_grants_are_isolated_by_ai_and_tool(self):
        registry = ToolPermissionRegistry(store=self.store)
        registry.grant("AI-01", "duration_timer", "tool-hub-admin")
        registry.grant("AI-02", "quiz_engine", "tool-hub-admin")
        self.assertTrue(registry.can_use("AI-01", "duration_timer"))
        self.assertFalse(registry.can_use("AI-02", "duration_timer"))
        self.assertFalse(registry.can_use("AI-01", "quiz_engine"))

    def test_unknown_tool_and_invalid_principal_cannot_be_granted(self):
        registry = ToolPermissionRegistry(store=self.store)
        with self.assertRaisesRegex(ValueError, "unsupported_tool_permission"):
            registry.grant("AI-01", "shell_exec", "tool-hub-admin")
        with self.assertRaisesRegex(ValueError, "invalid_tool_permission_principal"):
            registry.grant(" AI-01", "duration_timer", "tool-hub-admin")

    def test_migration_preserves_existing_messenger_data_and_schema(self):
        version = self.store._connection.execute(
            "SELECT value FROM schema_meta WHERE key='version'"
        ).fetchone()["value"]
        self.assertEqual(version, "3")
        self.store.save_conversation("room", ["AI-01", "AI-02"])
        self.store.close()
        self.store = SQLiteMessengerStore(self.path)
        self.assertEqual(self.store.load_conversations()["room"], {"AI-01", "AI-02"})



    def test_schema_v2_is_accepted_by_read_only_recovery_validation(self):
        self.assertEqual(verify_messenger_schema(self.path), (True, "RESTORE_SCHEMA_COMPATIBLE"))


    def test_permission_audit_is_durable_and_records_grant_and_revoke_actor(self):
        registry = ToolPermissionRegistry(store=self.store)
        registry.grant("AI-01", "duration_timer", "admin-01")
        registry.revoke("AI-01", "duration_timer", "admin-02")
        events = registry.list_audit_events()
        self.assertEqual([event["action"] for event in events], ["GRANT", "REVOKE"])
        self.assertEqual([event["actorId"] for event in events], ["admin-01", "admin-02"])
        self.assertTrue(events[0]["grantExisted"])
        self.assertTrue(events[1]["grantExisted"])
        self.store.close()
        self.store = SQLiteMessengerStore(self.path)
        restarted = ToolPermissionRegistry(store=self.store)
        self.assertEqual(len(restarted.list_audit_events()), 2)

if __name__ == "__main__":
    unittest.main()
