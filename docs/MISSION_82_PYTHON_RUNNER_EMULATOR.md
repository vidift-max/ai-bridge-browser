# Mission 82 — Production Python runner against Firebase Emulators

## Ten rounds
1. Reconfirm Mission 81 push and pull-request workflows passed after the fixture correction.
2. Create an isolated feature branch from the validated Mission 81 PR head; keep PRs Draft and unmerged.
3. Inspect the existing production smoke runner and its HTTPS-only Firebase URL validation.
4. Add an explicit opt-in emulator mode, restricted to HTTP loopback hosts and the RTDB Emulator namespace.
5. Preserve production URL validation: HTTPS Firebase hosts only, with no query string or credentials.
6. Add unit coverage for emulator namespace parsing, loopback restrictions, and authenticated request query construction.
7. Provision ephemeral Auth Emulator users and RTDB fixture records in the existing emulator integration test.
8. Execute the existing Python smoke runner in a child process using Auth Emulator ID tokens for read-only preflight.
9. Execute the same runner with explicit --send; verify recipient delivery and sender-side ACK confirmation, and assert tokens are absent from child output.
10. Keep the test inside CI with the Auth + RTDB emulators; record boundaries and the next production-readiness gate.

## Security boundaries
- Emulator support requires MESSENGER_FIREBASE_EMULATOR=true and an HTTP loopback URL on port 9000 or 9001 with exactly one ns query parameter.
- Normal production mode remains HTTPS-only and accepts only Firebase RTDB host suffixes.
- Tokens are passed to the Python child process through its environment; stdout/stderr are checked for token leakage and the runner itself never logs request URLs.
- Test identities and messages exist only in ephemeral Auth/RTDB Emulator instances.
- No Firebase production project, production credentials, published rules, deployment, or physical device is used.

## Validation target
The integration workflow must prove the existing Python runner itself can complete authenticated preflight, POST one nonce message, GET it as the recipient, PUT an ACK, and verify that ACK as the sender. CI result is the source of truth; no PASS claim before it completes.
