# Mission 83 — Production Firebase send safety gate

## Ten rounds
1. Reconfirm the Python runner emulator integration passed on the previous mission's push workflow.
2. Start an isolated branch from the reviewed Mission 82 head; do not merge or deploy.
3. Audit the production send path and identify that --send alone could trigger an external message.
4. Add a second explicit CLI opt-in for production sends.
5. Require the matching MESSENGER_FIREBASE_ALLOW_PRODUCTION_SEND=true environment gate.
6. Keep read-only preflight available without either send opt-in.
7. Keep emulator sends available only in explicit loopback emulator mode, without production opt-in.
8. Add unit tests for missing CLI approval, missing environment approval, both approvals, emulator exemption, and read-only preflight.
9. Add a dedicated CI workflow for the production-send safety gate and existing regression suites.
10. Document that production sends remain disabled by default and require a separate user authorization before any real test.

## Resulting operator behavior
- Production read-only preflight: no additional opt-in.
- Production message send: requires both --send and --allow-production-send, plus MESSENGER_FIREBASE_ALLOW_PRODUCTION_SEND=true.
- Emulator message send: requires --send and explicit MESSENGER_FIREBASE_EMULATOR=true with a valid loopback URL and namespace; production opt-in is not required.
- This change does not grant permission to create a Firebase project, provision production identities, publish rules, or send a real message.

## Evidence boundaries
All tests are unit/CI or emulator-only. No production credentials or Firebase production requests are used. A successful CI run validates the guard logic, not a real AI-to-AI message.
