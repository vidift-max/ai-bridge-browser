import tempfile
import unittest

from server.sqlite_store import SQLiteMessengerStore
from server.voice_room_control import VoiceRoomControl


class VoiceRoomControlTest(unittest.TestCase):
    def setUp(self):
        self.rooms = {"room-1": {"AI-ADMIN", "AI-A", "AI-B"},
                      "room-2": {"AI-ADMIN", "AI-C"}}
        self.control = VoiceRoomControl({"AI-ADMIN"})

    def test_admin_can_mute_and_unmute_room_member(self):
        muted = self.control.mute("AI-ADMIN", "room-1", "AI-A", self.rooms)
        self.assertTrue(muted["muted"])
        self.assertTrue(self.control.is_muted("room-1", "AI-A"))
        released = self.control.unmute("AI-ADMIN", "room-1", "AI-A", self.rooms)
        self.assertFalse(released["muted"])
        self.assertFalse(self.control.is_muted("room-1", "AI-A"))

    def test_non_admin_cannot_mute(self):
        with self.assertRaisesRegex(PermissionError, "voice_admin_required"):
            self.control.mute("AI-A", "room-1", "AI-B", self.rooms)

    def test_admin_must_belong_to_room(self):
        rooms_without_admin = {"room-1": {"AI-A", "AI-B"}}
        with self.assertRaisesRegex(PermissionError, "voice_room_membership_required"):
            self.control.mute("AI-ADMIN", "room-1", "AI-A", rooms_without_admin)

    def test_target_must_belong_to_same_room(self):
        with self.assertRaisesRegex(PermissionError, "voice_room_membership_required"):
            self.control.mute("AI-ADMIN", "room-1", "AI-C", self.rooms)

    def test_admin_cannot_mute_self(self):
        with self.assertRaisesRegex(ValueError, "admin_cannot_mute_self"):
            self.control.mute("AI-ADMIN", "room-1", "AI-ADMIN", self.rooms)

    def test_mute_state_is_isolated_per_room(self):
        self.control.mute("AI-ADMIN", "room-1", "AI-A", self.rooms)
        self.assertTrue(self.control.is_muted("room-1", "AI-A"))
        self.assertFalse(self.control.is_muted("room-2", "AI-A"))
        self.assertEqual(self.control.muted_participants("room-1"), {"AI-A"})

    def test_repeated_mute_and_unmute_are_idempotent(self):
        self.control.mute("AI-ADMIN", "room-1", "AI-A", self.rooms)
        self.control.mute("AI-ADMIN", "room-1", "AI-A", self.rooms)
        self.assertEqual(self.control.muted_participants("room-1"), {"AI-A"})
        self.control.unmute("AI-ADMIN", "room-1", "AI-A", self.rooms)
        self.control.unmute("AI-ADMIN", "room-1", "AI-A", self.rooms)
        self.assertEqual(self.control.muted_participants("room-1"), set())

    def test_mute_survives_control_restart_and_expires(self):
        class Clock:
            value = 1000.0
            def __call__(self):
                return self.value

        with tempfile.NamedTemporaryFile(suffix=".sqlite") as f:
            clock = Clock()
            store = SQLiteMessengerStore(f.name)
            control = VoiceRoomControl({"AI-ADMIN"}, store=store, clock=clock)
            result = control.mute("AI-ADMIN", "room-1", "AI-A",
                                  self.rooms, duration_seconds=60)
            self.assertEqual(result["expiresAt"], 1060.0)
            self.assertTrue(control.is_muted("room-1", "AI-A"))
            store.close()

            reopened_store = SQLiteMessengerStore(f.name)
            reopened = VoiceRoomControl({"AI-ADMIN"}, store=reopened_store,
                                        clock=clock)
            self.assertTrue(reopened.is_muted("room-1", "AI-A"))
            clock.value = 1060.0
            self.assertFalse(reopened.is_muted("room-1", "AI-A"))
            self.assertEqual(reopened_store.load_active_voice_mutes(1060.0), [])
            reopened_store.close()

    def test_mute_duration_is_bounded(self):
        with self.assertRaisesRegex(ValueError, "invalid_voice_mute_duration"):
            self.control.mute("AI-ADMIN", "room-1", "AI-A", self.rooms, 0)
        with self.assertRaisesRegex(ValueError, "invalid_voice_mute_duration"):
            self.control.mute("AI-ADMIN", "room-1", "AI-A", self.rooms, 3601)
        with self.assertRaisesRegex(ValueError, "invalid_voice_mute_duration"):
            self.control.mute("AI-ADMIN", "room-1", "AI-A", self.rooms, True)

    def test_invalid_admin_configuration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_voice_admin_ids"):
            VoiceRoomControl(["AI-ADMIN", "AI-ADMIN"])


if __name__ == "__main__":
    unittest.main()
