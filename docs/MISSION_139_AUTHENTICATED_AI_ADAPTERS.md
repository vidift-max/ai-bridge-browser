# M139 — Authenticated AI Agent Adapters

## Goal
Define a safe provider boundary and composition runtime for the M138 bounded conversation controller. The browser must never impersonate another AI identity or hold provider secrets.

## Ten rounds
1. Audited M138's injected callbacks and identified that they did not themselves establish authenticated provider identity.
2. Defined exact two-member PRIVATE-room validation.
3. Implemented a provider boundary delegating execution to a host-supplied `requestAgent`.
4. Required a host verifier to validate server-issued response attestation.
5. Bound requests to conversation, requester, selected agent and bounded turn metadata.
6. Rechecked room and identity after asynchronous provider execution.
7. Separated local presentation from server message submission.
8. Added negative contract tests for forged identities, invalid membership, attestation failure, stale context and content limits.
9. Added a composition runtime that wires the authenticated adapter into the bounded conversation controller, with integration tests and a dedicated workflow.
10. Documented the exact production gates and opened a draft PR without merge/deploy.

## Adapter contract
- `requestAgent` is injected by a trusted host/server integration. Provider credentials remain server-side.
- `verifyAttestation` must validate a server-issued cryptographic proof binding conversation, agent identity, response and turn.
- `onMessage` is a local presentation callback only. It must not submit a message as the peer.
- The runtime alternates agent targets through the M138 controller, but it does not supply the production provider runtime or cryptographic verifier.
- The Rooms page does not yet instantiate this composition runtime. A production host integration and independent provider identities are still required.

## Validation
CI command: `node --test web/ai-agent-adapter.test.mjs web/ai-conversation-loop.test.mjs web/ai-conversation-runtime.test.mjs`. Tests use controlled fakes; they do not prove live inference, real credentials, device communication or deployment. CI status must be checked independently.

## Safety / scope
No cookie/session scraping, private ChatGPT tab access, paid API keys, secrets, Render resources, deployment, device activation or merge.
