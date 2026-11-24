# Mission 99 — AI-01 to AI-02 message path audit

## Ten-round execution record

1. Confirmed PR #97 remains Draft, open, unmerged, and mergeable; its head is the audit base.
2. Inspected the authenticated message submission path: sender identity is derived from the bearer credential, not trusted from a client-supplied sender field.
3. Confirmed recipient authorization requires the sender and every recipient to belong to the same server-owned conversation.
4. Traced message persistence and idempotency: the message and sender/request key are stored transactionally; retries with the same request return the original message.
5. Traced recipient delivery: pending reads are scoped to the authenticated recipient, conversation membership, and unacknowledged state.
6. Traced HTTP Long Poll: wait endpoint authenticates the principal, validates cursor/batch/timeout, waits for new messages, and returns sender/sequence/body metadata.
7. Traced ACK: only an authenticated conversation member listed as a recipient can acknowledge; repeat ACK is idempotent and acknowledged messages leave the pending queue.
8. Confirmed transport capability advertises HTTP_LONG_POLL only; WebSocket and server push remain disabled.
9. Added five focused backend contract tests for AI-01 → AI-02 wake/delivery, recipient-only ACK, outsider isolation, timeout/bounds, and transport policy; wired them into CI.
10. Preserved the external activation boundary: no staging deploy, no credentials, no real AI session, and no physical device communication were initiated.

## Evidence boundaries

- Audit base: M97 head `19231b2cf5c99469b4ced71280d25e1f877e8654`.
- The existing HTTP E2E suite already contains a two-principal HTTP send/read/ACK flow and a private-conversation test that restarts the backend before delivery and after ACK.
- The new M99 tests exercise backend behavior with test credentials mapped to AI-01, AI-02, and an unauthorized AI-03.
- These are automated tests against an in-process backend and local HTTP test server. They do not prove two independent AI agents, separate devices, cross-Wi-Fi reachability, or a deployed staging service.
- The staging Blueprint remains Free/ephemeral and manually deployed only; no Render service was created or activated by this mission.
- No merge, deploy, paid resource, payment information, secret provisioning, or physical device activation.

## Acceptance result

Code-level message/ACK contract: pending CI execution on this branch.
Real AI-01 ↔ AI-02 text contact: BLOCKED pending explicitly authorized staging activation and independent AI sessions.
