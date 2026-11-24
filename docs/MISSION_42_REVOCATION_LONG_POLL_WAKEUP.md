# Mission 42 — Revocation-Aware Long Poll Wakeup

## Objective
Ensure an HTTP Long Poll waiting on an empty room is promptly re-evaluated when a provisioned guest loses room access.

## Change
After the persistent guest revocation succeeds and the in-memory room membership is removed, the backend notifies the shared message condition. Waiting polls wake, re-run the normal pending/authentication path, and fail closed for the revoked credential instead of sleeping until the original timeout.

## Regression coverage
A threaded test provisions a guest, starts an empty room-scoped long poll, observes that it entered the condition wait, revokes the guest, and verifies the poll exits promptly with an authorization failure and returns no messages.

## Scope
HTTP Long Poll remains the only enabled realtime transport. No WebSocket/SSE, provider automation, deployment, or physical-device validation is included.
