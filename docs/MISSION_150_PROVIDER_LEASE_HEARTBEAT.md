# Mission 150 — Provider Lease Heartbeat

## Ten-round scope

1. Audited M149 PR #150 and its dedicated CI before creating this branch.
2. Corrected the duplicate synchronization decorator discovered during the M149 audit; its dedicated CI is rerun on the corrected head.
3. Identified that a fixed six-minute PROCESSING lease could expire during a slow synchronous provider call.
4. Added generation-fenced durable lease renewal to SQLite.
5. Added authenticated backend plumbing for lease renewal.
6. Added a bounded background lease keeper that renews every 60 seconds while provider execution is active.
7. Made renewal fail closed: expired, completed, failed, or superseded claims cannot be renewed.
8. Made the HTTP route reject persistence if the lease keeper reports ownership loss; generation fencing remains the final atomic guard.
9. Added tests for successful renewal, expired/stale generation rejection, and lease keeper loss/stop behavior.
10. Added dedicated CI and documentation; opened a Draft PR without merge or deployment.

## Lease behavior

- Default lease: 360 seconds.
- Renewal interval: 60 seconds.
- A renewal updates the durable lease timestamp only when the same request digest and attempt generation still own a live PROCESSING claim.
- The keeper stops when provider execution returns.
- If renewal fails or throws, the route does not persist that provider response.
- SQLite generation checks still protect the final commit if a newer attempt wins a race.

## Evidence boundary

The tests use SQLite and controlled callbacks/fake providers. They do not prove live provider inference, production deployment, or physical AI-to-AI communication. No API key, paid call, device activation, private browser session access, or merge was performed.
