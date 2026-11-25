"""Durable SQLite reference adapter for the provider-audit remote-anchor contract.

This is a separate-file reference backend for testing and single-host deployments.
It is NOT a remote service or a security boundary against a privileged host/database
administrator. Production deployments must place the anchor in an independently
administered trust domain.
"""
import json
import sqlite3
from pathlib import Path

from server.provider_audit_remote_anchor import (
    _GENESIS_DIGEST,
    _validate_record,
)


class SQLiteDurableAuditAnchor:
    """Append-only, transactionally sequenced anchor backed by a separate SQLite file."""

    def __init__(self, database_path):
        if not isinstance(database_path, str) or not database_path or database_path == ":memory:":
            raise ValueError("durable_anchor_path_required")
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _initialize(self):
        connection = self._connect()
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS provider_audit_anchor_records (
                    sequence INTEGER PRIMARY KEY CHECK(sequence > 0),
                    checkpoint_audit_id INTEGER NOT NULL CHECK(checkpoint_audit_id >= 0),
                    record_digest TEXT NOT NULL UNIQUE,
                    record_json TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE TRIGGER IF NOT EXISTS provider_audit_anchor_no_update
                BEFORE UPDATE ON provider_audit_anchor_records
                BEGIN SELECT RAISE(ABORT, 'anchor_records_are_append_only'); END
            """)
            connection.execute("""
                CREATE TRIGGER IF NOT EXISTS provider_audit_anchor_no_delete
                BEFORE DELETE ON provider_audit_anchor_records
                BEGIN SELECT RAISE(ABORT, 'anchor_records_are_append_only'); END
            """)
        finally:
            connection.close()

    def read_latest(self):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM provider_audit_anchor_records ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
        return json.loads(row["record_json"]) if row else None

    def append_checkpoint(self, expected_sequence, record):
        _validate_record(record)
        if type(expected_sequence) is not int or expected_sequence < 0:
            raise ValueError("remote_anchor_expected_sequence_invalid")
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT sequence, checkpoint_audit_id, record_digest FROM provider_audit_anchor_records "
                "ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            actual_sequence = row["sequence"] if row else 0
            previous_digest = row["record_digest"] if row else _GENESIS_DIGEST
            previous_audit_id = row["checkpoint_audit_id"] if row else -1
            if expected_sequence != actual_sequence:
                raise ValueError("remote_anchor_sequence_conflict")
            if record["sequence"] != actual_sequence + 1:
                raise ValueError("remote_anchor_sequence_invalid")
            if record["previous_digest"] != previous_digest:
                raise ValueError("remote_anchor_chain_conflict")
            if record["checkpoint_audit_id"] <= previous_audit_id:
                raise ValueError("remote_anchor_audit_id_not_monotonic")
            connection.execute(
                "INSERT INTO provider_audit_anchor_records "
                "(sequence, checkpoint_audit_id, record_digest, record_json) VALUES (?, ?, ?, ?)",
                (record["sequence"], record["checkpoint_audit_id"], record["record_digest"], encoded),
            )
            connection.commit()
            return dict(record)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def verify_history(self, expected_head=None):
        """Verify the full chain; expected_head is an independently trusted witness.

        Without expected_head, a valid shorter prefix cannot prove that a suffix
        was not deleted. Supplying the externally retained head detects rollback
        and suffix truncation without attempting an automatic repair.
        """
        previous = _GENESIS_DIGEST
        previous_audit_id = -1
        expected_sequence = 1
        checked = 0
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT sequence, checkpoint_audit_id, record_digest, record_json "
                "FROM provider_audit_anchor_records ORDER BY sequence"
            ).fetchall()
        for row in rows:
            try:
                record = json.loads(row["record_json"])
                _validate_record(record)
            except (TypeError, ValueError, json.JSONDecodeError):
                return {"valid": False, "reason": "history_record_corrupt",
                        "records_checked": checked, "first_invalid_sequence": expected_sequence}
            if (row["sequence"] != expected_sequence
                    or record["sequence"] != expected_sequence
                    or row["record_digest"] != record["record_digest"]
                    or record["previous_digest"] != previous
                    or row["checkpoint_audit_id"] != record["checkpoint_audit_id"]
                    or record["checkpoint_audit_id"] <= previous_audit_id):
                return {"valid": False, "records_checked": checked,
                        "first_invalid_sequence": expected_sequence}
            previous = record["record_digest"]
            previous_audit_id = record["checkpoint_audit_id"]
            expected_sequence += 1
            checked += 1
        result = {"valid": True, "reason": None, "records_checked": checked,
                  "last_sequence": checked, "last_digest": previous}
        if expected_head is not None:
            if (not isinstance(expected_head, dict)
                    or set(expected_head) != {"sequence", "record_digest", "checkpoint_audit_id"}
                    or type(expected_head["sequence"]) is not int
                    or expected_head["sequence"] < 0
                    or type(expected_head["checkpoint_audit_id"]) is not int
                    or expected_head["checkpoint_audit_id"] < -1
                    or not isinstance(expected_head["record_digest"], str)
                    or len(expected_head["record_digest"]) != 64
                    or any(ch not in "0123456789abcdef" for ch in expected_head["record_digest"])):
                raise ValueError("trusted_anchor_head_invalid")
            actual_head = {
                "sequence": checked,
                "record_digest": previous,
                "checkpoint_audit_id": previous_audit_id,
            }
            if actual_head != expected_head:
                return {**result, "valid": False, "reason": "trusted_head_mismatch",
                        "expected_head": expected_head, "actual_head": actual_head}
        return result


def compare_provider_audit_anchor_copies(left_anchor, right_anchor, expected_head=None):
    """Compare two independently obtained, fully verified chain heads.

    This detects divergence only when each adapter can verify its own complete
    history. It does not establish that either copy is authentic unless
    expected_head came from an independently trusted source.
    """
    try:
        left = left_anchor.verify_history(expected_head=expected_head)
        right = right_anchor.verify_history(expected_head=expected_head)
    except Exception:
        return {"valid": False, "reason": "anchor_copy_unavailable"}
    if not left.get("valid") or not right.get("valid"):
        return {"valid": False, "reason": "anchor_copy_integrity_failed",
                "left": left, "right": right}
    if (left.get("last_sequence"), left.get("last_digest")) != (
            right.get("last_sequence"), right.get("last_digest")):
        return {"valid": False, "reason": "anchor_copy_divergence",
                "left": left, "right": right}
    return {"valid": True, "reason": None,
            "sequence": left["last_sequence"], "record_digest": left["last_digest"]}
