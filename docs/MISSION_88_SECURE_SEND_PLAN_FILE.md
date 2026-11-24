# Mission 88 — Secure local send-plan file

## Objective
Make the Mission 87 dry-run plan portable between preparation and review without introducing a Firebase write path.

## Behavior
- `--prepare-send --plan-output <path>` performs the existing three authenticated read-only GET checks, then creates a new JSON file with exclusive creation and mode `0600`.
- Existing files are never overwritten. Symbolic links are not followed where the platform exposes `O_NOFOLLOW`.
- The file is flushed and fsynced before success is reported.
- `--verify-plan-file <path>` loads a bounded (64 KiB) regular JSON file and validates schema, identity pair, recipient, payload digest and safety metadata locally.
- Verification prints only a sanitized summary and makes zero Firebase requests.
- `--plan-output` is valid only with `--prepare-send`; verify mode cannot be combined with network or send flags.

## Security boundaries
The plan contains the proposed message body and a nonce, but no Firebase ID tokens. File permissions are requested as owner-only (0600), subject to host filesystem semantics. Exclusive creation prevents accidental overwrite. SHA-256 is an integrity checksum, not a signature or operator authentication. Local verification does not establish current Firebase membership or prove either AI is online; it validates only the saved artifact against the configured AI pair.

## Safety
No production POST, PUT, PATCH or DELETE was added. Preparing still uses three GET requests; verifying a saved plan uses no network requests. Actual sending remains separate and protected by the existing dual opt-in.

## Validation
Tests cover private file mode, no-overwrite behavior, local round-trip validation, symlink rejection, CLI option boundaries, no network during verification, and secret redaction, alongside the existing Auth/RTDB Emulator regression suite.
