# Mission 153 — Provider Lease Completion Fencing

## Ten-round scope

1. Audited M152 PR #153, exact head SHA, and the successful PR CI run before starting new work.
2. Created an isolated branch from the audited M152 commit.
3. Reviewed the provider request claim, heartbeat renewal, and atomic message completion path.
4. Identified that durable completion fenced attempt generation but did not independently reject a lease that had expired before completion.
5. Added finite, positive lease-duration validation for claim, renewal, and completion operations.
6. Added a live-lease expiry check inside the SQLite atomic completion transaction, before message and idempotency rows are committed.
7. Added a conditional generation-and-expiry guard to the completion update so a stale or expired attempt cannot mark the request COMPLETED.
8. Propagated the lease duration through MessengerBackend and mapped expired completion to HTTP 409; the request is marked FAILED only if the same generation still owns it.
9. Added store and HTTP regression tests for expired completion, no message publication, invalid lease durations, and stale-generation fencing.
10. Added a dedicated Python 3.12 CI workflow and this mission record; the PR is Draft and unmerged.

## Safety invariant

A provider response may be atomically persisted only when the request is still PROCESSING, the attempt generation matches, the request digest matches, and the lease is still live at the completion timestamp. An expired lease returns a conflict and does not publish a room message.

## Evidence boundary

Tests use SQLite and fake provider callbacks. They do not prove live provider inference, paid API calls, production deployment, Android device operation, or physical AI-to-AI communication. No merge, deployment, device activation, private browser-session access, or external API key was used.
