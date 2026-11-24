import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore
from server.audio_blob_store import AudioBlobStore

class MessengerBackendTest(unittest.TestCase):
    def setUp(self):
        self.backend = MessengerBackend({"opaque-a": "AI-A", "opaque-b": "AI-B", "opaque-c": "AI-C", "opaque-d": "AI-D"}, {"room-1": {"AI-A", "AI-B"}})

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

    def test_group_message_fans_out_only_to_selected_room_members(self):
        self.backend.create_conversation(
            "opaque-a", "multi-ai-room", ["AI-A", "AI-B", "AI-C", "AI-D"], "GROUP")
        message = self.backend.submit(
            "opaque-a", "multi-ai-group-msg", "multi-ai-room",
            ["AI-B", "AI-C"], "coordenação entre IAs", "multi-ai-group-req")
        self.assertEqual(message.recipient_ai_ids, ("AI-B", "AI-C"))
        self.assertEqual(self.backend.pending("opaque-b", "multi-ai-room")[0].body,
                         "coordenação entre IAs")
        self.assertEqual(self.backend.pending("opaque-c", "multi-ai-room")[0].body,
                         "coordenação entre IAs")
        self.assertEqual(self.backend.pending("opaque-d", "multi-ai-room"), [])

    def test_group_message_rejects_recipient_outside_room(self):
        self.backend.create_conversation(
            "opaque-a", "multi-ai-private-room", ["AI-A", "AI-B"], "PRIVATE")
        with self.assertRaisesRegex(PermissionError, "recipient_authorization_denied"):
            self.backend.submit(
                "opaque-a", "multi-ai-leak-msg", "multi-ai-private-room",
                ["AI-C"], "must not leak", "multi-ai-leak-req")

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

    def test_list_conversations_returns_only_authenticated_memberships(self):
        self.backend.create_conversation(
            "opaque-a", "private-a", ["AI-A", "AI-B"], "PRIVATE")
        self.backend.create_conversation(
            "opaque-b", "private-b", ["AI-B", "AI-A"], "PRIVATE")
        result_a = self.backend.list_conversations("opaque-a")
        result_b = self.backend.list_conversations("opaque-b")
        self.assertEqual(
            [item["conversationId"] for item in result_a["conversations"]],
            ["private-a", "private-b", "room-1"])
        self.assertEqual(
            [item["conversationId"] for item in result_b["conversations"]],
            ["private-a", "private-b", "room-1"])
        self.assertEqual(result_a["conversations"][0]["kind"], "PRIVATE")
        self.assertEqual(result_a["conversations"][0]["memberAiIds"],
                         ["AI-A", "AI-B"])

    def test_list_conversations_paginates_with_stable_exclusive_cursor(self):
        for room_id in ("room-a", "room-b", "room-c"):
            self.backend.create_conversation(
                "opaque-a", room_id, ["AI-A", "AI-B"], "GROUP")
        first = self.backend.list_conversations("opaque-a", limit=2)
        second = self.backend.list_conversations(
            "opaque-a", limit=2, after=first["nextCursor"])
        self.assertEqual(
            [item["conversationId"] for item in first["conversations"]],
            ["room-1", "room-a"])
        self.assertEqual(
            [item["conversationId"] for item in second["conversations"]],
            ["room-b", "room-c"])
        self.assertIsNone(second["nextCursor"])

    def test_list_conversations_rejects_invalid_auth_limit_and_cursor(self):
        with self.assertRaises(PermissionError):
            self.backend.list_conversations("invalid-token")
        for limit in (0, 101, True, "10"):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(ValueError, "invalid_conversation_limit"):
                    self.backend.list_conversations("opaque-a", limit=limit)
        with self.assertRaisesRegex(ValueError, "invalid_conversation_cursor"):
            self.backend.list_conversations("opaque-a", after=None)


    def test_room_invite_requires_creator_admin_and_approval_before_membership(self):
        self.backend.create_conversation(
            "opaque-a", "invite-room", ["AI-A", "AI-B"], "GROUP")
        with self.assertRaisesRegex(PermissionError, "room_admin_required"):
            self.backend.create_room_invite("opaque-b", "invite-room")
        invite = self.backend.create_room_invite(
            "opaque-a", "invite-room", expires_in_seconds=600, max_uses=2)
        self.assertNotIn("token", self.backend.get_public_invite(invite["inviteId"]))
        self.assertEqual(
            self.backend.get_public_invite(invite["inviteId"])["status"], "ACTIVE")
        request = self.backend.redeem_room_invite("opaque-c", invite["token"])
        self.assertEqual(request["status"], "PENDING")
        self.assertNotIn("AI-C", self.backend.conversation_members()["invite-room"])
        repeated = self.backend.redeem_room_invite("opaque-c", invite["token"])
        self.assertEqual(repeated["requestId"], request["requestId"])
        pending = self.backend.list_join_requests("opaque-a", "invite-room")
        self.assertEqual([item["ai_id"] for item in pending], ["AI-C"])
        approved = self.backend.decide_join_request(
            "opaque-a", "invite-room", request["requestId"], "APPROVE")
        self.assertEqual(approved["status"], "APPROVED")
        self.assertIn("AI-C", self.backend.conversation_members()["invite-room"])

    def test_room_invite_reject_revocation_and_token_hash_storage(self):
        self.backend.create_conversation(
            "opaque-a", "invite-revoke-room", ["AI-A", "AI-B"], "GROUP")
        invite = self.backend.create_room_invite("opaque-a", "invite-revoke-room")
        stored = self.backend._store.get_room_invite(invite["inviteId"])
        self.assertNotEqual(stored["token_hash"], invite["token"])
        self.assertEqual(len(stored["token_hash"]), 64)
        revoked = self.backend.revoke_room_invite(
            "opaque-a", "invite-revoke-room", invite["inviteId"])
        self.assertEqual(revoked["status"], "REVOKED")
        self.assertEqual(
            self.backend.get_public_invite(invite["inviteId"])["status"], "REVOKED")
        with self.assertRaisesRegex(ValueError, "invite_unavailable"):
            self.backend.redeem_room_invite("opaque-c", invite["token"])

    def test_join_request_rejection_does_not_add_member(self):
        self.backend.create_conversation(
            "opaque-a", "invite-reject-room", ["AI-A", "AI-B"], "GROUP")
        invite = self.backend.create_room_invite("opaque-a", "invite-reject-room")
        request = self.backend.redeem_room_invite("opaque-c", invite["token"])
        rejected = self.backend.decide_join_request(
            "opaque-a", "invite-reject-room", request["requestId"], "REJECT")
        self.assertEqual(rejected["status"], "REJECTED")
        self.assertNotIn("AI-C", self.backend.conversation_members()["invite-reject-room"])


    def test_room_invite_expiry_and_use_limit_are_enforced(self):
        self.backend.create_conversation(
            "opaque-a", "invite-limit-room", ["AI-A", "AI-B"], "GROUP")
        invite = self.backend.create_room_invite(
            "opaque-a", "invite-limit-room", expires_in_seconds=60, max_uses=1)
        self.backend.redeem_room_invite("opaque-c", invite["token"])
        with self.assertRaisesRegex(ValueError, "invite_unavailable"):
            self.backend.redeem_room_invite("opaque-d", invite["token"])
        self.assertEqual(
            self.backend.get_public_invite(invite["inviteId"])["status"], "EXHAUSTED")

        expiring = self.backend.create_room_invite(
            "opaque-a", "invite-limit-room", expires_in_seconds=60, max_uses=2)
        with patch("server.messenger_backend.time.time",
                   return_value=expiring["expiresAt"] + 1):
            with self.assertRaisesRegex(ValueError, "invite_unavailable"):
                self.backend.redeem_room_invite("opaque-d", expiring["token"])

    def test_invites_admin_and_membership_survive_backend_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/messenger.sqlite"
            first = MessengerBackend(
                {"opaque-a": "AI-A", "opaque-b": "AI-B", "opaque-c": "AI-C"},
                {}, SQLiteMessengerStore(path))
            first.create_conversation("opaque-a", "persistent-invite-room",
                                      ["AI-A", "AI-B"], "GROUP")
            invite = first.create_room_invite(
                "opaque-a", "persistent-invite-room")
            first.close()

            second = MessengerBackend(
                {"opaque-a": "AI-A", "opaque-b": "AI-B", "opaque-c": "AI-C"},
                {}, SQLiteMessengerStore(path))
            request = second.redeem_room_invite("opaque-c", invite["token"])
            second.decide_join_request(
                "opaque-a", "persistent-invite-room", request["requestId"], "APPROVE")
            second.close()

            third = MessengerBackend(
                {"opaque-a": "AI-A", "opaque-b": "AI-B", "opaque-c": "AI-C"},
                {}, SQLiteMessengerStore(path))
            self.assertIn("AI-C", third.conversation_members()["persistent-invite-room"])
            approved = third._store.list_join_requests(
                "persistent-invite-room", status="APPROVED")
            self.assertEqual(approved[0]["status"], "APPROVED")
            third.close()

    def test_long_poll_returns_immediately_when_message_is_pending(self):
        self.backend.submit("opaque-a", "long-poll-immediate", "room-1", ["AI-B"], "hello", "long-poll-immediate-req")
        messages = self.backend.wait_for_messages("opaque-b", "room-1", after_sequence=0, limit=10, timeout_seconds=0)
        self.assertEqual([message.message_id for message in messages], ["long-poll-immediate"])

    def test_long_poll_times_out_with_empty_result(self):
        messages = self.backend.wait_for_messages("opaque-b", "room-1", after_sequence=0, limit=10, timeout_seconds=0)
        self.assertEqual(messages, [])

    def test_long_poll_wakes_when_new_message_is_submitted(self):
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                self.backend.wait_for_messages,
                "opaque-b", "room-1", 0, 10, 5)
            self.backend.submit(
                "opaque-a", "long-poll-wakeup", "room-1", ["AI-B"],
                "wake up", "long-poll-wakeup-req")
            messages = future.result(timeout=2)
        self.assertEqual([message.message_id for message in messages], ["long-poll-wakeup"])

    def test_long_poll_rejects_invalid_timeout(self):
        for timeout in (-1, 26, True, "20"):
            with self.subTest(timeout=timeout):
                with self.assertRaisesRegex(ValueError, "invalid_wait_timeout"):
                    self.backend.wait_for_messages(
                        "opaque-b", "room-1", 0, 10, timeout)


    def test_long_poll_rejects_non_finite_and_over_limit_timeouts(self):
        for timeout in (float("nan"), float("inf"), float("-inf"), 25.01, 10 ** 1000):
            with self.subTest(timeout=timeout):
                with self.assertRaisesRegex(ValueError, "invalid_wait_timeout"):
                    self.backend.wait_for_messages(
                        "opaque-b", "room-1", 0, 10, timeout)

    def test_long_poll_rejects_invalid_cursor_types_and_bounds(self):
        invalid_cursors = (True, False, -1, 1.5, "1", 9007199254740992)
        for cursor in invalid_cursors:
            with self.subTest(cursor=cursor):
                with self.assertRaisesRegex(ValueError, "invalid_cursor"):
                    self.backend.wait_for_messages(
                        "opaque-b", "room-1", cursor, 10, 0)

    def test_long_poll_rejects_invalid_batch_types_and_bounds(self):
        invalid_limits = (True, False, 0, -1, 101, 1.5, "10")
        for limit in invalid_limits:
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(ValueError, "invalid_cursor"):
                    self.backend.wait_for_messages(
                        "opaque-b", "room-1", 0, limit, 0)

    def test_pending_uses_same_strict_cursor_and_batch_validation(self):
        for cursor, limit in ((True, 10), (-1, 10), (0, True), (0, 101),
                              (9007199254740992, 10)):
            with self.subTest(cursor=cursor, limit=limit):
                with self.assertRaisesRegex(ValueError, "invalid_cursor"):
                    self.backend.pending(
                        "opaque-b", "room-1", after_sequence=cursor, limit=limit)

    def test_long_poll_accepts_maximum_safe_cursor_and_zero_wait(self):
        self.assertEqual(
            self.backend.wait_for_messages(
                "opaque-b", "room-1", 9007199254740991, 1, 0),
            [],
        )

    def test_transport_capabilities_are_authorized_and_conservative(self):
        capabilities = self.backend.transport_capabilities("opaque-b", "room-1")
        self.assertEqual(capabilities["contractVersion"], 1)
        self.assertEqual(capabilities["conversationId"], "room-1")
        self.assertTrue(capabilities["authorized"])
        self.assertEqual(capabilities["defaultTransport"], "HTTP_LONG_POLL")
        self.assertEqual(capabilities["transports"]["httpLongPoll"]["minWaitSeconds"], 0)
        self.assertEqual(capabilities["transports"]["httpLongPoll"]["maxWaitSeconds"], 25)
        self.assertEqual(capabilities["transports"]["httpLongPoll"]["defaultWaitSeconds"], 20)
        self.assertEqual(capabilities["transports"]["httpLongPoll"]["maxBatchSize"], 100)
        self.assertFalse(capabilities["transports"]["webSocket"]["enabled"])
        self.assertFalse(capabilities["transports"]["serverPush"]["enabled"])
        self.assertEqual(capabilities["cursor"], {"type": "sequence", "ackRequired": True})

    def test_transport_capabilities_fail_closed_for_non_member(self):
        with self.assertRaisesRegex(PermissionError, "authorization_denied"):
            self.backend.transport_capabilities("opaque-c", "room-1")

    def test_transport_capabilities_require_valid_credentials(self):
        with self.assertRaises(PermissionError):
            self.backend.transport_capabilities("not-a-valid-token", "room-1")

    def test_transport_contract_limits_match_long_poll_enforcement(self):
        capabilities = self.backend.transport_capabilities("opaque-b", "room-1")
        poll = capabilities["transports"]["httpLongPoll"]
        self.assertLessEqual(poll["maxWaitSeconds"], 25)
        self.assertLessEqual(poll["maxBatchSize"], 100)
        self.assertLessEqual(poll["defaultWaitSeconds"], poll["maxWaitSeconds"])

if __name__ == "__main__":
    unittest.main()