# Mission 37 — Strict Long-Poll Query Contract

## 10 rounds
1. Established the negotiated server contract as the source of truth: sequence cursor, batch size 1–100, and wait timeout 0–25 seconds.
2. Added a dedicated parser for long-poll query strings rather than relying on permissive defaults.
3. Restricted the request to exactly three parameters: `after`, `limit`, and `timeout`.
4. Rejected duplicate keys, unknown keys, missing keys, empty values, malformed separators, and excessive field counts.
5. Required ASCII decimal integers; signs, whitespace, decimal fractions, and Unicode digit lookalikes fail closed.
6. Bounded the sequence cursor to JavaScript's maximum safe integer so browser and server cursor semantics agree.
7. Enforced batch size 1–100 and timeout 0–25 seconds, including valid zero-wait behavior.
8. Wired the authenticated long-poll route to the strict parser; invalid requests return the existing HTTP 400 error contract.
9. Added focused backend tests for defaults, narrower profiles, boundaries, duplicates, malformed values, and out-of-range values.
10. Added a dedicated CI workflow for strict-query tests plus browser, backend, and Android regression gates.

## Security and compatibility
- Authentication and room membership checks remain mandatory before waiting for messages.
- The backend remains authoritative for message visibility, sequence ordering, and ACK.
- The browser's negotiated request shape is accepted; malformed or ambiguous query strings are rejected.
- The API does not add WebSocket, SSE, push notifications, provider automation, or background delivery.

## Proof boundaries
- Automated tests validate parser behavior and regressions only.
- No deployed server, external provider identity, cross-network communication, or physical-device behavior is claimed.
- The Mission 36 CI repair is tracked independently; Mission 37's own CI must pass before acceptance.
