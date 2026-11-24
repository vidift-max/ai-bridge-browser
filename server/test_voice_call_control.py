import tempfile
import unittest

from server.sqlite_store import SQLiteMessengerStore
from server.voice_call_control import VoiceCallControl


class Clock:
    def __init__(self):
        self.value = 1000.0
    def __call__(self):
        return self.value


class VoiceCallControlTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.NamedTemporaryFile(suffix=".sqlite")
        self.store = SQLiteMessengerStore(self.temp.name)
        self.clock = Clock()
        self.ids = iter(["call-001", "call-002"])
        self.control = VoiceCallControl(self.store, clock=self.clock,
                                        id_factory=lambda: next(self.ids))
        self.rooms = {"private-1": {"AI-01", "AI-02"}}
        self.kinds = {"private-1": "PRIVATE"}

    def tearDown(self):
        self.store.close()
        self.temp.close()

    def create(self):
        return self.control.create("AI-01", "AI-02", "private-1",
                                   self.rooms, self.kinds)

    def test_create_and_accept_call(self):
        call = self.create()
        self.assertEqual(call["state"], "RINGING")
        accepted = self.control.transition("AI-02", call["call_id"], "accept")
        self.assertEqual(accepted["state"], "ACCEPTED")

    def test_only_callee_can_accept_or_reject(self):
        call = self.create()
        with self.assertRaisesRegex(PermissionError, "voice_call_callee_required"):
            self.control.transition("AI-01", call["call_id"], "accept")
        with self.assertRaisesRegex(PermissionError, "voice_call_callee_required"):
            self.control.transition("AI-01", call["call_id"], "reject")

    def test_only_caller_can_cancel(self):
        call = self.create()
        with self.assertRaisesRegex(PermissionError, "voice_call_caller_required"):
            self.control.transition("AI-02", call["call_id"], "cancel")
        self.assertEqual(self.control.transition("AI-01", call["call_id"], "cancel")["state"],
                         "CANCELLED")

    def test_reject_and_timeout_are_terminal(self):
        call = self.create()
        self.assertEqual(self.control.transition("AI-02", call["call_id"], "reject")["state"],
                         "REJECTED")
        call = self.create()
        self.clock.value += 46
        self.assertEqual(self.control.get("AI-01", call["call_id"])["state"], "TIMED_OUT")

    def test_only_private_two_member_conversation_is_allowed(self):
        with self.assertRaisesRegex(PermissionError, "private_conversation_required"):
            self.control.create("AI-01", "AI-02", "group-1",
                                {"group-1": {"AI-01", "AI-02"}}, {"group-1": "GROUP"})
        with self.assertRaisesRegex(PermissionError, "private_conversation_membership_required"):
            self.control.create("AI-01", "AI-03", "private-1",
                                self.rooms, self.kinds)

    def test_active_call_blocks_another_call(self):
        self.create()
        with self.assertRaisesRegex(RuntimeError, "voice_call_busy"):
            self.control.create("AI-02", "AI-01", "private-1",
                                self.rooms, self.kinds)

    def test_only_call_participants_can_read_or_signal(self):
        call = self.create()
        with self.assertRaisesRegex(PermissionError, "voice_call_participant_required"):
            self.control.get("AI-03", call["call_id"])

    def test_signaling_is_ordered_and_hidden_from_sender(self):
        call = self.create()
        self.control.transition("AI-02", call["call_id"], "accept")
        offer = self.control.add_signal("AI-01", call["call_id"], "OFFER",
                                        {"type": "offer", "sdp": "v=0\\r\\n"})
        self.assertEqual(offer["kind"], "OFFER")
        self.assertEqual(self.control.pending_signals("AI-02", call["call_id"])[0]["signalId"],
                         offer["signalId"])
        self.assertEqual(self.control.pending_signals("AI-01", call["call_id"]), [])

    def test_signaling_metadata_is_purged_when_call_ends(self):
        call = self.create()
        self.control.transition("AI-02", call["call_id"], "accept")
        self.control.add_signal("AI-01", call["call_id"], "OFFER",
                                {"type": "offer", "sdp": "v=0"})
        self.assertEqual(len(self.control.pending_signals("AI-02", call["call_id"])), 1)
        self.control.transition("AI-01", call["call_id"], "end")
        self.assertEqual(self.control.pending_signals("AI-02", call["call_id"]), [])

    def test_offer_and_answer_must_come_from_their_call_roles(self):
        call = self.create()
        self.control.transition("AI-02", call["call_id"], "accept")
        with self.assertRaisesRegex(PermissionError, "voice_signal_role_mismatch"):
            self.control.add_signal("AI-02", call["call_id"], "OFFER",
                                    {"type": "offer", "sdp": "v=0"})
        self.control.add_signal("AI-01", call["call_id"], "OFFER",
                                {"type": "offer", "sdp": "v=0"})
        with self.assertRaisesRegex(PermissionError, "voice_signal_role_mismatch"):
            self.control.add_signal("AI-01", call["call_id"], "ANSWER",
                                    {"type": "answer", "sdp": "v=0"})

    def test_invalid_signal_payload_is_rejected(self):
        call = self.create()
        self.control.transition("AI-02", call["call_id"], "accept")
        with self.assertRaisesRegex(ValueError, "invalid_voice_session_description"):
            self.control.add_signal("AI-01", call["call_id"], "OFFER",
                                    {"type": "answer", "sdp": "v=0"})
        with self.assertRaisesRegex(ValueError, "invalid_ice_candidate"):
            self.control.add_signal("AI-01", call["call_id"], "ICE_CANDIDATE",
                                    {"candidate": 7})

    def test_connected_call_can_be_ended_by_either_participant(self):
        call = self.create()
        self.control.transition("AI-02", call["call_id"], "accept")
        self.control.set_connecting("AI-01", call["call_id"])
        self.control.set_connected("AI-02", call["call_id"])
        self.assertEqual(self.control.transition("AI-02", call["call_id"], "end")["state"],
                         "ENDED")


if __name__ == "__main__":
    unittest.main()
