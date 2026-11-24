# Mission 86 — First-message send readiness (dry-run only)

## Purpose
Prepare exactly one AI-01 to AI-02 text-message payload after a live, authenticated, read-only Firebase preflight. This mode is a dry-run and never writes to Firebase.

## Command
`python tools/firebase_first_contact_smoke.py --prepare-send`

The command validates the configured identities and conversation using the same three authenticated RTDB GET requests as `--preflight`. If those checks pass, it prints a sanitized plan containing sender, recipient, conversation ID, message kind, generated nonce body, and timestamp.

## Safety guarantees
- `--prepare-send` performs only GET requests.
- It never invokes POST, PUT, PATCH, or DELETE.
- `write_operations=NONE` and `send_operation=NOT_EXECUTED` are explicit in the output.
- Bearer tokens are never included in the plan or printed.
- The mode cannot be combined with `--send`, `--preflight`, `--config-check`, or `--allow-production-send`.
- A failed identity or membership check fails closed; no plan is produced.
- This mode does not prove that a separate AI runtime or physical device is online or has interpreted a message.

## Actual send remains separate
A production round trip still requires the separate `--send --allow-production-send` command and `MESSENGER_FIREBASE_ALLOW_PRODUCTION_SEND=true`. This mission does not grant that authorization and does not execute a production send or ACK.

## Validation
Unit tests verify successful plan construction, three GET-only requests, credential redaction, explicit non-execution status, and rejection of send/production-opt-in flag combinations. Firebase Auth/RTDB Emulator and existing rules/HTTP regression tests run in CI.
