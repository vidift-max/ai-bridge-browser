"""Persistent, authenticated AI-PHONE number registry.

Numbers and serials are allocated only by the server and are never recycled.
A registry record is created only after the caller has authenticated elsewhere.
"""
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


_AI_ID = re.compile(r"^AI-[A-Z0-9][A-Z0-9-]{1,62}$")


class IdentityRegistry:
    def __init__(self, database_path: str):
        if not database_path:
            raise ValueError("database_path_required")
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(database_path, timeout=10, isolation_level=None,
                                   check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA busy_timeout=10000")
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS ai_phone_registry (
                ai_id TEXT PRIMARY KEY,
                display_number TEXT NOT NULL UNIQUE,
                serial TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                provider TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('ACTIVE','SUSPENDED','REVOKED')),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ai_phone_registry_sequence (
                sequence_id INTEGER PRIMARY KEY CHECK(sequence_id=1),
                next_number INTEGER NOT NULL CHECK(next_number > 0)
            );
            INSERT OR IGNORE INTO ai_phone_registry_sequence(sequence_id,next_number)
                VALUES(1,1);
        """)

    def close(self):
        self._db.close()

    @staticmethod
    def _validate_ai_id(ai_id: str):
        if not isinstance(ai_id, str) or not _AI_ID.fullmatch(ai_id):
            raise ValueError("invalid_ai_id")

    @staticmethod
    def _public_record(row):
        if row is None:
            return None
        return {
            "aiId": row["ai_id"],
            "displayNumber": row["display_number"],
            "serial": row["serial"],
            "displayName": row["display_name"],
            "provider": row["provider"],
            "status": row["status"],
            "createdAt": row["created_at"],
        }

    def register_authenticated(self, ai_id: str, display_name: str = None,
                               provider: str = "configured") -> dict:
        """Idempotently assign a number to an already-authenticated AI_ID."""
        self._validate_ai_id(ai_id)
        name = (display_name or ai_id).strip()
        vendor = (provider or "configured").strip()
        if not name or len(name) > 80 or not vendor or len(vendor) > 80:
            raise ValueError("invalid_identity_profile")
        self._db.execute("BEGIN IMMEDIATE")
        try:
            existing = self._db.execute(
                "SELECT * FROM ai_phone_registry WHERE ai_id=?", (ai_id,)
            ).fetchone()
            if existing is not None:
                if existing["status"] != "ACTIVE":
                    raise PermissionError("identity_not_active")
                self._db.commit()
                return self._public_record(existing)
            next_number = self._db.execute(
                "SELECT next_number FROM ai_phone_registry_sequence WHERE sequence_id=1"
            ).fetchone()["next_number"]
            year = datetime.now(timezone.utc).year
            record = (
                ai_id, f"AI-PHONE-{next_number:06d}",
                f"AIP-{year}-{next_number:08d}", name, vendor, "ACTIVE",
                datetime.now(timezone.utc).isoformat(),
            )
            self._db.execute("""
                INSERT INTO ai_phone_registry
                (ai_id,display_number,serial,display_name,provider,status,created_at)
                VALUES(?,?,?,?,?,?,?)
            """, record)
            self._db.execute(
                "UPDATE ai_phone_registry_sequence SET next_number=? WHERE sequence_id=1",
                (next_number + 1,),
            )
            row = self._db.execute(
                "SELECT * FROM ai_phone_registry WHERE ai_id=?", (ai_id,)
            ).fetchone()
            self._db.commit()
            return self._public_record(row)
        except Exception:
            self._db.rollback()
            raise

    def get_by_ai_id(self, ai_id: str):
        self._validate_ai_id(ai_id)
        row = self._db.execute(
            "SELECT * FROM ai_phone_registry WHERE ai_id=?", (ai_id,)
        ).fetchone()
        return self._public_record(row)

    def get_by_number(self, display_number: str):
        if not isinstance(display_number, str) or not re.fullmatch(
                r"AI-PHONE-[0-9]{6}", display_number):
            raise ValueError("invalid_phone_number")
        row = self._db.execute(
            "SELECT * FROM ai_phone_registry WHERE display_number=? AND status='ACTIVE'",
            (display_number,),
        ).fetchone()
        return self._public_record(row)
