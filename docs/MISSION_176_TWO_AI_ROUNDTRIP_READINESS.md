# Mission 176 — Two-AI Round-Trip Readiness

## Objective
Prepare a first controlled A → B → A conversation test using two distinct AI identities and separate provider adapters. Security hardening beyond the existing minimum authenticated Messenger contract is explicitly deferred to a later mission.

## Ten rounds
1. Audit PRs 137–142 and identify the provider-to-Messenger path and existing CI blockers.
2. Trace the browser conversation loop, authenticated adapter, Rooms panel, provider host and Messenger persistence.
3. Identify the missing composition boundary: the panel requires a host object, while the server route executes only for the authenticated agent identity.
4. Extend the HTTP integration fixture to use a distinct deterministic provider instance for each AI identity.
5. Exercise AI-A's provider response and persist a Messenger message addressed to AI-B.
6. Exercise AI-B with its own bearer identity and feed it AI-A's persisted message body.
7. Exercise AI-A again with AI-B's persisted response, completing A → B → A.
8. Verify sender/recipient identities, per-agent provider call isolation, message histories and response attestations.
9. Document the exact manual/runtime prerequisites for replacing fakes with real providers without using browser cookies or private web sessions.
10. Run focused Python and browser regression CI and inspect exact final-SHA results.

## What the round-trip test proves
The deterministic integration test drives the actual local HTTP route, authenticated principal resolution, provider-host dispatch, SQLite-backed Messenger persistence and recipient history. AI-A and AI-B use distinct bearer tokens and distinct fake provider instances. Three provider responses complete the sequence A → B → A, and each response is verified against its host attestation.

## What it does not prove
The test does not call real model APIs, establish independent commercial provider accounts, deploy a server, activate browser tabs, or prove a live long-poll delivery to a physical device. The browser panel still requires a configured `AIBridgeAgentHost`; the server provider route requires the bearer token for the identity whose provider is being invoked. An orchestrator/host composition that safely supplies each agent's own session remains a prerequisite for a real automatic conversation.

## First real test prerequisites
- Two registered AI identities in the same PRIVATE room.
- A distinct valid session for each identity, held by the server-side host/orchestrator (not copied into page JavaScript).
- Two configured provider adapters with explicit provider/model mapping.
- Provider calls remain disabled unless the owner separately authorizes their cost and configuration.
- A bounded turn count and explicit user start/stop.
- The test must be labeled simulated until real provider responses and Messenger delivery are observed.

## Security scope
This mission retains the existing authentication and exact two-member PRIVATE-room requirements because they are intrinsic to the current Messenger contract. It does not add advanced cryptography, remote witness/quorum, key rotation, independent administrative domains, or production hardening. Those remain deferred.

No secrets were created, no paid API was called, no deployment or device activation occurred, and no PR was merged.
