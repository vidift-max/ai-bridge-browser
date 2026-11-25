# Mission 147 — Provider Retry Recovery

## Ten-round scope

1. Re-verified M146 final CI before starting M147.
2. Created an isolated M147 branch from the M146 final SHA.
3. Audited replay reservation behavior when provider execution fails.
4. Identified that failed provider attempts could retain a process-local replay key until TTL expiry.
5. Changed the provider host to release the replay reservation after provider-side failure.
6. Added regression coverage for transient provider exceptions.
7. Added regression coverage for malformed provider responses.
8. Preserved duplicate protection while a successful request remains completed.
9. Added dedicated M147 CI and evidence-boundary documentation.
10. Kept the work Draft/unmerged with no live provider or device activity.

## Recovery semantics

The process-local replay guard reserves a request before provider execution so concurrent duplicate attempts are rejected. If provider execution fails or returns an invalid provider result, that reservation is removed, allowing a legitimate retry with the same request ID.

Successful requests remain protected by the replay guard. The durable provider-request ledger remains authoritative for the HTTP provider flow and durable idempotency.

## Evidence boundary

Tests use fake providers. No API key was created or enabled. No paid provider call, deployment, device activation, private browser session access, or live AI-to-AI inference was performed.
