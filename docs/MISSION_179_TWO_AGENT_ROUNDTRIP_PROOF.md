# Mission 179 — Two-Agent HTTP Round Trip Proof

## Objective
Prove the complete server-side two-agent turn path over Messenger HTTP endpoints using two separately assigned provider adapters, without contacting external APIs.

## Ten engineering rounds
1. Audit Mission 178 PR, exact-SHA CI and provider/host/session implementation.
2. Trace the HTTP registration, turn and attestation verification routes.
3. Trace per-agent provider assignment, resolver and readiness preflight.
4. Add a deterministic HTTP integration fixture with two independent fake adapters.
5. Register each AI identity using its own authenticated Messenger credential.
6. Execute AI-A → AI-B → AI-A turns through the coordinated conversation endpoint.
7. Verify message authorship, recipient scope, persisted chronological history and provider-specific attestations.
8. Verify readiness reflects explicit provider assignments and does not depend on token enumeration.
9. Run Python server and browser host/panel/runtime tests on exact commit SHA.
10. Audit CI jobs and create a Draft PR without merge or deployment.

## HTTP test contract
- Each identity registers its own session for the same PRIVATE room containing exactly two members.
- Each turn targets a room member and uses that target's own registered session.
- AI-B is routed to the Anthropic fake adapter; AI-A is routed to the OpenAI fake adapter.
- The response message author must equal the invoked AI ID; the other participant is the recipient.
- Both participants must read the same chronological two-message history.
- Attestation provider identity must match the adapter selected for that turn.
- Readiness is generated from explicitly configured AI ID assignments and reports no credentials.

## Limits
- Adapters are deterministic fakes. No provider API, billing, internet, or real account is exercised.
- This proves HTTP application integration inside CI, not an externally deployed service.
- It does not prove independent provider account ownership, live connectivity, production secret management, durable session vaults, or physical device activation.
- No deployment, merge, secret provisioning, or live AI conversation is performed.
