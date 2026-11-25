# M139 — Authenticated AI Agent Adapters

## Goal
Define a safe provider boundary for the M138 bounded conversation controller. The browser must never impersonate another AI identity or hold provider secrets.

## Ten rounds
1. Audit M138: found that its injected `respond` and `deliver` callbacks were not an authenticated provider integration.
2. Define exact two-member PRIVATE-room context and fail-closed membership checks.
3. Add an adapter that delegates provider execution to a host-supplied `requestAgent` boundary.
4. Require the host to verify a non-empty server attestation before accepting an agent response.
5. Bind every request to the current conversation, requester identity, selected agent, turn and maximum turn count.
6. Recheck room and identity after asynchronous provider execution to reject stale responses.
7. Separate local UI delivery from server message submission; the display callback cannot claim a new sender identity.
8. Add negative tests for forged identities, invalid room membership, missing/invalid attestation, stale context and oversized content.
9. Add a dedicated CI workflow for adapter and M138 controller regression tests.
10. Document operational gates and keep the PR draft and unmerged.

## Adapter contract
- `requestAgent` is injected by a trusted host/server integration. Provider credentials must remain server-side.
- `verifyAttestation` must validate a server-issued, cryptographically authenticated proof binding conversation, agent identity, response and turn. The browser callback itself is not proof.
- `onMessage` is a local presentation callback only. It must not submit a message as the peer.
- The current repository does not yet provide a production provider runtime or an attestation issuer/verifier. Until those are supplied and independently tested, this is an integration seam, not live AI-to-AI communication.

## Validation
Run `node --test web/ai-agent-adapter.test.mjs web/ai-conversation-loop.test.mjs` in CI. Tests use controlled fakes and prove contract behavior only, not real inference, real identity credentials, physical devices or deployment.

## Safety / scope
No cookie/session scraping, no reading private ChatGPT tabs, no paid API keys, no secrets, no Render resources, no deploy, no device activation, no merge.
