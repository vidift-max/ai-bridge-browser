# Mission 104 — Use the real pending-message route

## Ten rounds

1. Re-read the M103 verifier and tests against the current server implementation.
2. Inspected `server/http_server.py` route dispatch for conversation messages.
3. Confirmed the server exposes `GET /v1/conversations/{id}/messages/wait` for pending-message retrieval.
4. Found the verifier's post-ACK check called `/v1/conversations/{id}/messages`, for which no matching GET route exists in the inspected handler.
5. Replaced that nonexistent route with the actual authenticated Long Poll route.
6. Preserved the exact-message sequence cursor (`after=sequence-1`) and bounded page size 100.
7. Set `timeout=0` for an immediate pending-state check, avoiding an unnecessary 25-second wait.
8. Updated regression fakes to distinguish initial receive (`timeout=25`) from post-ACK inspection (`timeout=0`).
9. Verified the success and negative test cases target the actual route and retain principal/sequence checks.
10. Added the branch to CI triggers and opened a Draft PR for review.

## Evidence boundary

- The previous post-ACK route mismatch is corrected against the inspected HTTP handler.
- Regression tests still use controlled fake HTTP responses; no live server or two real AI sessions were exercised.
- CI status must be checked on the final branch SHA before declaring PASS.
- No Render service, deployment, real credentials, paid resources, merge, or physical-device activation.
- HTTP Long Poll remains the sole realtime transport in scope.
