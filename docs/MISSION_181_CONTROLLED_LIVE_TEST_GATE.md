# Mission 181 — Controlled Live-Test Gate

## Purpose

M181 defines the final authorization boundary immediately before the first real two-AI exchange. The gate is evaluative only: it does not execute the test.

## Ten rounds

1. Audit M180 PR #182 and exact passing SHA.
2. Confirm M180 remains Draft/unmerged and its base is M179.
3. Define a side-effect-free authorization evidence contract.
4. Require an identified deployed staging commit.
5. Require an approved staging endpoint.
6. Require one PRIVATE room containing exactly AI-USER and AI-PEER.
7. Require each AI to have registered its own authenticated session.
8. Require explicit provider assignments and separate operator/provider-call authorization.
9. Test all fail-closed conditions and run CI without provider network calls.
10. Audit the final PR and report whether real execution remains blocked.

## Gate semantics

evaluate_gate() returns AUTHORIZED_FOR_OPERATOR_EXECUTION only when all required evidence is present. It always returns executionPerformed=false and providerCallsPerformed=false.

Those fields describe this gate function's own behavior, not external environment health.

## Required evidence

- deployed commit identified;
- approved staging endpoint identified;
- room PRIVATE with exactly AI-USER + AI-PEER;
- both AIs registered their own authenticated sessions;
- both AIs have explicit provider assignments;
- operator authorization explicit;
- provider-call authorization explicit.

Provider credentials are never stored in this evidence object.

## Execution boundary

An AUTHORIZED result does not automatically enable provider calls. The next step, if explicitly authorized, is operator execution in approved staging.

Until then: no deploy, no secret provisioning, no provider API call, no real AI-to-AI message, no device activation, and no automatic room creation or session registration.

## Future execution evidence

Record only non-secret metadata: deployed SHA, staging identifier, room ID, AI IDs, provider IDs, request/correlation IDs, timestamps and response status. Never record provider API keys, session bearer tokens, or other secrets.
