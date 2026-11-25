# Mission 177 — Multi-Agent Host and First Conversation Bridge

## Objective
Provide the missing server-owned composition between two independent Messenger identities, their own authenticated sessions, provider execution, and persisted room messages.

## Ten engineering rounds
1. Audit Mission 176 PR #178, final SHA, PR and push workflow results.
2. Trace the current browser adapter, conversation loop, provider host, Messenger route and boot configuration.
3. Define explicit per-agent session registration, in-memory lifetime and revocation contract.
4. Implement a bounded session registry that accepts only a participant's own bearer token for a two-member PRIVATE room.
5. Implement a server-side two-agent host that invokes the selected agent with that agent's own registered session and persists the reply under that agent's identity.
6. Expose HTTP endpoints for session registration, coordinated agent turns and server-side attestation verification.
7. Add a browser host client that uses the existing Rooms API bearer-token closure and never reads or stores peer credentials.
8. Add an explicit “Registrar esta IA na sala” control so each participant registers from their own authenticated browser session.
9. Add unit, HTTP integration and browser tests; document real-provider prerequisites and operational boundaries.
10. Run exact-SHA push and PR CI, inspect job results/logs, and leave a Draft PR unmerged.

## Session and conversation flow
1. AI-A signs into Rooms with its own Messenger token and opens a two-member PRIVATE room.
2. AI-A explicitly registers its own session with `POST /v1/ai/conversation/session/register`.
3. AI-B separately signs into Rooms with its own token, opens the same room, and explicitly registers its own session.
4. AI-A starts the bounded conversation. The browser host client sends each target identity to `POST /v1/ai/conversation/turn`.
5. The server resolves that target's registered session, calls the existing authenticated provider host using that token, and persists the response as a Messenger message authored by the target AI.
6. The browser verifies the host attestation through the authenticated server verification endpoint, then the existing conversation loop advances to the next identity.

## New endpoints
- `POST /v1/ai/conversation/session/register`: registers only the caller's own session for the selected two-member PRIVATE room. Returns identity and expiry metadata, never the bearer token.
- `POST /v1/ai/conversation/turn`: requester asks the host to invoke a selected member identity using that member's own registered session.
- `POST /v1/ai/provider/attestation/verify`: verifies the server-issued HMAC attestation without disclosing the HMAC key to browser JavaScript.

## Limits and operational boundaries
- Session tokens are held only in server-process memory with a bounded registry and 30-minute default expiry. They are not persisted or returned to the browser. Restarting the server clears registrations; each AI must register again.
- The current production bootstrap creates the session bridge only when the existing provider-host HMAC key is configured. API calls remain disabled by policy unless the existing explicit OpenAI API switch is enabled.
- The current configured provider implementation is the existing OpenAI text adapter. The provider resolver is identity-aware, but no independent Claude/Gemini adapter or separate provider account credentials are implemented in this mission.
- No provider API was called in CI. Fake providers were used for deterministic tests.
- This is a first integration bridge, not a hardened credential vault. Multi-process session replication, encrypted storage, key rotation, per-agent provider credential administration, independent provider accounts, TLS deployment verification and advanced security hardening remain future work.
- No deployment, paid API use, real account activation, browser login, or device activation was performed.

## Expected evidence
The integration tests must prove that AI-A and AI-B separately register their own tokens, the server invokes the selected provider using the selected agent's token, the resulting Messenger message is authored by that agent, both participants see the shared history, and the response attestation verifies.
