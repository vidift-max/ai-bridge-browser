import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore
from server.audio_blob_store import AudioBlobStore

class MessengerBackendTest(unittest.TestCase):
    def setUp(self):
        self.backend = MessengerBackend({"opaque-a": "AI-A", "opaque-b": "AI-B"}, {"room-1": {"AI-A", "AI-B"}})

    def tearDown(self):
        self.backend.close()

    def test_audio_attachment_is_bound_to_message_and_survives_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            db = SQLiteMessengerStore(f"{directory}/messenger.sqlite")
            backend = MessengerBackend(
                {"opaque-a": "AI-A", "opaque-b": "AI-B"},
                {"room-1": {"AI-A", "AI-B"}}, db)
            store = AudioBlobStore(f"{directory}/audio")
            backend.submit("opaque-a", "audio-msg", "room-1", ["AI-B"], "voice", "voice-req")
            attachment = backend.attach_audio("opaque-a", "audio-msg", store, b"OggS" + b"x" * 20, "audio/ogg")
            self.assertEqual(attachment.message_id, "audio-msg")
            self.assertEqual(attachment.sender_ai_id, "AI-A")
            self.assertEqual(backend.read_audio("opaque-b", "audio-msg", attachment.object_id, store), b"OggS" + b"x" * 20)
            backend.close()
            db = SQLiteMessengerStore(f"{directory}/messenger.sqlite")

            restarted = MessengerBackend(
                {"opaque-a": "AI-A", "opaque-b": "AI-B"}, {}, db)
            listed = restarted.list_audio_attachments("opaque-b", "audio-msg")
            self.assertEqual([item.object_id for item in listed], [attachment.object_id])
            restarted.close()

    def test_audio_attachment_sender_only_and_member_only_read_access(self):
        with tempfile.TemporaryDirectory() as directory:
            db = SQLiteMessengerStore(f"{directory}/messenger.sqlite")
            backend = MessengerBackend(
                {"opaque-a": "AI-A", "opaque-b": "AI-B", "opaque-c": "AI-C"},
                {"room-1": {"AI-A", "AI-B"}}, db)
            store = AudioBlobStore(f"{directory}/audio")
            backend.submit("opaque-a", "audio-msg", "room-1", ["AI-B"], "voice", "voice-req")
            with self.assertRaisesRegex(PermissionError, "attachment_sender_only"):
                backend.attach_audio("opaque-b", "audio-msg", store, b"OggS" + b"x" * 20, "audio/ogg")
            attachment = backend.attach_audio("opaque-a", "audio-msg", store, b"OggS" + b"x" * 20, "audio/ogg")
            with self.assertRaisesRegex(PermissionError, "authorization_denied"):
                backend.list_audio_attachments("opaque-c", "audio-msg")
            with self.assertRaisesRegex(PermissionError, "authorization_denied"):
                backend.read_audio("opaque-c", "audio-msg", attachment.object_id, store)
            backend.close()

    def test_authenticated_submit_and_pending(self):
        msg=self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"hello","req-1")
        self.assertEqual(msg.sender_ai_id,"AI-A")
        self.assertEqual(self.backend.pending("opaque-b","room-1")[0].message_id,"m-1")

    def test_restart_recovers_message_and_ack(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as f:
            first=MessengerBackend({"opaque-a":"AI-A","opaque-b":"AI-B"},{"room-1":{"AI-A","AI-B"}},SQLiteMessengerStore(f.name))
            first.submit("opaque-a","m-1","room-1",["AI-B"],"hello","req-1")
            first.acknowledge("opaque-b","m-1")
            first.close()
            second=MessengerBackend({"opaque-a":"AI-A","opaque-b":"AI-B"},{"room-1":{"AI-A","AI-B"}},SQLiteMessengerStore(f.name))
            self.assertEqual(second.pending("opaque-b","room-1"),[])
            self.assertEqual(second.submit("opaque-a","m-1","room-1",["AI-B"],"hello","req-1").message_id,"m-1")
            second.close()

    def test_unauthenticated_submit_rejected(self):
        with self.assertRaises(PermissionError):
            self.backend.submit("bad","m-1","room-1",["AI-B"],"hello","req-1")

    def test_idempotency_conflict_rejected(self):
        self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"hello","req-1")
        with self.assertRaises(ValueError):
            self.backend.submit("opaque-a","m-2","room-1",["AI-B"],"different","req-1")

    def test_duplicate_message_id_rejected(self):
        self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"hello","req-1")
        with self.assertRaises(ValueError):
            self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"other","req-2")

    def test_recipients_are_deduplicated(self):
        msg=self.backend.submit("opaque-a","m-1","room-1",["AI-B","AI-B"],"hello","req-1")
        self.assertEqual(msg.recipient_ai_ids,("AI-B",))

    def test_create_private_conversation_requires_exactly_two_members(self):
        result = self.backend.create_conversation(
            "opaque-a", "private-1", ["AI-A", "AI-B"], "PRIVATE")
        self.assertEqual(result["kind"], "PRIVATE")
        self.assertEqual(result["memberCount"], 2)

    def test_create_group_allows_up_to_twenty_members(self):
        tokens = {f"token-{i}": f"AI-{i}" for i in range(1, 21)}
        backend = MessengerBackend(tokens, {})
        try:
            result = backend.create_conversation(
                "token-1", "room-20", list(tokens.values()), "GROUP")
            self.assertEqual(result["memberCount"], 20)
            self.assertEqual(len(backend._conversations["room-20"]), 20)
        finally:
            backend.close()

    def test_create_group_rejects_more_than_twenty_members(self):
        tokens = {f"token-{i}": f"AI-{i}" for i in range(1, 22)}
        backend = MessengerBackend(tokens, {})
        try:
            with self.assertRaisesRegex(ValueError, "conversation_member_limit"):
                backend.create_conversation(
                    "token-1", "room-21", list(tokens.values()), "GROUP")
        finally:
            backend.close()

    def test_create_conversation_rejects_unknown_members(self):
        with self.assertRaisesRegex(ValueError, "unknown_conversation_member"):
            self.backend.create_conversation(
                "opaque-a", "room-unknown", ["AI-A", "AI-UNPROVISIONED"], "GROUP")

    def test_private_conversation_rejects_three_members(self):
        tokens = {"a": "AI-A", "b": "AI-B", "c": "AI-C"}
        backend = MessengerBackend(tokens, {})
        try:
            with self.assertRaisesRegex(ValueError, "private_conversation_requires_two_members"):
                backend.create_conversation("a", "private-3", ["AI-A", "AI-B", "AI-C"], "PRIVATE")
        finally:
            backend.close()

    def test_created_conversation_authorizes_message_delivery(self):
        self.backend.create_conversation(
            "opaque-a", "new-room", ["AI-A", "AI-B"], "GROUP")
        message = self.backend.submit(
            "opaque-a", "new-room-msg", "new-room", ["AI-B"], "hello team", "new-room-req")
        self.assertEqual(message.conversation_id, "new-room")
        self.assertEqual(self.backend.pending("opaque-b", "new-room")[0].body, "hello team")

    def test_created_conversation_survives_store_restart(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as f:
            first = MessengerBackend(
                {"opaque-a": "AI-A", "opaque-b": "AI-B"}, {},
                SQLiteMessengerStore(f.name))
            first.create_conversation("opaque-a", "persistent-room",
                                      ["AI-A", "AI-B"], "GROUP")
            first.close()
            second = MessengerBackend(
                {"opaque-a": "AI-A", "opaque-b": "AI-B"}, {},
                SQLiteMessengerStore(f.name))
            try:
                message = second.submit("opaque-a", "persisted-msg", "persistent-room",
                                         ["AI-B"], "survived", "persisted-request")
                self.assertEqual(message.conversation_id, "persistent-room")
            finally:
                second.close()

    def test_group_normal_message_expires_after_one_hour(self):
        with patch("server.messenger_backend.time.time", return_value=1000.0):
            message = self.backend.submit("opaque-a", "retention-group", "room-1",
                                          ["AI-B"], "normal", "retention-group-req")
        with patch("server.messenger_backend.time.time", return_value=1000.0 + 3600 - 1):
            self.assertEqual(len(self.backend.pending("opaque-b", "room-1")), 1)
        with patch("server.messenger_backend.time.time", return_value=1000.0 + 3600):
            self.assertEqual(self.backend.pending("opaque-b", "room-1"), [])

    def test_mission_message_expires_after_twenty_four_hours(self):
        with patch("server.messenger_backend.time.time", return_value=2000.0):
            self.backend.submit("opaque-a", "retention-mission", "room-1",
                                ["AI-B"], "mission", "retention-mission-req", "MISSION")
        with patch("server.messenger_backend.time.time", return_value=2000.0 + 86400 - 1):
            self.assertEqual(len(self.backend.pending("opaque-b", "room-1")), 1)
        with patch("server.messenger_backend.time.time", return_value=2000.0 + 86400):
            self.assertEqual(self.backend.pending("opaque-b", "room-1"), [])

    def test_private_message_expires_after_twenty_four_hours(self):
        with patch("server.messenger_backend.time.time", return_value=3000.0):
            self.backend.create_conversation("opaque-a", "retention-private",
                                              ["AI-A", "AI-B"], "PRIVATE")
            self.backend.submit("opaque-a", "retention-private-msg", "retention-private",
                                ["AI-B"], "private", "retention-private-req")
        with patch("server.messenger_backend.time.time", return_value=3000.0 + 86400 - 1):
            self.assertEqual(len(self.backend.pending("opaque-b", "retention-private")), 1)
        with patch("server.messenger_backend.time.time", return_value=3000.0 + 86400):
            self.assertEqual(self.backend.pending("opaque-b", "retention-private"), [])

    def test_body_limit_rejected(self):
        with self.assertRaises(ValueError):
            self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"x"*5001,"req-1")

    def test_pending_cursor(self):
        self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"one","req-1")
        self.backend.submit("opaque-a","m-2","room-1",["AI-B"],"two","req-2")
        self.assertEqual([m.message_id for m in self.backend.pending("opaque-b","room-1",after_sequence=1)],["m-2"])

    def test_submit_rejects_non_string_or_blank_message_fields(self):
        invalid_cases = [
            (None, "room-1", "body", "request"),
            ("message", None, "body", "request"),
            ("message", "room-1", ["not", "text"], "request"),
            ("message", "room-1", "body", {"not": "text"}),
            ("message", "room-1", "   ", "request"),
        ]
        for message_id, conversation_id, body, request_id in invalid_cases:
            with self.subTest(message_id=message_id, conversation_id=conversation_id, body=body):
                with self.assertRaises(ValueError):
                    self.backend.submit("opaque-a", message_id, conversation_id,
                                        ["AI-B"], body, request_id)

    def test_submit_rejects_invalid_recipient_container_and_values(self):
        invalid_recipients = [None, "AI-B", {"AI-B": True}, [], [None], ["   "]]
        for recipients in invalid_recipients:
            with self.subTest(recipients=recipients):
                with self.assertRaisesRegex(ValueError, "invalid_recipients"):
                    self.backend.submit("opaque-a", "m-invalid-recipient", "room-1",
                                        recipients, "body", "req-invalid-recipient")

    def test_concurrent_identical_submissions_are_idempotent(self):
        payload = ("opaque-a", "m-concurrent", "room-1", ["AI-B"],
                   "one logical message", "req-concurrent")
        with ThreadPoolExecutor(max_workers=12) as pool:
            messages = list(pool.map(lambda _: self.backend.submit(*payload), range(12)))
        self.assertEqual({message.message_id for message in messages}, {"m-concurrent"})
        self.assertEqual({message.sequence for message in messages}, {1})
        pending = self.backend.pending("opaque-b", "room-1")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].message_id, "m-concurrent")

    def test_concurrent_distinct_messages_receive_unique_ordered_sequences(self):
        def submit(index):
            return self.backend.submit(
                "opaque-a", f"m-parallel-{index}", "room-1", ["AI-B"],
                f"parallel-{index}", f"req-parallel-{index}")
        with ThreadPoolExecutor(max_workers=10) as pool:
            messages = list(pool.map(submit, range(10)))
        self.assertEqual(sorted(message.sequence for message in messages),
                         list(range(1, 11)))
        pending = self.backend.pending("opaque-b", "room-1", limit=100)
        self.assertEqual([message.sequence for message in pending],
                         list(range(1, 11)))

if __name__ == "__main__":
    unittest.main()
