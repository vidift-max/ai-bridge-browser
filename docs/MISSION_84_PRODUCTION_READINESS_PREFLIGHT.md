# Mission 84 — Production readiness preflight (read-only)

## Ten completed engineering rounds
1. Rechecked Mission 83: both push and pull-request workflows passed; PR #82 remains Draft and unmerged.
2. Created an isolated Mission 84 branch from the validated Mission 83 commit.
3. Audited the existing smoke runner and separated configuration readiness from live Firebase preflight.
4. Added `--production-readiness`, a local-only configuration check that performs no HTTP requests.
5. Made the result explicit: CONFIG_READY, network_requests=NONE, message_round_trip=NOT_RUN, production_send=NOT_AUTHORIZED.
6. Kept production send authorization independent; readiness mode rejects `--send` and `--allow-production-send`.
7. Tightened production RTDB URL validation to reject custom paths, unexpected ports, malformed ports, query strings, fragments, and non-Firebase hosts.
8. Rejected whitespace in bearer ID tokens while keeping all token values out of output and error messages.
9. Added tests for network-free success, token redaction, incompatible flags, missing configuration, URL restrictions, and token formatting.
10. Added a dedicated GitHub Actions workflow and operator documentation; no production Firebase request, message, rule publication, deployment, or physical device action was performed.

## Operator use

Set the six required environment variables already documented by the first-contact runner, then execute:

```sh
python tools/firebase_first_contact_smoke.py --production-readiness
```

A successful result means only that required values and basic formats are present. It does **not** prove that credentials are valid, identities exist, the conversation is provisioned, rules are published, or either AI can communicate.

The command is deliberately local-only. It does not call Firebase, read remote identity records, send a message, or authorize production sends. A subsequent real first-contact test still requires a separate explicit user authorization and the existing double opt-in for production sends.

## Evidence boundary

Automated tests validate the local command and safety properties. CI success is not evidence of production connectivity, live AI-to-AI delivery, audio, calls, or physical AI-PHONE operation.
