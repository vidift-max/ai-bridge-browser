import tempfile
import unittest
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore

class MessengerBackendTest(unittest.TestCase):
    def setUp(self):
        self.backend = MessengerBackend({"opaque-a": "AI-A", "opaque-b": "AI-B"}, {"room-1": {"AI-A", "AI-B"}})

    def tearDown(self):
        self.backend.close()

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

    def test_body_limit_rejected(self):
        with self.assertRaises(ValueError):
            self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"x"*5001,"req-1")

    def test_pending_cursor(self):
        self.backend.submit("opaque-a","m-1","room-1",["AI-B"],"one","req-1")
        self.backend.submit("opaque-a","m-2","room-1",["AI-B"],"two","req-2")
        self.assertEqual([m.message_id for m in self.backend.pending("opaque-b","room-1",after_sequence=1)],["m-2"])


    def test_invitation_acceptance_adds_only_authenticated_target(self):
        tokens = {"opaque-a": "AI-A", "opaque-b": "AI-B", "opaque-c": "AI-C"}
        backend = MessengerBackend(tokens, {"room-1": {"AI-A", "AI-B"}})
        try:
            invitation = backend.create_invitation("opaque-a", "room-1", "AI-C")
            self.assertNotIn("token", str(backend._store._connection.execute(
                "SELECT token_hash FROM invitations").fetchone()[0]))
            result = backend.accept_invitation("opaque-c", invitation["token"])
            self.assertEqual(result["memberCount"], 3)
            self.assertEqual(result["memberAiIds"], ["AI-A", "AI-B", "AI-C"])
            with self.assertRaises(ValueError):
                backend.accept_invitation("opaque-c", invitation["token"])
        finally:
            backend.close()

    def test_invitation_rejects_wrong_target(self):
        tokens = {"opaque-a": "AI-A", "opaque-b": "AI-B", "opaque-c": "AI-C"}
        backend = MessengerBackend(tokens, {"room-1": {"AI-A", "AI-B"}})
        try:
            invitation = backend.create_invitation("opaque-a", "room-1", "AI-C")
            with self.assertRaises(ValueError):
                backend.accept_invitation("opaque-b", invitation["token"])
            self.assertEqual(backend._conversations["room-1"], {"AI-A", "AI-B"})
        finally:
            backend.close()

    def test_invitation_cannot_expand_private_conversation(self):
        backend = MessengerBackend(
            {"opaque-a": "AI-A", "opaque-b": "AI-B", "opaque-c": "AI-C"}, {})
        try:
            backend.create_conversation("opaque-a", "private-1",
                                        ["AI-A", "AI-B"], "PRIVATE")
            with self.assertRaisesRegex(ValueError, "private_conversation_cannot_expand"):
                backend.create_invitation("opaque-a", "private-1", "AI-C")
        finally:
            backend.close()

    def test_invitation_revocation_blocks_acceptance(self):
        tokens = {"opaque-a": "AI-A", "opaque-b": "AI-B", "opaque-c": "AI-C"}
        backend = MessengerBackend(tokens, {"room-1": {"AI-A", "AI-B"}})
        try:
            invitation = backend.create_invitation("opaque-a", "room-1", "AI-C")
            backend.revoke_invitation("opaque-a", invitation["invitationId"])
            with self.assertRaises(ValueError):
                backend.accept_invitation("opaque-c", invitation["token"])
        finally:
            backend.close()

    def test_invitation_target_must_be_provisioned(self):
        with self.assertRaisesRegex(ValueError, "unknown_invitation_target"):
            self.backend.create_invitation("opaque-a", "room-1", "AI-NOT-PROVISIONED")

if __name__ == "__main__":
    unittest.main()
