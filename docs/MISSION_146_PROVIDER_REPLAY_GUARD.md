# Mission 146 — Provider Replay Guard Hardening

## Ten-round scope

1. Re-verified M145 final CI before starting M146.
2. Created an isolated M146 branch from the M145 final SHA.
3. Reviewed the provider host replay guard and identified process-local retention as permanently capacity-consuming.
4. Added a bounded replay TTL to the in-memory guard.
5. Added deterministic cleanup of expired replay entries before capacity checks.
6. Added explicit positive validation for replay capacity and TTL configuration.
7. Centralized the provider response-size limit as a named host constant.
8. Added regression tests for replay expiry, capacity recovery, and invalid configuration.
9. Added a dedicated M146 CI workflow with compile and provider/messenger regression suites.
10. Kept the work Draft/unmerged and preserved the no-live-provider evidence boundary.

## Evidence boundary

This mission hardens the process-local replay guard only. The durable provider-request ledger remains the authoritative recovery/idempotency mechanism in the HTTP path, which already bypasses the process-local guard for the durable request flow.

No API key was created or enabled. No paid provider call, deployment, device activation, private browser session access, or live AI-to-AI inference was performed.

The M146 replay guard now expires entries after a configurable positive TTL (default 300 seconds), preventing old request keys from permanently consuming the host's bounded in-memory capacity.
