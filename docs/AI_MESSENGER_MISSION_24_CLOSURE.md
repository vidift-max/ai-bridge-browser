# Mission 24 — Restore Candidate Data Consistency

## Objective
Extend isolated restore-candidate validation beyond SQLite integrity and schema shape by checking the relational invariants represented by the current Messenger schema. All checks are read-only.

## Ten-round record
1. Inspected the actual SQLite schema and persistence methods before defining invariants.
2. Confirmed the stored conversation membership representation and message fields; avoided assumptions about fields not persisted.
3. Implemented read-only loading of conversations and membership sets.
4. Added message checks for existing conversation, member sender, member recipients, non-empty identifiers, and positive sequence.
5. Added idempotency reference checks against the target message's sender and client request ID.
6. Added acknowledgement checks against an existing message and conversation membership.
7. Integrated data consistency into the existing integrity + schema candidate-validation gate.
8. Added fixtures for valid data, orphan conversation, invalid sender, invalid recipient, mismatched idempotency, invalid acknowledgement, and invalid sequence.
9. Added read-only preservation and redacted operational-event tests; documented scope and operator handling.
10. Added final verification marker; Backend Test and Android Build must both succeed on the exact resulting HEAD for PASS.

## Stable outcomes
- RESTORE_DATA_UNAVAILABLE
- RESTORE_DATA_CONVERSATION_INVALID
- RESTORE_DATA_MESSAGE_INVALID
- RESTORE_DATA_IDEMPOTENCY_INVALID
- RESTORE_DATA_ACKNOWLEDGEMENT_INVALID
- RESTORE_DATA_UNREADABLE
- RESTORE_DATA_CONSISTENT
- Combined candidate failure: RESTORE_CANDIDATE_DATA_INCONSISTENT

## Safety boundaries
The validator opens the candidate in SQLite read-only mode. It does not migrate, repair, rewrite, delete, promote, activate, or restore over a live database. It emits generic diagnostics and does not log candidate paths or message contents.

These checks do not establish provenance, authenticated identity, delivery semantics, correctness of message content, complete business rules, production recoverability, or application startup. A successful candidate is still not approved for production. Any promotion requires a separate explicit authorization and procedure.

## Final verification
- Backend Test: pending
- Android Build: pending
- Exact final HEAD: pending at closure creation
- Deployment / physical-device test / live restore: not performed

## Verdict
Implementation record: 10/10 rounds completed. Mission verdict remains BLOCKED pending same-HEAD Backend Test and Android Build success.