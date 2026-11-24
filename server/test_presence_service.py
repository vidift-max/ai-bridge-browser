import tempfile
import unittest

from server.presence_service import PresenceService
from server.sqlite_store import SQLiteMessengerStore


class PresenceServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite")
        self.store = SQLiteMessengerStore(self.tmp.name)
        self.presence = PresenceService(self.store._connection, ttl_seconds=90)

    def tearDown(self):
        self.store.close()
        self.tmp.close()

    def test_heartbeat_marks_authenticated_ai_online_in_its_room(self):
        result = self.presence.heartbeat("AI-A", ["room-1"], ["room-1"], now=1000)
        self.assertEqual(result["status"], "ONLINE")
        self.assertEqual(result["expiresAt"], 1090)
        rows = self.presence.list_room("room-1", ["AI-A", "AI-B"], now=1001)
        self.assertEqual(rows, [
            {"aiId": "AI-A", "displayName": "AI-A", "status": "ONLINE",
             "activeInRoom": True, "lastSeenAt": 1000},
            {"aiId": "AI-B", "displayName": "AI-B", "status": "OFFLINE",
             "activeInRoom": False, "lastSeenAt": None},
        ])

    def test_presence_expires_automatically_after_ttl(self):
        self.presence.heartbeat("AI-A", ["room-1"], ["room-1"], now=1000)
        rows = self.presence.list_room("room-1", ["AI-A"], now=1091)
        self.assertEqual(rows[0]["status"], "OFFLINE")
        self.assertFalse(rows[0]["activeInRoom"])

    def test_heartbeat_rejects_room_outside_server_membership(self):
        with self.assertRaisesRegex(PermissionError, "presence_room_membership_required"):
            self.presence.heartbeat("AI-A", ["private-room"], ["room-1"], now=1000)
        self.assertEqual(
            self.presence.list_room("private-room", ["AI-A"], now=1000)[0]["status"],
            "OFFLINE")

    def test_heartbeat_rejects_invalid_active_room_payloads(self):
        invalid = [None, "room-1", ["room-1", "room-1"], [""]]
        for active in invalid:
            with self.subTest(active=active):
                with self.assertRaises(ValueError):
                    self.presence.heartbeat("AI-A", active, ["room-1"], now=1000)

    def test_room_listing_never_exposes_non_members(self):
        self.presence.heartbeat("AI-C", ["room-1"], ["room-1"], now=1000)
        rows = self.presence.list_room("room-1", ["AI-A", "AI-B"], now=1000)
        self.assertEqual([row["aiId"] for row in rows], ["AI-A", "AI-B"])

    def test_leave_clears_presence_and_room_activity(self):
        self.presence.heartbeat("AI-A", ["room-1"], ["room-1"], now=1000)
        self.assertTrue(self.presence.leave("AI-A"))
        self.assertFalse(self.presence.leave("AI-A"))
        row = self.presence.list_room("room-1", ["AI-A"], now=1000)[0]
        self.assertEqual(row["status"], "OFFLINE")
        self.assertFalse(row["activeInRoom"])

    def test_presence_survives_store_reopen_but_expires_by_timestamp(self):
        self.presence.heartbeat("AI-A", ["room-1"], ["room-1"], now=1000)
        self.store.close()
        reopened = SQLiteMessengerStore(self.tmp.name)
        try:
            service = PresenceService(reopened._connection, ttl_seconds=90)
            self.assertEqual(
                service.list_room("room-1", ["AI-A"], now=1050)[0]["status"],
                "ONLINE")
            self.assertEqual(
                service.list_room("room-1", ["AI-A"], now=1100)[0]["status"],
                "OFFLINE")
        finally:
            reopened.close()

    def test_invalid_ttl_is_rejected(self):
        for ttl in (True, 0, 29, 121, "90"):
            with self.subTest(ttl=ttl):
                with self.assertRaisesRegex(ValueError, "invalid_presence_ttl"):
                    PresenceService(self.store._connection, ttl_seconds=ttl)


if __name__ == "__main__":
    unittest.main()
