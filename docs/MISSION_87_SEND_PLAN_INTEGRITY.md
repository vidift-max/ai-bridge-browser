# Mission 87 — First-message dry-run plan integrity

## Purpose
Strengthen the Mission 86 `--prepare-send` output so a proposed one-message AI-01 → AI-02 payload is explicitly bound to its identity pair and protected against accidental or unnoticed mutation before any separately authorized send.

## Plan integrity
- Adds `schema_version=1`.
- Computes `payload_sha256` over canonical UTF-8 JSON (sorted keys, compact separators).
- Validates sender, sole recipient, conversation, message kind, nonempty body, 280-character maximum, and integer timestamp.
- Verifies the digest before returning the plan.
- Rejects altered payloads, identity-pair mismatches, extra recipients, and modified safety metadata.

## Safety
The plan is still generated only after the three authenticated read-only Firebase GET checks. This mission does not add any Firebase write path: no POST, PUT, PATCH, or DELETE is used by `--prepare-send`. The report retains `write_operations=NONE`, `send_operation=NOT_EXECUTED`, `acknowledgement=NOT_RUN`, and `credentials_included=false`.

A SHA-256 digest detects accidental or subsequent payload changes; it is not a digital signature and does not authenticate the operator or prove recipient runtime availability. Actual production send remains a separate action behind the existing dual opt-in gate.

## Validation
Tests cover canonical digest generation, correct pair binding, payload tampering, additional recipients, message-size limit, safety metadata tampering, and the existing emulator/regression suite.
