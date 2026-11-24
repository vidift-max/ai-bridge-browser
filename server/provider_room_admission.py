"""Room admission boundary for authenticated provider sessions.

This service binds an already-authenticated provider session to one durable room
membership. It does not perform provider login, network calls, or invite issuance.
"""
import sqlite3
import threading
import time


ROLES = frozenset(("COORDINATOR", "PARTICIPANT", "OBSERVER"))
ACTIONS = frozenset(("ADMIT_PROVIDER_SESSION", "REVOKE_PROVIDER_SESSION"))


class ProviderRoomAdmissionService:
    def __init__(self, connection: sqlite3.Connection, session_registry, authorize):
        if not callable(authorize):
            raise ValueError("admission_authorizer_required")
        self._connection = connection
        self._sessions = session_registry
        self._authorize = authorize
        self._lock = threading.RLock()
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS provider_room_admissions (
                session_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                ai_id TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('COORDINATOR','PARTICIPANT','OBSERVER')),
                credential_generation INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('ACTIVE','REVOKED')),
                admitted_at REAL NOT NULL,
                revoked_at REAL,
                PRIMARY KEY(session_id, conversation_id)
            )
        """)
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_provider_room_admissions_room "
            "ON provider_room_admissions(conversation_id,status,ai_id)"
        )
        self._connection.commit()

    @staticmethod
    def _text(value, error):
        if not isinstance(value, str) or not value.strip() or len(value) > 200:
            raise ValueError(error)
        return value.strip()

    def _authenticate(self, session_id, credential_generation, now):
        session_id = self._text(session_id, "invalid_session_id")
        if isinstance(credential_generation, bool) or not isinstance(credential_generation, int) or credential_generation < 1:
            raise ValueError("invalid_credential_generation")
        principal = self._sessions.authenticate_bound(session_id, credential_generation, now)
        if principal.session_id != session_id or principal.status != "ACTIVE":
            raise PermissionError("provider_session_not_active")
        return principal

    def admit(self, session_id, conversation_id, provider_id, role, credential_generation,
              authorization, now=None):
        conversation_id = self._text(conversation_id, "invalid_conversation_id")
        provider_id = self._text(provider_id, "invalid_provider_id")
        session_id = self._text(session_id, "invalid_session_id")
        if not isinstance(role, str) or role not in ROLES:
            raise ValueError("invalid_room_role")
        principal = self._authenticate(session_id, credential_generation, None)
        if not authorization or self._authorize(
                session_id=session_id, action="ADMIT_PROVIDER_SESSION",
                conversation_id=conversation_id, provider_id=provider_id,
                role=role, authorization=authorization) is not True:
            raise PermissionError("provider_room_admission_not_authorized")
        if isinstance(now, bool):
            raise ValueError("invalid_admission_timestamp")
        timestamp = time.time() if now is None else float(now)
        if timestamp <= 0:
            raise ValueError("invalid_admission_timestamp")
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                existing = self._connection.execute(
                    "SELECT * FROM provider_room_admissions WHERE session_id=? AND conversation_id=?",
                    (session_id, conversation_id)).fetchone()
                if existing and existing["status"] == "ACTIVE":
                    self._connection.rollback()
                    raise ValueError("provider_session_already_admitted")
                if role == "COORDINATOR":
                    coordinator = self._connection.execute(
                        """SELECT 1 FROM provider_room_admissions
                           WHERE conversation_id=? AND role='COORDINATOR' AND status='ACTIVE'""",
                        (conversation_id,)).fetchone()
                    if coordinator:
                        self._connection.rollback()
                        raise ValueError("room_coordinator_already_assigned")
                self._connection.execute(
                    """INSERT INTO provider_room_admissions
                       (session_id,conversation_id,ai_id,provider_id,role,
                        credential_generation,status,admitted_at,revoked_at)
                       VALUES(?,?,?,?,?,?,'ACTIVE',?,NULL)
                       ON CONFLICT(session_id,conversation_id) DO UPDATE SET
                         ai_id=excluded.ai_id, provider_id=excluded.provider_id,
                         role=excluded.role, credential_generation=excluded.credential_generation,
                         status='ACTIVE', admitted_at=excluded.admitted_at, revoked_at=NULL""",
                    (session_id, conversation_id, principal.ai_id, provider_id,
                     role, credential_generation, timestamp))
                self._connection.commit()
            except Exception:
                if self._connection.in_transaction:
                    self._connection.rollback()
                raise
        return {"sessionId": session_id, "conversationId": conversation_id,
                "aiId": principal.ai_id, "providerId": provider_id,
                "role": role, "status": "ACTIVE", "admittedAt": timestamp}

    def list_room(self, requester_session_id, conversation_id, credential_generation, now=None):
        conversation_id = self._text(conversation_id, "invalid_conversation_id")
        principal = self._authenticate(requester_session_id, credential_generation, now)
        with self._lock:
            requester = self._connection.execute(
                """SELECT 1 FROM provider_room_admissions
                   WHERE session_id=? AND conversation_id=? AND ai_id=? AND status='ACTIVE'""",
                (requester_session_id, conversation_id, principal.ai_id)).fetchone()
            if requester is None:
                raise PermissionError("provider_room_membership_required")
            rows = self._connection.execute(
                """SELECT session_id,ai_id,provider_id,role,status,admitted_at
                   FROM provider_room_admissions
                   WHERE conversation_id=? AND status='ACTIVE'
                   ORDER BY admitted_at,ai_id""", (conversation_id,)).fetchall()
        return [{"sessionId": row["session_id"], "aiId": row["ai_id"],
                 "providerId": row["provider_id"], "role": row["role"],
                 "status": row["status"], "admittedAt": row["admitted_at"]}
                for row in rows]

    def revoke(self, actor_session_id, target_session_id, conversation_id,
               actor_generation, authorization, now=None):
        conversation_id = self._text(conversation_id, "invalid_conversation_id")
        actor = self._authenticate(actor_session_id, actor_generation, now)
        if not authorization or self._authorize(
                session_id=actor_session_id, action="REVOKE_PROVIDER_SESSION",
                conversation_id=conversation_id, target_session_id=target_session_id,
                actor_ai_id=actor.ai_id, authorization=authorization) is not True:
            raise PermissionError("provider_room_revocation_not_authorized")
        timestamp = time.time() if now is None else float(now)
        if timestamp <= 0:
            raise ValueError("invalid_admission_timestamp")
        with self._lock:
            cursor = self._connection.execute(
                """UPDATE provider_room_admissions SET status='REVOKED',revoked_at=?
                   WHERE session_id=? AND conversation_id=? AND status='ACTIVE'""",
                (timestamp, target_session_id, conversation_id))
            self._connection.commit()
        return cursor.rowcount == 1
