# Mission 186 — First Live-Test Readiness Audit

## Objective

Provide an offline, fail-closed audit of the prerequisites for a future first AI-USER → AI-PEER round trip. This is a readiness review only, not an execution permit.

## Ten rounds

1. Revalidate Mission 185 PR, exact head SHA, and CI.
2. Create an isolated M186 branch from the verified M185 head.
3. Define a typed readiness snapshot without credentials or message contents.
4. Bind readiness to the exact approved deployed SHA.
5. Require staging identity and independently verified health.
6. Require a verified private room with exactly AI-USER and AI-PEER.
7. Require one owned session for each AI and exact provider mapping.
8. Separate provider readiness, operator authorization, provider-call authorization, and stop-condition acknowledgement.
9. Add negative tests and offline CI; document the operator checklist.
10. Audit the final SHA, workflow result, PR state, and proof boundaries.

## Readiness states

- `BLOCKED`: at least one prerequisite is absent or mismatched.
- `READY_FOR_OPERATOR_REVIEW`: all supplied attestations pass structural checks. This state is not an execution authorization.

The evaluator always returns `executionAuthorized: false`, `executionPerformed: false`, `providerCallsPerformed: false`, and `networkCallsPerformed: false`.

## Operator checklist before any future live test

- [ ] Confirm approved commit SHA is deployed to the intended staging environment.
- [ ] Confirm staging identity, URL, and health using independent evidence.
- [ ] Confirm the room is private and contains only AI-USER and AI-PEER.
- [ ] Confirm both AIs registered their own authenticated sessions.
- [ ] Confirm exact provider IDs and that credentials remain server-side.
- [ ] Confirm provider readiness without exposing key values.
- [ ] Record operator authorization separately from provider-call authorization.
- [ ] Review stop conditions: identity mismatch, 401/403, 429, 5xx, timeout, malformed response, unexpected second turn, or evidence mismatch.
- [ ] Obtain explicit authorization for exactly one AI-USER → AI-PEER round trip.
- [ ] Stop immediately after the first successful round trip and preserve redacted evidence only.

## Proof limits

CI proves only deterministic validation logic using supplied metadata. It does not prove that staging exists, that provider accounts or credentials work, that a room/session is live, or that two real AIs exchanged messages. No deploy, secret access, provider API call, room creation, session registration, or message send is performed by this mission.
