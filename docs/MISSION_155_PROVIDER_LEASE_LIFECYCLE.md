# Mission 155 — Provider Lease Lifecycle Consistency

## Ten rounds

1. Audited M154 PR #155, confirmed it is Draft/open/unmerged, and verified the exact-head CI.
2. Created an isolated M155 branch from the audited M154 HEAD.
3. Reviewed durable claim, lease renewal, failure, and both completion paths.
4. Found that renewal could report success when wall-clock time moved backwards because MAX(updated_at, now) retained the old timestamp.
5. Changed renewal to require a strictly forward timestamp while the same generation remains live.
6. Made retry claims preserve the greatest previously recorded timestamp, preventing FAILED-to-PROCESSING transitions from moving time backwards.
7. Validated failure-transition timestamps and preserved monotonic updated_at on failure.
8. Added clock-regression and live-lease fences to both atomic-message and legacy completion paths; propagated configurable lease duration through MessengerBackend.
9. Added regression tests for clock rollback, same-time renewal, forward renewal, failure-state timestamp integrity, atomic no-publication, and legacy completion expiry.
10. Added a dedicated Python 3.12 CI workflow and this mission record; the PR remains Draft and unmerged.

## Safety invariants

- Provider lease timestamps are finite numeric values.
- A renewal only succeeds when it advances the stored timestamp and the lease is still live.
- FAILED-to-PROCESSING retries never move the stored timestamp backwards.
- Failure transitions preserve monotonic timestamps.
- Completion rejects clock regression and expired leases before changing the completion state or publishing a message.
- Attempt-generation fencing remains in force.

## Evidence boundary

CI tests use SQLite and controlled timestamps/fake providers. They do not prove a synchronized production clock, live provider inference, paid API use, production deployment, Android device activation, or physical AI-to-AI communication. No merge, deployment, external API key, or private browser-session access was performed.
