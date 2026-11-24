# Mission 36 — Negotiated Long-Poll Runtime

## 10 rounds
1. Revalidated Mission 35 CI on its final commit before starting this mission.
2. Preserved the server-advertised minimum wait in the validated transport profile.
3. Added a bounded request-path builder that accepts only a valid room, sequence cursor, and negotiated profile.
4. Stored the validated transport profile only for the currently authorized guest room.
5. Replaced hard-coded long-poll timeout and batch size with the negotiated server values.
6. Added tests proving the default server profile produces the expected wait request.
7. Added tests for narrower server profiles, URL-encoded room IDs, and invalid cursor/timeout/batch bounds.
8. Added regression coverage that polling uses negotiated settings and session teardown clears the profile.
9. Documented runtime behavior and proof boundaries.
10. Added a dedicated CI workflow for browser, backend, and Android regression gates.

## Runtime behavior
- The guest browser validates the authenticated room capability response before loading the room.
- The validated timeout and maximum batch size are used in each HTTP long-poll request.
- A server may advertise stricter values than the current maximum; the client honors them.
- Invalid or missing negotiated state fails closed; no hard-coded fallback transport profile is used.
- The negotiated profile is cleared on failed entry, logout, and page teardown.

## Proof boundaries
- HTTP long polling remains the only implemented guest transport.
- This mission does not implement WebSocket, SSE, push notifications, or background delivery.
- It does not prove external provider identity, provider automation, cross-network calls, deployment, or physical-device operation.
- Backend authorization, sequence cursor, ACK, and long-poll limits remain authoritative.

## Acceptance
PASS requires the dedicated Mission 36 workflow to complete successfully on the final commit.
