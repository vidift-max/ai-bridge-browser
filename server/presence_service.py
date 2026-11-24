"""Durable, room-scoped AI presence primitives.

This module deliberately contains no network or identity-token handling. Callers
must pass the AI ID derived from an authenticated server principal and the
server-owned membership set for the room.
"""
import sqlite3
import threading
import time
from typing import Dict, Iterable, List, Optional, Set


class PresenceService:
    DEFAULT_TTL_SECONDS = 90
    MAX_TTL_SECONDS = 120
    MAX_ACTIVE_ROOMS = 100

    def __init__(self, connection: sqlite3.Connection, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int):
            raise ValueError("invalid_presence_ttl")
        if ttl_seconds < 30 or ttl_seconds > self.MAX_TTL_SECONDS:
            raise ValueError("invalid_presence_ttl")
        self._connection = connection
        self._ttl_seconds = ttl_seconds
        self._lock = threading.RLock()
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS ai_presence (
                ai_id TEXT PRIMARY KEY,
                last_seen REAL NOT NULL
            )
        """)
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS ai_presence_rooms (
                ai_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                PRIMARY KEY(ai_id, conversation_id)
            )
        """)
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_ai_presence_rooms_conversation "
            "ON ai_presence_rooms(conversation_id, ai_id)"
        )
        self._connection.commit()

    @staticmethod
    def _validate_ai_id(ai_id: str) -> str:
        if not isinstance(ai_id, str) or not ai_id.strip() or len(ai_id) > 200:
            raise ValueError("invalid_ai_id")
        return ai_id

    @staticmethod
    def _validate_room_id(room_id: str) -> str:
        if not isinstance(room_id, str) or not room_id.strip() or len(room_id) > 200:
            raise ValueError("invalid_conversation_id")
        return room_id

    def heartbeat(self, ai_id: str, active_conversation_ids: Iterable[str],
                  allowed_conversation_ids: Iterable[str], now: Optional[float] = None) -> Dict[str, object]:
        ai_id = self._validate_ai_id(ai_id)
        if isinstance(active_conversation_ids, (str, bytes)):
            raise ValueError("invalid_active_conversations")
        try:
            active = list(active_conversation_ids)
            allowed = set(allowed_conversation_ids)
        except TypeError:
            raise ValueError("invalid_active_conversations")
        if len(active) > self.MAX_ACTIVE_ROOMS or len(set(active)) != len(active):
            raise ValueError("invalid_active_conversations")
        normalized = {self._validate_room_id(room_id) for room_id in active}
        if not normalized.issubset(allowed):
            raise PermissionError("presence_room_membership_required")
        timestamp = time.time() if now is None else float(now)
        if timestamp <= 0:
            raise ValueError("invalid_presence_timestamp")
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._connection.execute(
                    "INSERT INTO ai_presence(ai_id,last_seen) VALUES(?,?) "
                    "ON CONFLICT(ai_id) DO UPDATE SET last_seen=excluded.last_seen",
                    (ai_id, timestamp))
                self._connection.execute(
                    "DELETE FROM ai_presence_rooms WHERE ai_id=?", (ai_id,))
                self._connection.executemany(
                    "INSERT INTO ai_presence_rooms(ai_id,conversation_id) VALUES(?,?)",
                    [(ai_id, room_id) for room_id in sorted(normalized)])
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise
        return {"aiId": ai_id, "status": "ONLINE", "lastSeenAt": timestamp,
                "activeConversationIds": sorted(normalized),
                "expiresAt": timestamp + self._ttl_seconds}

    def leave(self, ai_id: str) -> bool:
        ai_id = self._validate_ai_id(ai_id)
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._connection.execute(
                    "DELETE FROM ai_presence_rooms WHERE ai_id=?", (ai_id,))
                cursor = self._connection.execute(
                    "DELETE FROM ai_presence WHERE ai_id=?", (ai_id,))
                self._connection.commit()
                return cursor.rowcount > 0
            except Exception:
                self._connection.rollback()
                raise

    def list_room(self, conversation_id: str, member_ai_ids: Iterable[str],
                  now: Optional[float] = None) -> List[Dict[str, object]]:
        conversation_id = self._validate_room_id(conversation_id)
        members = sorted({self._validate_ai_id(item) for item in member_ai_ids})
        timestamp = time.time() if now is None else float(now)
        if timestamp <= 0:
            raise ValueError("invalid_presence_timestamp")
        if not members:
            return []
        with self._lock:
            rows = self._connection.execute(
                "SELECT p.ai_id,p.last_seen,CASE WHEN r.ai_id IS NULL THEN 0 ELSE 1 END AS active_here "
                "FROM ai_presence p LEFT JOIN ai_presence_rooms r "
                "ON r.ai_id=p.ai_id AND r.conversation_id=? "
                "WHERE p.ai_id IN (" + ",".join("?" for _ in members) + ")",
                [conversation_id] + members).fetchall()
        by_id = {row["ai_id"]: row for row in rows}
        result = []
        for ai_id in members:
            row = by_id.get(ai_id)
            online = bool(row and row["last_seen"] >= timestamp - self._ttl_seconds)
            result.append({
                "aiId": ai_id,
                "displayName": ai_id,
                "status": "ONLINE" if online else "OFFLINE",
                "activeInRoom": bool(online and row["active_here"]),
                "lastSeenAt": row["last_seen"] if row else None,
            })
        return result
