import hashlib
from dataclasses import dataclass
from functools import wraps
from threading import RLock
from datetime import datetime, timezone
from typing import Dict, Optional


def _synchronized(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapped


@dataclass(frozen=True)
class CredentialRecord:
    token_hash: str
    ai_id: str
    status: str = "ACTIVE"
    expires_at: Optional[datetime] = None
    generation: int = 1

    def effective_status(self, now: Optional[datetime] = None) -> str:
        if self.status != "ACTIVE":
            return self.status
        if self.expires_at is not None and (now or datetime.now(timezone.utc)) >= self.expires_at:
            return "EXPIRED"
        return "ACTIVE"


class CredentialRegistry:
    """Runtime authentication registry with durable hash-only guest credentials."""

    def __init__(self, token_to_ai_id: Dict[str, str], token_expiry: Optional[Dict[str, datetime]] = None,
                 connection=None):
        self._lock = RLock()
        self._connection = connection
        expiry = token_expiry or {}
        self._records = {
            self._hash(token): CredentialRecord(
                token_hash=self._hash(token), ai_id=ai_id, expires_at=expiry.get(token))
            for token, ai_id in token_to_ai_id.items()
        }
        self._persistent_hashes = set()
        if self._connection is not None:
            rows = self._connection.execute(
                "SELECT token_hash,ai_id,status,expires_at,generation FROM credential_records"
            ).fetchall()
            for row in rows:
                expires_at = (datetime.fromtimestamp(row["expires_at"], timezone.utc)
                              if row["expires_at"] is not None else None)
                record = CredentialRecord(row["token_hash"], row["ai_id"], row["status"],
                                          expires_at, row["generation"])
                self._records[record.token_hash] = record
                self._persistent_hashes.add(record.token_hash)

    @_synchronized
    def attach_connection(self, connection):
        self._connection = connection
        rows = connection.execute(
            "SELECT token_hash,ai_id,status,expires_at,generation FROM credential_records"
        ).fetchall()
        for row in rows:
            expires_at = (datetime.fromtimestamp(row["expires_at"], timezone.utc)
                          if row["expires_at"] is not None else None)
            record = CredentialRecord(row["token_hash"], row["ai_id"], row["status"],
                                      expires_at, row["generation"])
            self._records[record.token_hash] = record
            self._persistent_hashes.add(record.token_hash)

    @staticmethod
    def _hash(token: str) -> str:
        if not isinstance(token, str) or not token:
            return ""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _epoch(value):
        return value.timestamp() if value is not None else None

    def _persist(self, record):
        if self._connection is None or record.token_hash not in self._persistent_hashes:
            return
        self._connection.execute(
            "UPDATE credential_records SET status=?,expires_at=?,generation=? WHERE token_hash=?",
            (record.status, self._epoch(record.expires_at), record.generation, record.token_hash))
        self._connection.commit()

    @_synchronized
    def activate_persisted(self, token: str, ai_id: str, expires_at: Optional[datetime] = None):
        token_hash = self._hash(token)
        if not token_hash or token_hash not in self._persistent_hashes:
            raise RuntimeError("persisted_credential_not_found")
        record = CredentialRecord(token_hash, ai_id, "ACTIVE", expires_at, 1)
        self._records[token_hash] = record
        return record.generation

    @_synchronized
    def provision(self, token: str, ai_id: str, expires_at: Optional[datetime] = None):
        token_hash = self._hash(token)
        if not token_hash or not isinstance(ai_id, str) or not ai_id.strip():
            raise ValueError("invalid_credential")
        if token_hash in self._records:
            raise ValueError("credential_already_exists")
        if self._connection is None:
            raise RuntimeError("durable_credential_store_required")
        record = CredentialRecord(token_hash, ai_id, "ACTIVE", expires_at, 1)
        self._connection.execute(
            """INSERT INTO credential_records(token_hash,ai_id,status,expires_at,generation,created_at)
               VALUES(?,?,'ACTIVE',?,1,?)""",
            (token_hash, ai_id, self._epoch(expires_at), datetime.now(timezone.utc).timestamp()))
        self._connection.commit()
        self._records[token_hash] = record
        self._persistent_hashes.add(token_hash)
        return record.generation

    @_synchronized
    def authenticate(self, token: str, now: Optional[datetime] = None) -> str:
        record = self._records.get(self._hash(token))
        if record is None or record.effective_status(now) != "ACTIVE":
            raise PermissionError("authentication_required")
        return record.ai_id

    @_synchronized
    def authenticate_with_generation(self, token: str, now: Optional[datetime] = None):
        record = self._records.get(self._hash(token))
        if record is None or record.effective_status(now) != "ACTIVE":
            raise PermissionError("authentication_required")
        return record.ai_id, record.generation

    @_synchronized
    def revoke(self, token: str) -> None:
        token_hash = self._hash(token)
        record = self._records.get(token_hash)
        if record is None:
            raise KeyError("credential_unknown")
        updated = CredentialRecord(record.token_hash, record.ai_id, "REVOKED",
                                   record.expires_at, record.generation)
        self._records[token_hash] = updated
        self._persist(updated)

    @_synchronized
    def expire(self, token: str) -> None:
        token_hash = self._hash(token)
        record = self._records.get(token_hash)
        if record is None:
            raise KeyError("credential_unknown")
        updated = CredentialRecord(record.token_hash, record.ai_id, "EXPIRED",
                                   record.expires_at, record.generation)
        self._records[token_hash] = updated
        self._persist(updated)

    @_synchronized
    def rotate(self, old_token: str, new_token: str) -> None:
        old_hash, new_hash = self._hash(old_token), self._hash(new_token)
        old = self._records.get(old_hash)
        if old is None:
            raise KeyError("credential_unknown")
        if old.effective_status() != "ACTIVE":
            raise PermissionError("credential_not_active")
        if new_hash in self._records:
            raise ValueError("credential_already_exists")
        updated = CredentialRecord(old.token_hash, old.ai_id, "ROTATED",
                                   old.expires_at, old.generation)
        self._records[old_hash] = updated
        self._persist(updated)
        next_record = CredentialRecord(new_hash, old.ai_id, "ACTIVE", None, old.generation + 1)
        self._records[new_hash] = next_record
        if old_hash in self._persistent_hashes:
            self._connection.execute(
                """INSERT INTO credential_records(token_hash,ai_id,status,expires_at,generation,created_at)
                   VALUES(?,?,'ACTIVE',NULL,?,?)""",
                (new_hash, old.ai_id, next_record.generation,
                 datetime.now(timezone.utc).timestamp()))
            self._connection.commit()
            self._persistent_hashes.add(new_hash)

    @_synchronized
    def generation(self, token: str) -> int:
        record = self._records.get(self._hash(token))
        if record is None:
            raise PermissionError("authentication_required")
        return record.generation

    @_synchronized
    def status(self, token: str, now: Optional[datetime] = None) -> str:
        record = self._records.get(self._hash(token))
        return "UNKNOWN" if record is None else record.effective_status(now)

