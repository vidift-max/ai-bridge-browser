"""Independent-witness and safe SQLite backup/restore helpers.

The witness file is a separate local artifact, not a remote trust boundary.
Production independence requires separate administration and credentials.
"""
import os
import sqlite3
import tempfile
from pathlib import Path

from server.provider_audit_durable_anchor import SQLiteDurableAuditAnchor


def _validate_head(head):
    if (not isinstance(head, dict)
            or set(head) != {"sequence", "record_digest", "checkpoint_audit_id"}
            or type(head["sequence"]) is not int or head["sequence"] < 0
            or type(head["checkpoint_audit_id"]) is not int
            or head["checkpoint_audit_id"] < -1
            or not isinstance(head["record_digest"], str)
            or len(head["record_digest"]) != 64
            or any(ch not in "0123456789abcdef" for ch in head["record_digest"])):
        raise ValueError("trusted_anchor_head_invalid")
    if head["sequence"] == 0 and (
            head["record_digest"] != "0" * 64 or head["checkpoint_audit_id"] != -1):
        raise ValueError("trusted_anchor_genesis_invalid")
    if head["sequence"] > 0 and head["checkpoint_audit_id"] < 0:
        raise ValueError("trusted_anchor_head_invalid")
    return dict(head)


class SQLiteTrustedHeadWitness:
    """Append-only witness journal stored separately from the anchor database."""

    def __init__(self, database_path):
        if not isinstance(database_path, str) or not database_path or database_path == ":memory:":
            raise ValueError("trusted_head_witness_path_required")
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(database_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS trusted_head_witness (
                witness_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence INTEGER NOT NULL,
                record_digest TEXT NOT NULL,
                checkpoint_audit_id INTEGER NOT NULL,
                UNIQUE(sequence, record_digest, checkpoint_audit_id)
            )""")
            db.execute("""CREATE TRIGGER IF NOT EXISTS trusted_head_no_update
                BEFORE UPDATE ON trusted_head_witness
                BEGIN SELECT RAISE(ABORT, 'trusted_head_witness_append_only'); END""")
            db.execute("""CREATE TRIGGER IF NOT EXISTS trusted_head_no_delete
                BEFORE DELETE ON trusted_head_witness
                BEGIN SELECT RAISE(ABORT, 'trusted_head_witness_append_only'); END""")

    def _connect(self):
        db = sqlite3.connect(self.database_path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def read_latest(self):
        with self._connect() as db:
            row = db.execute(
                "SELECT sequence, record_digest, checkpoint_audit_id "
                "FROM trusted_head_witness ORDER BY witness_id DESC LIMIT 1"
            ).fetchone()
        return dict(row) if row else None

    def record_head(self, head):
        head = _validate_head(head)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT sequence, record_digest, checkpoint_audit_id "
                "FROM trusted_head_witness ORDER BY witness_id DESC LIMIT 1"
            ).fetchone()
            previous = dict(row) if row else None
            if previous == head:
                return {"recorded": False, "replayed": True, "head": head}
            if previous is not None and (
                    head["sequence"] <= previous["sequence"]
                    or head["checkpoint_audit_id"] <= previous["checkpoint_audit_id"]):
                raise ValueError("trusted_head_witness_rollback")
            db.execute(
                "INSERT INTO trusted_head_witness "
                "(sequence, record_digest, checkpoint_audit_id) VALUES (?, ?, ?)",
                (head["sequence"], head["record_digest"], head["checkpoint_audit_id"]),
            )
            return {"recorded": True, "replayed": False, "head": head}

    def verify_anchor(self, anchor):
        head = self.read_latest()
        if head is None:
            return {"valid": False, "reason": "trusted_head_witness_empty"}
        result = anchor.verify_history(expected_head=head)
        return {"valid": bool(result.get("valid")), "reason": result.get("reason"),
                "witness_head": head, "anchor_result": result}


def _sqlite_integrity_check(path):
    with sqlite3.connect(path) as db:
        rows = db.execute("PRAGMA integrity_check").fetchall()
    return rows == [("ok",)]


def create_verified_anchor_backup(anchor, backup_path, trusted_head):
    """Create a new backup only after source and witness agree; never overwrite."""
    if os.path.exists(backup_path):
        raise FileExistsError("anchor_backup_destination_exists")
    head = _validate_head(trusted_head)
    source_result = anchor.verify_history(expected_head=head)
    if not source_result.get("valid"):
        raise ValueError("anchor_backup_source_integrity_failed")
    destination = Path(backup_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(anchor.database_path)
    target = sqlite3.connect(str(destination))
    try:
        source.backup(target)
        target.commit()
    finally:
        target.close()
        source.close()
    if not _sqlite_integrity_check(str(destination)):
        raise ValueError("anchor_backup_sqlite_integrity_failed")
    restored = SQLiteDurableAuditAnchor(str(destination))
    result = restored.verify_history(expected_head=head)
    if not result.get("valid"):
        raise ValueError("anchor_backup_chain_verification_failed")
    return {"created": True, "path": str(destination), "head": head,
            "integrity_check": "ok", "records_checked": result["records_checked"]}


def restore_anchor_backup_to_new_file(backup_path, destination_path, trusted_head):
    """Restore to a new path only; refuse overwrite and remove failed output copy."""
    if os.path.exists(destination_path):
        raise FileExistsError("anchor_restore_destination_exists")
    head = _validate_head(trusted_head)
    if not _sqlite_integrity_check(backup_path):
        raise ValueError("anchor_restore_backup_sqlite_integrity_failed")
    backup = SQLiteDurableAuditAnchor(backup_path)
    verified = backup.verify_history(expected_head=head)
    if not verified.get("valid"):
        raise ValueError("anchor_restore_backup_chain_verification_failed")
    destination = Path(destination_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(backup_path)
    target = sqlite3.connect(str(destination))
    try:
        source.backup(target)
        target.commit()
    finally:
        target.close()
        source.close()
    try:
        if not _sqlite_integrity_check(str(destination)):
            raise ValueError("anchor_restore_sqlite_integrity_failed")
        restored = SQLiteDurableAuditAnchor(str(destination))
        result = restored.verify_history(expected_head=head)
        if not result.get("valid"):
            raise ValueError("anchor_restore_chain_verification_failed")
    except Exception:
        for suffix in ("", "-wal", "-shm"):
            try:
                os.unlink(str(destination) + suffix)
            except FileNotFoundError:
                pass
        raise
    return {"restored": True, "path": str(destination),
            "head": head, "records_checked": result["records_checked"]}
