"""Transport-neutral contract for a monotonic remote provider-audit anchor.

A production client must implement atomic compare-and-append in a trust domain
independent from the application database and checkpoint file. No network or
cloud provider is selected or contacted by this module.
"""
import hashlib
import hmac
import json
import math

from server.provider_audit_checkpoint import (
    _canonical,
    _read_checkpoint,
    verify_provider_audit_checkpoint,
)

_ANCHOR_VERSION = 1
_GENESIS_DIGEST = "0" * 64


def _record_digest(record):
    payload = {key: record[key] for key in (
        "version", "sequence", "previous_digest", "checkpoint_audit_id",
        "checkpoint_event_hash", "checkpoint_created_at", "checkpoint_signature",
    )}
    return hashlib.sha256((record["previous_digest"] + _canonical(payload)).encode("utf-8")).hexdigest()


def _validate_record(record):
    if not isinstance(record, dict) or set(record) != {
        "version", "sequence", "previous_digest", "checkpoint_audit_id",
        "checkpoint_event_hash", "checkpoint_created_at", "checkpoint_signature",
        "record_digest",
    }:
        raise ValueError("invalid_remote_anchor_record")
    if type(record["version"]) is not int or record["version"] != _ANCHOR_VERSION:
        raise ValueError("invalid_remote_anchor_record")
    if type(record["sequence"]) is not int or record["sequence"] < 1:
        raise ValueError("invalid_remote_anchor_record")
    for field in ("previous_digest", "checkpoint_event_hash", "checkpoint_signature", "record_digest"):
        value = record[field]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("invalid_remote_anchor_record")
    if type(record["checkpoint_audit_id"]) is not int or record["checkpoint_audit_id"] < 0:
        raise ValueError("invalid_remote_anchor_record")
    created = record["checkpoint_created_at"]
    if isinstance(created, bool) or not isinstance(created, (int, float)) or not math.isfinite(float(created)):
        raise ValueError("invalid_remote_anchor_record")
    if not hmac.compare_digest(record["record_digest"], _record_digest(record)):
        raise ValueError("remote_anchor_record_digest_invalid")
    return record


def _record_from_checkpoint(payload, previous_record):
    sequence = previous_record["sequence"] + 1 if previous_record else 1
    previous_digest = previous_record["record_digest"] if previous_record else _GENESIS_DIGEST
    record = {
        "version": _ANCHOR_VERSION,
        "sequence": sequence,
        "previous_digest": previous_digest,
        "checkpoint_audit_id": payload["audit_id"],
        "checkpoint_event_hash": payload["event_hash"],
        "checkpoint_created_at": payload["created_at"],
        "checkpoint_signature": payload["signature"],
    }
    record["record_digest"] = _record_digest(record)
    return record


def publish_provider_audit_remote_anchor(store, checkpoint_path, signing_key, remote_client):
    """Publish a verified local checkpoint using atomic remote compare-and-append.

    remote_client contract:
      read_latest() -> None or a complete anchor record
      append_checkpoint(expected_sequence: int, record: dict) -> stored record

    The remote service must atomically reject stale expected_sequence values,
    sequence gaps, duplicate/forked records, and any attempt to replace history.
    """
    local = _read_checkpoint(checkpoint_path, signing_key)
    verification = verify_provider_audit_checkpoint(store, checkpoint_path, signing_key)
    if not verification["valid"]:
        raise ValueError("local_provider_audit_checkpoint_invalid")
    latest = remote_client.read_latest()
    if latest is not None:
        _validate_record(latest)
        if latest["checkpoint_audit_id"] > local["audit_id"]:
            raise ValueError("remote_anchor_ahead_of_local_checkpoint")
        if latest["checkpoint_audit_id"] == local["audit_id"]:
            if (latest["checkpoint_event_hash"] == local["event_hash"]
                    and latest["checkpoint_signature"] == local["signature"]):
                return latest
            raise ValueError("remote_anchor_conflict")
    record = _record_from_checkpoint(local, latest)
    expected_sequence = latest["sequence"] if latest else 0
    stored = remote_client.append_checkpoint(expected_sequence, record)
    _validate_record(stored)
    if stored != record:
        raise ValueError("remote_anchor_append_mismatch")
    return stored


def verify_provider_audit_remote_anchor(store, checkpoint_path, signing_key, remote_client):
    """Verify remote latest record, local signature, and that local checkpoint is not stale."""
    latest = remote_client.read_latest()
    if latest is None:
        return {"valid": False, "reason": "remote_anchor_empty"}
    try:
        _validate_record(latest)
        local = _read_checkpoint(checkpoint_path, signing_key)
        local_result = verify_provider_audit_checkpoint(store, checkpoint_path, signing_key)
    except (ValueError, OSError):
        return {"valid": False, "reason": "local_or_remote_anchor_invalid"}
    if not local_result["valid"]:
        return {"valid": False, "reason": "local_checkpoint_invalid"}
    if local["audit_id"] < latest["checkpoint_audit_id"]:
        return {"valid": False, "reason": "local_checkpoint_rollback"}
    if local["audit_id"] == latest["checkpoint_audit_id"] and (
            local["event_hash"] != latest["checkpoint_event_hash"]
            or local["signature"] != latest["checkpoint_signature"]):
        return {"valid": False, "reason": "local_checkpoint_fork"}
    if local["audit_id"] > latest["checkpoint_audit_id"]:
        return {"valid": False, "reason": "local_checkpoint_not_yet_anchored"}
    return {"valid": True, "reason": None, "remote_sequence": latest["sequence"],
            "checkpoint_audit_id": latest["checkpoint_audit_id"],
            "record_digest": latest["record_digest"]}
