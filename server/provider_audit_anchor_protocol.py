"""Structural interface for Provider Audit anchor adapters.

Implementations must provide linearizable compare-and-append semantics; a Python
Protocol verifies shape only and cannot prove atomicity, durability, or trust-domain
independence. See docs/MISSION_171_INDEPENDENT_ANCHOR_CONTRACT.md.
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class ProviderAuditAnchor(Protocol):
    """Append-only anchor interface required by the publisher and HTTP service.

    read_latest() returns the complete latest record or None.
    append_checkpoint(expected_sequence, record) must atomically compare the
    current sequence and append exactly the next linked record, or raise
    ValueError for a conflict. Successful writes must be durable before return.
    Exact retry behavior is handled at the HTTP service boundary; adapters must
    never overwrite or delete committed history.
    """

    def read_latest(self) -> dict | None:
        ...

    def append_checkpoint(self, expected_sequence: int, record: dict) -> dict:
        ...
