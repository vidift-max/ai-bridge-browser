# Mission 25 — Restore Validation Edge-Case Hardening

## Ten-round execution record
1. Inspected the current schema/data validators and their existing regression tests.
2. Tightened schema validation to inspect the required index definition rather than its name alone.
3. Required the conversation/sequence index to be UNIQUE.
4. Required the exact ordered index columns: conversation_id, sequence.
5. Added strict parsing for comma-delimited identifier lists.
6. Rejected empty conversation membership and malformed empty segments instead of silently filtering them.
7. Rejected duplicate, whitespace-padded, and non-text identifier-list values without leaking exceptions.
8. Added regression tests for malformed lists and incorrect index definitions.
9. Updated operator runbook and backend documentation with precise acceptance limits.
10. Added the final same-HEAD verification marker; CI results determine the final verdict.

## Safety
All candidate inspection remains SQLite read-only. No normalization, repair, migration, deletion, promotion, or activation occurs. Empty recipient lists remain allowed because the current persistence model can represent them. The validator does not infer rules that are not supported by the stored schema.

## Verification
- Backend Test: pending
- Android Build: pending
- Exact final HEAD: pending at closure creation
- Live restore / deployment / physical-device test: not performed

## Verdict
Implementation record: 10/10 rounds. Mission verdict remains BLOCKED until Backend Test and Android Build both succeed on the same final commit.