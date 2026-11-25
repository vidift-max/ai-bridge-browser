"""Independent trusted-witness contract and quorum orchestration.

This module defines an adapter boundary only. A production adapter must provide
authenticated transport, authorization, durable atomic compare-and-append, and
its own bounded network deadlines. No network client is implemented here.
"""
from typing import Protocol, runtime_checkable


def _validate_head(head):
    if (not isinstance(head, dict)
            or set(head) != {"sequence", "record_digest", "checkpoint_audit_id"}
            or type(head["sequence"]) is not int or head["sequence"] < 0
            or type(head["checkpoint_audit_id"]) is not int
            or head["checkpoint_audit_id"] < -1
            or not isinstance(head["record_digest"], str)
            or len(head["record_digest"]) != 64
            or any(ch not in "0123456789abcdef" for ch in head["record_digest"])):
        raise ValueError("trusted_head_invalid")
    if head["sequence"] == 0 and (
            head["record_digest"] != "0" * 64 or head["checkpoint_audit_id"] != -1):
        raise ValueError("trusted_head_genesis_invalid")
    if head["sequence"] > 0 and head["checkpoint_audit_id"] < 0:
        raise ValueError("trusted_head_invalid")
    return dict(head)


@runtime_checkable
class ProviderAuditTrustedWitness(Protocol):
    """Minimal independent witness API; implementations must be durable."""

    def read_latest(self):
        """Return None or the exact trusted-head mapping."""
        ...

    def record_head(self, head):
        """Atomically append a monotonic head; exact retries must be idempotent."""
        ...


def _validate_quorum(witnesses, quorum):
    if not isinstance(witnesses, (list, tuple)) or not witnesses:
        raise ValueError("trusted_witnesses_required")
    if type(quorum) is not int or quorum < 1 or quorum > len(witnesses):
        raise ValueError("trusted_witness_quorum_invalid")
    if len({id(witness) for witness in witnesses}) != len(witnesses):
        raise ValueError("trusted_witness_duplicate_adapter")
    for witness in witnesses:
        if not callable(getattr(witness, "read_latest", None)) or not callable(
                getattr(witness, "record_head", None)):
            raise ValueError("trusted_witness_contract_invalid")


def replicate_trusted_head(witnesses, head, write_quorum):
    """Attempt idempotent replication; partial success is reported, never hidden.

    Adapter calls must enforce their own finite deadlines. Exceptions, including
    TimeoutError and authorization failures, count as non-acknowledgements.
    A retry of the same head can complete a partially successful replication.
    """
    head = _validate_head(head)
    _validate_quorum(witnesses, write_quorum)
    acknowledgements = []
    failures = []
    for index, witness in enumerate(witnesses):
        try:
            latest = witness.read_latest()
            if latest is not None:
                latest = _validate_head(latest)
                if latest == head:
                    acknowledgements.append(index)
                    continue
                if (head["sequence"] <= latest["sequence"]
                        or head["checkpoint_audit_id"] <= latest["checkpoint_audit_id"]):
                    raise ValueError("trusted_witness_conflict_or_rollback")
            result = witness.record_head(head)
            if (not isinstance(result, dict) or result.get("head") != head
                    or result.get("recorded") not in (True, False)
                    or result.get("replayed") not in (True, False)
                    or result.get("recorded") == result.get("replayed")):
                raise ValueError("trusted_witness_ack_invalid")
            acknowledgements.append(index)
        except Exception as error:
            failures.append({"witness_index": index,
                             "reason": type(error).__name__})
    return {
        "replicated": len(acknowledgements) >= write_quorum,
        "write_quorum": write_quorum,
        "acknowledgements": acknowledgements,
        "failures": failures,
        "partial_commit_possible": bool(acknowledgements) and
            len(acknowledgements) < write_quorum,
    }


def verify_trusted_head_quorum(witnesses, expected_head, read_quorum):
    """Require a quorum to report the exact expected head; fail closed on forks."""
    expected_head = _validate_head(expected_head)
    _validate_quorum(witnesses, read_quorum)
    matching = []
    stale = []
    failures = []
    conflicts = []
    for index, witness in enumerate(witnesses):
        try:
            latest = witness.read_latest()
            if latest is None:
                stale.append(index)
                continue
            latest = _validate_head(latest)
            if latest == expected_head:
                matching.append(index)
            elif (latest["sequence"] > expected_head["sequence"]
                    or (latest["sequence"] == expected_head["sequence"]
                        and latest != expected_head)):
                conflicts.append(index)
            else:
                stale.append(index)
        except Exception as error:
            failures.append({"witness_index": index,
                             "reason": type(error).__name__})
    valid = len(matching) >= read_quorum and not conflicts
    return {
        "valid": valid,
        "reason": None if valid else (
            "trusted_witness_conflict" if conflicts else
            "trusted_witness_quorum_unavailable"),
        "read_quorum": read_quorum,
        "matching": matching,
        "stale": stale,
        "conflicts": conflicts,
        "failures": failures,
    }
