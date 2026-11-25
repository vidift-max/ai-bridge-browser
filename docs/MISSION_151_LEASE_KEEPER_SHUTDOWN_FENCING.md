# Mission 151 — Lease Keeper Shutdown Fencing

## Ten-round scope

1. Audited M150 PR #151, including the final CI run and exact head SHA.
2. Created an isolated branch from the M150 head without merging either PR.
3. Identified a shutdown race: the heartbeat thread could still be inside its renewal callback when the provider route proceeded.
4. Added an explicit keeper lifecycle state and a configurable bounded shutdown wait.
5. Made an in-flight renewal that outlives shutdown mark lease ownership as uncertain.
6. Made the HTTP provider route inspect keeper state only after leaving the context manager.
7. Rejected response persistence whenever renewal failed, ownership was lost, or the heartbeat thread did not stop cleanly.
8. Validated interval and shutdown timeout inputs, rejecting booleans, NaN, and infinities; prevented restarting a keeper instance.
9. Added deterministic tests for clean shutdown, blocked renewal, callback exception, invalid timing values, and double start.
10. Added dedicated Python 3.12 CI and this evidence-boundary record; opened a Draft PR without merge or deployment.

## Safety invariant

The provider response is eligible for persistence only after the lease keeper has stopped and has not reported loss. If a renewal callback remains in flight beyond the bounded shutdown wait, the route fails closed and does not persist that response. Existing SQLite attempt-generation fencing remains the final atomic guard.

## Default behavior

- Heartbeat interval: 60 seconds.
- Lease duration: 360 seconds.
- Shutdown wait: 5 seconds.
- The keeper is single-use; a second start raises an error.
- A renewal exception, rejected renewal, or shutdown timeout marks the lease as lost.

## Evidence boundary

CI tests use controlled callbacks, SQLite, and fake providers. They do not prove live provider inference, production deployment, or physical AI-to-AI communication. No API key, paid call, device activation, private browser session access, or merge was performed.
