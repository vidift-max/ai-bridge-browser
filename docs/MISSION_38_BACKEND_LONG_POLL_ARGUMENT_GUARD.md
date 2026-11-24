# Mission 38 — Backend Long-Poll Argument Guard

## 10 rounds
1. Centralized the maximum safe sequence cursor alongside the existing server Long Poll limits.
2. Added strict cursor validation: integer only, no booleans, non-negative, and no greater than 9,007,199,254,740,991.
3. Added strict batch validation: integer only, no booleans, between 1 and the advertised maximum batch size (100).
4. Hardened wait validation to reject booleans, strings, NaN, infinities, negative values, and values above the advertised 25-second maximum.
5. Validate all wait arguments before entering the condition wait, preventing malformed input from reaching the wait loop.
6. Reused the same cursor/batch validator in the pending-message path to prevent divergent behavior between immediate reads and Long Poll.
7. Kept advertised capability limits and runtime enforcement tied to the same backend constants.
8. Added regression tests for invalid types, numeric boundaries, non-finite timeouts, and the maximum safe cursor.
9. Documented the guard behavior and compatibility boundary.
10. Added a dedicated CI workflow for backend tests and browser/Android regression gates.

## Security and compatibility
- Authentication and room-membership authorization remain enforced by the backend before message delivery.
- The browser/server sequence cursor uses the same safe-integer boundary.
- The API remains HTTP Long Poll only; WebSocket and Server Push remain disabled.
- Invalid direct backend arguments fail with explicit ValueError contracts.

## Proof boundaries
- CI demonstrates automated test behavior, not a deployed service.
- No provider identity, external AI automation, cross-network messaging, or physical-device validation is claimed.
