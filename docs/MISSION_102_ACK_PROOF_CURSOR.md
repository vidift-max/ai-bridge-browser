# Mission 102 — ACK proof cursor hardening

## Ten-round execution record

1. Re-opened the M101 first-contact runner and its focused unit tests.
2. Traced the real HTTP Long Poll handler and confirmed the route returns the authenticated recipient identity and pending messages.
3. Traced the real pending-message handler and confirmed its `after` parameter filters out messages at or below the supplied sequence.
4. Found a false-positive in M101: the post-ACK check used the received message sequence as its cursor, which could hide the very message being checked.
5. Changed the post-ACK verification cursor to `after=0` so the verifier examines the full bounded pending queue.
6. Increased the post-ACK query limit to the server-supported maximum of 100, avoiding a too-small default window.
7. Added an authenticated-recipient assertion to the post-ACK response; the check now requires `principalAiId=AI-02`.
8. Strengthened the successful and still-pending regression tests to require the full-queue cursor and recipient token.
9. Added a regression test that rejects a pending-check response attributed to AI-03.
10. Added this mission branch to the existing CI triggers; no deployment or real credentials were used.

## Safety and evidence boundaries

- The code-only regression closes a false-positive in the ACK proof.
- Tests use a controlled fake HTTP transport; this is not proof of a live AI-01 ↔ AI-02 exchange.
- No Render service was created or deployed.
- No real staging credentials were created, read, or printed.
- No paid plan, persistent disk, or payment information was used.
- No merge was performed; the resulting PR is Draft and `maintainer_can_modify:false`.
- HTTP Long Poll remains the only intended realtime transport; WebSocket/SSE remain out of scope.
