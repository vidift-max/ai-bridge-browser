"""Signed external checkpoints for the provider audit hash chain.

The checkpoint file and HMAC key must be stored independently from the SQLite
database by the operator. This module never persists the signing key.
"""
import hashlib
import hmac
import json
import os
import tempfile
import time
from pathlib import Path

_GENESIS_HASH = "0" * 64
_CHECKPOINT_VERSION = 1
_MIN_KEY_BYTES = 32


def _key_bytes(signing_key):
    if not isinstance(signing_key, bytes) or len(signing_key) < _MIN_KEY_BYTES:
        raise ValueError("invalid_checkpoint_signing_key")
    return signing_key


def _canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _signed_payload(payload, signing_key):
    signature = hmac.new(_key_bytes(signing_key), _canonical(payload).encode("utf-8"),
                         hashlib.sha256).hexdigest()
    return {**payload, "signature": signature}


def _read_checkpoint(checkpoint_path, signing_key):
    try:
        raw = Path(checkpoint_path).read_text(encoding="utf-8")
        document = json.loads(raw)
        if not isinstance(document, dict) or set(document) != {
            "version", "audit_id", "event_hash", "created_at", "signature"
        }:
            raise ValueError("invalid_checkpoint_format")
        payload = {key: document[key] for key in
                   ("version", "audit_id", "event_hash", "created_at")}
        if (type(payload["version"]) is not int or payload["version"] != _CHECKPOINT_VERSION
                or type(payload["audit_id"]) is not int or payload["audit_id"] < 0
                or not isinstance(payload["event_hash"], str)
                or len(payload["event_hash"]) != 64
                or not isinstance(payload["created_at"], (int, float))
                or isinstance(payload["created_at"], bool)):
            raise ValueError("invalid_checkpoint_format")
        expected = hmac.new(_key_bytes(signing_key), _canonical(payload).encode("utf-8"),
                            hashlib.sha256).hexdigest()
        if not isinstance(document["signature"], str) or not hmac.compare_digest(
                document["signature"], expected):
            raise ValueError("checkpoint_signature_invalid")
        return payload
    except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
        raise ValueError("checkpoint_unavailable_or_invalid") from exc


def create_provider_audit_checkpoint(store, checkpoint_path, signing_key, created_at=None):
    """Atomically write a signed snapshot of the latest verified audit-chain head."""
    _key_bytes(signing_key)
    connection = store.connection
    connection.execute("BEGIN")
    try:
        verification = store.verify_provider_request_audit_chain()
        if not verification["valid"]:
            raise ValueError("provider_audit_chain_invalid")
        row = connection.execute(
            "SELECT audit_id,event_hash FROM provider_request_audit_events ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()
        audit_id = int(row["audit_id"]) if row else 0
        event_hash = row["event_hash"] if row else _GENESIS_HASH
        timestamp = time.time() if created_at is None else created_at
        if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
            raise ValueError("invalid_checkpoint_timestamp")
        payload = {
            "version": _CHECKPOINT_VERSION,
            "audit_id": audit_id,
            "event_hash": event_hash,
            "created_at": float(timestamp),
        }
        document = _signed_payload(payload, signing_key)
        connection.commit()
    except Exception:
        connection.rollback()
        raise

    destination = Path(checkpoint_path)\n    if str(destination.resolve()) == str(Path(store._database_path).resolve()):\n        raise ValueError("checkpoint_must_be_separate_from_database")\n    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(prefix=".provider-audit-checkpoint-",
                                          dir=str(destination.parent))
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(_canonical(document))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        try:
            directory_fd = os.open(str(destination.parent), os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            # Some platforms/filesystems do not support directory fsync.
            pass
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)
    return payload


def verify_provider_audit_checkpoint(store, checkpoint_path, signing_key):
    """Verify the signed checkpoint and prove its anchored event still exists."""
    payload = _read_checkpoint(checkpoint_path, signing_key)
    chain = store.verify_provider_request_audit_chain()
    if not chain["valid"]:
        return {"valid": False, "reason": "provider_audit_chain_invalid",
                "first_invalid_audit_id": chain["first_invalid_audit_id"]}
    if payload["audit_id"] == 0:
        anchored_hash = _GENESIS_HASH
    else:
        row = store.connection.execute(
            "SELECT event_hash FROM provider_request_audit_events WHERE audit_id=?",
            (payload["audit_id"],)).fetchone()
        if row is None:
            return {"valid": False, "reason": "checkpoint_ahead_of_database"}
        anchored_hash = row["event_hash"]
    if not hmac.compare_digest(anchored_hash, payload["event_hash"]):
        return {"valid": False, "reason": "checkpoint_anchor_mismatch"}
    latest = store.connection.execute(
        "SELECT audit_id FROM provider_request_audit_events ORDER BY audit_id DESC LIMIT 1"
    ).fetchone()
    latest_id = int(latest["audit_id"]) if latest else 0
    if latest_id < payload["audit_id"]:
        return {"valid": False, "reason": "database_rollback_detected"}
    return {"valid": True, "reason": None, "checkpoint_audit_id": payload["audit_id"],
            "latest_audit_id": latest_id, "event_hash": payload["event_hash"]}
