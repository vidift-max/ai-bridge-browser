# Mission 33 — Guest Transport Lifecycle Safety

## 10 rounds
1. Revalidated Mission 32 CI as successful on the starting SHA before changing transport behavior.
2. Audited the long-poll request lifecycle across logout, session failure, visibility changes, and late HTTP responses.
3. Added an in-memory AbortController for the active guest long-poll request.
4. Aborted an in-flight long poll when the guest session is logged out or torn down.
5. Aborted an in-flight long poll when the browser document becomes hidden, preventing unnecessary background waits.
6. Added a session-generation guard so responses from an older session cannot mutate the current room UI.
7. Treated expected AbortError cancellation as a silent lifecycle event rather than a transport failure/backoff signal.
8. Preserved the existing 20-second long-poll, cursor, acknowledgement, presence, visibility, and bounded retry contracts.
9. Added browser regression coverage for cancellation, hidden-tab abort, and stale-response isolation.
10. Added dedicated Mission 33 CI and documented the resulting proof boundaries.

## Security and proof boundaries
- Session credentials remain memory-only in the guest browser.
- Cancellation is client-side lifecycle control; it does not revoke server credentials.
- Server authentication, room authorization, message cursoring, acknowledgement, and long-poll limits are unchanged.
- No WebSocket, provider verification, external AI automation, deployment, or physical-device validation is claimed.
- No claim is made that a canceled HTTP request immediately stops server-side work on every network/server stack; the client no longer consumes or applies the stale response.
- Paid APIs, model downloads, and inference remain outside this mission.

## Acceptance
PASS requires the Mission 33 CI workflow to complete successfully on the final SHA.
