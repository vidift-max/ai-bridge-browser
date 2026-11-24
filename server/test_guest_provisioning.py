import tempfile
import threading
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from server.auth import Authenticator
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore
from server.recovery import verify_messenger_schema, verify_messenger_data_consistency


class GuestCredentialProvisioningTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = self.temp.name + "/messenger.sqlite"
        self.tokens = {"admin-token": "AI-ADMIN", "member-token": "AI-MEMBER"}
        self.store = SQLiteMessengerStore(self.path)
        self.auth = Authenticator(self.tokens)
        self.backend = MessengerBackend(
            self.tokens, {}, self.store, authenticator=self.auth)
        self.backend.create_conversation(
            "admin-token", "room-a", ["AI-ADMIN", "AI-MEMBER"], "GROUP")
        self.backend.create_conversation(
            "admin-token", "room-b", ["AI-ADMIN", "AI-MEMBER"], "GROUP")
        self.invite = self.backend.create_room_invite(
            "admin-token", "room-a", expires_in_seconds=600, max_uses=5)
        self.application = self.backend.submit_public_guest_application({
            "inviteToken": self.invite["token"],
            "displayName": "External Guest",
            "providerClaim": "CLAUDE",
        })
        self.backend.decide_guest_application(
            "admin-token", "room-a", self.application["applicationId"], "APPROVE")

    def tearDown(self):
        try:
            self.backend.close()
        finally:
            self.temp.cleanup()

    def provision(self):
        return self.backend.provision_guest_application(
            "admin-token", "room-a", self.application["applicationId"])

    def test_admin_provisions_one_identity_with_room_scoped_access(self):
        result = self.provision()
        ai_id = result["identity"]["aiId"]
        token = result["credential"]
        self.assertTrue(ai_id.startswith("AI-GUEST-"))
        self.assertEqual(result["identity"]["displayName"], "External Guest")
        self.assertTrue(result["credentialShownOnce"])
        self.assertFalse(result["providerVerified"])
        self.assertEqual(result["roomAccess"], "INVITED_ROOM_ONLY")
        self.assertEqual(self.backend.authenticate(token), ai_id)
        self.assertIn(ai_id, self.backend.conversation_members()["room-a"])
        self.assertNotIn(ai_id, self.backend.conversation_members()["room-b"])
        self.assertFalse(self.store.is_conversation_admin("room-a", ai_id))
        row = self.store._connection.execute(
            "SELECT token_hash FROM credential_records WHERE ai_id=?", (ai_id,)).fetchone()
        self.assertEqual(len(row["token_hash"]), 64)
        self.assertNotEqual(row["token_hash"], token)

    def test_only_approved_application_can_be_provisioned(self):
        invite = self.backend.create_room_invite(
            "admin-token", "room-a", expires_in_seconds=600, max_uses=2)
        pending = self.backend.submit_public_guest_application({
            "inviteToken": invite["token"], "displayName": "Pending Guest",
            "providerClaim": "OTHER"})
        with self.assertRaisesRegex(ValueError, "guest_application_unavailable"):
            self.backend.provision_guest_application(
                "admin-token", "room-a", pending["applicationId"])

    def test_application_cannot_be_provisioned_through_another_room_route(self):
        with self.assertRaisesRegex(ValueError, "guest_application_unavailable"):
            self.backend.provision_guest_application(
                "admin-token", "room-b", self.application["applicationId"])
        self.assertNotIn("AI-GUEST", ",".join(self.backend.conversation_members()["room-b"]))

    def test_non_admin_cannot_provision(self):
        with self.assertRaisesRegex(PermissionError, "room_admin_required"):
            self.backend.provision_guest_application(
                "member-token", "room-a", self.application["applicationId"])

    def test_provisioning_is_one_time_and_replay_safe(self):
        first = self.provision()
        with self.assertRaisesRegex(ValueError, "guest_application_unavailable"):
            self.provision()
        self.assertEqual(
            self.store._connection.execute(
                "SELECT COUNT(*) FROM credential_records WHERE ai_id=?",
                (first["identity"]["aiId"],)).fetchone()[0], 1)

    def test_credential_and_membership_survive_backend_restart(self):
        first = self.provision()
        token = first["credential"]
        ai_id = first["identity"]["aiId"]
        self.backend.close()
        new_store = SQLiteMessengerStore(self.path)
        new_backend = MessengerBackend(
            self.tokens, {}, new_store, authenticator=Authenticator(self.tokens))
        try:
            self.assertEqual(new_backend.authenticate(token), ai_id)
            self.assertIn(ai_id, new_backend.conversation_members()["room-a"])
            self.assertNotIn(ai_id, new_backend.conversation_members()["room-b"])
        finally:
            new_backend.close()

    def test_admin_revocation_invalidates_credential_and_removes_room_access(self):
        result = self.provision()
        ai_id, token = result["identity"]["aiId"], result["credential"]
        revoked = self.backend.revoke_guest_provisioning(
            "admin-token", "room-a", self.application["applicationId"])
        self.assertEqual(revoked["status"], "REVOKED")
        self.assertNotIn(ai_id, self.backend.conversation_members()["room-a"])
        with self.assertRaisesRegex(PermissionError, "authentication_required"):
            self.backend.authenticate(token)
        status = self.store._connection.execute(
            "SELECT status FROM credential_records WHERE ai_id=?", (ai_id,)).fetchone()[0]
        self.assertEqual(status, "REVOKED")

    def test_revocation_wakes_waiting_long_poll_and_revalidates_access(self):
        provisioned = self.provision()
        guest_token = provisioned["credential"]

        waiting = threading.Event()
        outcome = {}

        def poll():
            try:
                outcome["messages"] = self.backend.wait_for_messages(
                    guest_token, "room-a", after_sequence=0, limit=10,
                    timeout_seconds=5)
            except Exception as exc:
                outcome["error"] = exc

        original_wait = self.backend._message_condition.wait

        def observed_wait(timeout=None):
            waiting.set()
            return original_wait(timeout)

        with patch.object(self.backend._message_condition, "wait",
                          side_effect=observed_wait):
            worker = threading.Thread(target=poll)
            worker.start()
            self.assertTrue(waiting.wait(2), "long poll did not enter wait")
            self.backend.revoke_guest_provisioning(
                "admin-token", "room-a", self.application["applicationId"])
            worker.join(2)

        self.assertFalse(worker.is_alive(), "revoked long poll was not woken promptly")
        self.assertIsInstance(outcome.get("error"), PermissionError)
        self.assertNotIn("messages", outcome)

    def test_revoked_guest_cannot_read_submit_or_acknowledge(self):
        provisioned = self.provision()
        guest_token = provisioned["credential"]
        guest_ai_id = provisioned["identity"]["aiId"]
        message = self.backend.submit(
            "admin-token", "revocation-operation-message", "room-a",
            [guest_ai_id], "message before revocation",
            "revocation-operation-request")

        revoked = self.backend.revoke_guest_provisioning(
            "admin-token", "room-a", self.application["applicationId"])
        self.assertEqual(revoked["status"], "REVOKED")

        operations = (
            ("read_pending", lambda: self.backend.pending(
                guest_token, "room-a")),
            ("submit_message", lambda: self.backend.submit(
                guest_token, "revoked-guest-message", "room-a",
                ["AI-ADMIN"], "must not be sent", "revoked-guest-request")),
            ("acknowledge_message", lambda: self.backend.acknowledge(
                guest_token, message.message_id)),
            ("long_poll", lambda: self.backend.wait_for_messages(
                guest_token, "room-a", after_sequence=0, limit=10,
                timeout_seconds=0)),
        )
        for operation, invoke in operations:
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(
                        PermissionError, "authentication_required"):
                    invoke()

        stored = self.store._connection.execute(
            "SELECT status FROM credential_records WHERE ai_id=?",
            (guest_ai_id,),
        ).fetchone()
        self.assertEqual(stored["status"], "REVOKED")
        self.assertNotIn(
            "revoked-guest-message",
            {row["message_id"] for row in self.store._connection.execute(
                "SELECT message_id FROM messages").fetchall()},
        )

    def test_revocation_survives_backend_restart(self):
        result = self.provision()
        token = result["credential"]
        ai_id = result["identity"]["aiId"]
        self.backend.revoke_guest_provisioning(
            "admin-token", "room-a", self.application["applicationId"])
        self.backend.close()
        new_store = SQLiteMessengerStore(self.path)
        new_backend = MessengerBackend(
            self.tokens, {}, new_store, authenticator=Authenticator(self.tokens))
        try:
            with self.assertRaisesRegex(PermissionError, "authentication_required"):
                new_backend.authenticate(token)
            self.assertNotIn(ai_id, new_backend.conversation_members()["room-a"])
        finally:
            new_backend.close()

    def test_revocation_wakes_all_concurrent_long_polls(self):
        provisioned = self.provision()
        guest_token = provisioned["credential"]
        waiter_count = 8
        waiting_count = 0
        count_lock = threading.Lock()
        all_waiting = threading.Event()
        outcomes = [{} for _ in range(waiter_count)]

        def poll(index):
            try:
                outcomes[index]["messages"] = self.backend.wait_for_messages(
                    guest_token, "room-a", after_sequence=0, limit=10,
                    timeout_seconds=5)
            except Exception as exc:
                outcomes[index]["error"] = exc

        original_wait = self.backend._message_condition.wait

        def observed_wait(timeout=None):
            nonlocal waiting_count
            with count_lock:
                waiting_count += 1
                if waiting_count == waiter_count:
                    all_waiting.set()
            return original_wait(timeout)

        with patch.object(self.backend._message_condition, "wait",
                          side_effect=observed_wait):
            workers = [
                threading.Thread(target=poll, args=(index,))
                for index in range(waiter_count)
            ]
            for worker in workers:
                worker.start()
            self.assertTrue(
                all_waiting.wait(3),
                "not all long polls entered the condition wait",
            )
            self.backend.revoke_guest_provisioning(
                "admin-token", "room-a", self.application["applicationId"])
            for worker in workers:
                worker.join(2)

        self.assertTrue(
            all(not worker.is_alive() for worker in workers),
            "revocation did not wake every waiting long poll",
        )
        self.assertEqual(len(outcomes), waiter_count)
        for outcome in outcomes:
            self.assertIsInstance(outcome.get("error"), PermissionError)
            self.assertNotIn("messages", outcome)

    def test_credential_expiry_is_enforced(self):
        result = self.provision()
        token = result["credential"]
        future = datetime.now(timezone.utc) + timedelta(days=31)
        self.assertEqual(self.auth._registry.status(token, now=future), "EXPIRED")
        with self.assertRaisesRegex(PermissionError, "authentication_required"):
            self.auth._registry.authenticate(token, now=future)

    def test_read_only_restore_validation_accepts_active_and_revoked_guest_records(self):
        self.provision()
        self.assertEqual(verify_messenger_schema(self.path), (True, "RESTORE_SCHEMA_COMPATIBLE"))
        self.assertEqual(verify_messenger_data_consistency(self.path),
                         (True, "RESTORE_DATA_CONSISTENT"))
        self.backend.revoke_guest_provisioning(
            "admin-token", "room-a", self.application["applicationId"])
        self.assertEqual(verify_messenger_data_consistency(self.path),
                         (True, "RESTORE_DATA_CONSISTENT"))

    def test_credential_activation_failure_fails_closed(self):
        with patch.object(
                self.backend._authenticator,
                "activate_persisted_credential",
                side_effect=RuntimeError("registry activation failed")):
            with self.assertRaisesRegex(RuntimeError, "registry activation failed"):
                self.provision()

        members = self.backend.conversation_members()["room-a"]
        self.assertFalse(any(ai_id.startswith("AI-GUEST-") for ai_id in members))

        application = self.store._connection.execute(
            """SELECT provisioning_status, provisioned_ai_id
               FROM guest_applications WHERE application_id=?""",
            (self.application["applicationId"],),
        ).fetchone()
        self.assertEqual(application["provisioning_status"], "REVOKED")
        self.assertIsNotNone(application["provisioned_ai_id"])

        credential = self.store._connection.execute(
            """SELECT status FROM credential_records WHERE ai_id=?""",
            (application["provisioned_ai_id"],),
        ).fetchone()
        self.assertEqual(credential["status"], "REVOKED")

    def test_concurrent_provisioning_issues_at_most_one_credential(self):
        outcomes = []
        def worker():
            try:
                outcomes.append(("ok", self.provision()))
            except ValueError:
                outcomes.append(("blocked", None))
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        self.assertEqual(sum(kind == "ok" for kind, _ in outcomes), 1)
        self.assertEqual(sum(kind == "blocked" for kind, _ in outcomes), 1)


if __name__ == "__main__":
    unittest.main()
