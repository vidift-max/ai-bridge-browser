"""Server-owned, durable directory for provisioned AI identities.

Internal numbers are allocated once by SQLite and never accepted from clients.
Display names can only be supplied by trusted server-side provisioning code.
"""
import sqlite3
from typing import Dict, Iterable, List, Optional


class IdentityDirectory:
    MAX_DISPLAY_NAME_LENGTH = 80

    def __init__(self, connection: sqlite3.Connection,
                 known_ai_ids: Iterable[str],
                 display_names: Optional[Dict[str, str]] = None):
        self._connection = connection
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS ai_identity_directory (
                internal_number INTEGER PRIMARY KEY AUTOINCREMENT,
                ai_id TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                created_at REAL NOT NULL DEFAULT (unixepoch())
            )
        """)
        self._connection.commit()
        names = display_names or {}
        for ai_id in sorted(set(known_ai_ids)):
            ai_id = self._validate_ai_id(ai_id)
            if ai_id in names:
                self.provision(ai_id, names[ai_id])
            else:
                self._connection.execute(
                    """INSERT OR IGNORE INTO ai_identity_directory(ai_id,display_name)
                       VALUES(?,?)""", (ai_id, ai_id))
        self._connection.commit()

    @classmethod
    def _validate_ai_id(cls, ai_id: str) -> str:
        if not isinstance(ai_id, str) or not ai_id.strip() or len(ai_id) > 200:
            raise ValueError("invalid_ai_id")
        return ai_id

    @classmethod
    def _validate_display_name(cls, display_name: str) -> str:
        if (not isinstance(display_name, str) or not display_name.strip()
                or len(display_name.strip()) > cls.MAX_DISPLAY_NAME_LENGTH):
            raise ValueError("invalid_display_name")
        return display_name.strip()

    def provision(self, ai_id: str, display_name: str):
        """Provision or update a display name from trusted server-side code."""
        ai_id = self._validate_ai_id(ai_id)
        display_name = self._validate_display_name(display_name)
        self._connection.execute(
            """INSERT INTO ai_identity_directory(ai_id,display_name)
               VALUES(?,?)
               ON CONFLICT(ai_id) DO UPDATE SET display_name=excluded.display_name""",
            (ai_id, display_name))
        self._connection.commit()
        return self.get(ai_id)

    def get(self, ai_id: str):
        ai_id = self._validate_ai_id(ai_id)
        row = self._connection.execute(
            """SELECT internal_number,ai_id,display_name,created_at
               FROM ai_identity_directory WHERE ai_id=?""", (ai_id,)).fetchone()
        if row is None:
            raise KeyError("identity_not_provisioned")
        return self._as_dict(row)

    @staticmethod
    def _as_dict(row):
        return {"internalNumber": row["internal_number"], "aiId": row["ai_id"],
                "displayName": row["display_name"], "createdAt": row["created_at"]}

    def list_members(self, member_ai_ids: Iterable[str]) -> List[dict]:
        members = sorted({self._validate_ai_id(item) for item in member_ai_ids})
        if not members:
            return []
        placeholders = ",".join("?" for _ in members)
        rows = self._connection.execute(
            """SELECT internal_number,ai_id,display_name,created_at
               FROM ai_identity_directory WHERE ai_id IN (""" + placeholders + """)
               ORDER BY internal_number""", members).fetchall()
        found = {row["ai_id"] for row in rows}
        if found != set(members):
            raise KeyError("identity_not_provisioned")
        return [self._as_dict(row) for row in rows]
