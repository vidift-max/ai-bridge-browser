import sqlite3
import unittest
from datetime import datetime, timezone

from server.provider_room_admission import ProviderRoomAdmissionService
from server.session_registry import SessionRegistry


class ProviderRoomAdmissionTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.sessions = SessionRegistry()
        self.sessions.create("session-a", "AI-GPT-6", credential_generation=1)
        self.sessions.create("session-b", "AI-CLAUDE-01", credential_generation=1)
        self.authorized = True

        def authorize(**_kwargs):
            return self.authorized

        self.service = ProviderRoomAdmissionService(self.db, self.sessions, authorize)
        self.auth = "explicit-host-approval"

    def tearDown(self):
        self.db.close()

    def admit(self, session="session-a", ai_provider="openai", role="COORDINATOR"):
        ai_id = "AI-GPT-6" if session == "session-a" else "AI-CLAUDE-01"
        return self.service.admit(session, "room-1", ai_provider, role, 1, self.auth, now=1000)

    def test_admission_binds_authenticated_identity_and_provider_to_room(self):
        result = self.admit()
        self.assertEqual(result, {
            "sessionId": "session-a", "conversationId": "room-1",
            "aiId": "AI-GPT-6", "providerId": "openai",
            "role": "COORDINATOR", "status": "ACTIVE", "admittedAt": 1000.0,
        })

    def test_unapproved_admission_fails_closed(self):
        self.authorized = False
        with self.assertRaisesRegex(PermissionError, "provider_room_admission_not_authorized"):
            self.admit()
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM provider_room_admissions").fetchone()[0], 0)

    def test_session_identity_cannot_be_spoofed_by_caller(self):
        self.admit()
        rows = self.service.list_room("session-a", "room-1", 1)
        self.assertEqual(rows[0]["aiId"], "AI-GPT-6")

    def test_nonmember_cannot_list_room(self):
        with self.assertRaisesRegex(PermissionError, "provider_room_membership_required"):
            self.service.list_room("session-b", "room-1", 1)

    def test_multiple_provider_sessions_can_join_same_collective_room(self):
        self.admit()
        self.service.admit("session-b", "room-1", "anthropic", "PARTICIPANT", 1, self.auth, now=1001)
        rows = self.service.list_room("session-a", "room-1", 1)
        self.assertEqual({row["aiId"] for row in rows}, {"AI-GPT-6", "AI-CLAUDE-01"})
        self.assertEqual({row["providerId"] for row in rows}, {"openai", "anthropic"})

    def test_room_allows_only_one_active_coordinator(self):
        self.admit()
        with self.assertRaisesRegex(ValueError, "room_coordinator_already_assigned"):
            self.admit("session-b", "anthropic", "COORDINATOR")

    def test_duplicate_active_admission_is_rejected(self):
        self.admit()
        with self.assertRaisesRegex(ValueError, "provider_session_already_admitted"):
            self.admit()

    def test_revoked_admission_disappears_from_room_listing(self):
        self.admit()
        self.service.admit("session-b", "room-1", "anthropic", "PARTICIPANT", 1, self.auth, now=1001)
        self.assertTrue(self.service.revoke("session-a", "session-b", "room-1", 1, self.auth, now=1002))
        self.assertEqual([row["sessionId"] for row in self.service.list_room("session-a", "room-1", 1)], ["session-a"])

    def test_revocation_requires_explicit_authorization(self):
        self.admit()
        self.authorized = False
        with self.assertRaisesRegex(PermissionError, "provider_room_revocation_not_authorized"):
            self.service.revoke("session-a", "session-a", "room-1", 1, self.auth, now=1002)

    def test_revoked_session_generation_cannot_be_reused(self):
        self.admit()
        self.sessions.revoke("session-a")
        with self.assertRaises(PermissionError):
            self.service.list_room("session-a", "room-1", 1)

    def test_credential_rotation_invalidates_old_room_binding(self):
        self.admit()
        self.sessions.rotate("session-a", "session-a-new")
        with self.assertRaises(PermissionError):
            self.service.list_room("session-a", "room-1", 1)

    def test_expired_or_unknown_sessions_cannot_enter(self):
        with self.assertRaises(PermissionError):
            self.service.admit("unknown", "room-1", "openai", "PARTICIPANT", 1, self.auth)
        self.sessions.create("expired", "AI-EXPIRED", expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
        with self.assertRaises(PermissionError):
            self.service.admit("expired", "room-1", "openai", "PARTICIPANT", 1, self.auth)

    def test_role_and_identity_fields_are_validated(self):
        for role in ("ADMIN", "", None):
            with self.subTest(role=role), self.assertRaises(ValueError):
                self.service.admit("session-a", "room-1", "openai", role, 1, self.auth)
        for room in ("", "x" * 201):
            with self.subTest(room=room), self.assertRaises(ValueError):
                self.service.admit("session-a", room, "openai", "PARTICIPANT", 1, self.auth)

    def test_room_admission_persists_across_service_reopen(self):
        self.admit()
        reopened = ProviderRoomAdmissionService(self.db, self.sessions, lambda **_kwargs: True)
        self.assertEqual(reopened.list_room("session-a", "room-1", 1)[0]["aiId"], "AI-GPT-6")


if __name__ == "__main__":
    unittest.main()
