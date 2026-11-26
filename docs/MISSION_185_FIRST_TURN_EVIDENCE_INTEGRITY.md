# Mission 185 — First-Turn Evidence Integrity & Failure Audit

## Objective

Harden the metadata contract for the first AI-USER → AI-PEER round trip. This layer supplements Mission 183's semantic evidence contract and Mission 184's operator-state record.

## Ten rounds

1. Audit Mission 184's final SHA, PR state, and CI result.
2. Create an isolated branch from the exact Mission 184 head.
3. Add integrity validation for request identifiers.
4. Require exactly two distinct, non-empty request IDs.
5. Require exactly two integer 2xx response statuses; booleans and strings are rejected.
6. Require timezone-aware start and finish timestamps.
7. Reject finish timestamps earlier than start timestamps.
8. Add negative tests for malformed IDs, statuses, timestamps, deployment SHA, and provider mapping.
9. Add offline CI and document the evidence boundaries.
10. Verify exact head SHA, CI, PR Draft/open/unmerged state, and report PASS/NO-GO/BLOCKED.

## Security boundary

The validator is deterministic and performs no network I/O. It does not contact providers, deploy staging, create rooms, register sessions, authorize a live turn, or send messages. It never stores credentials, bearer tokens, cookies, prompts, or response bodies.

## Interpretation

A `VALID` result means only that the supplied metadata satisfies these structural and integrity checks. It is not proof of provider authenticity, transport-level delivery, or an actual live AI conversation. Real execution requires separately authorized operator evidence.

## Stop conditions

Any missing/duplicate request ID, non-2xx status, malformed or timezone-naive timestamp, reversed time interval, stale deployed SHA, or provider assignment mismatch yields `BLOCKED`.
