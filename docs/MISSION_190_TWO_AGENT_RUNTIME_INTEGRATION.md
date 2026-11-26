# Mission 190 — Two-Agent Runtime Integration

## Goal

Make the production HTTP server and the integration tests use one identical
composition path for the two-agent messaging runtime. The target is the first
real, controlled AI-USER ↔ AI-PEER exchange; this mission does not perform that
external execution.

## Changes

- Introduces `build_two_agent_runtime` as the single composition factory for
  provider routing, authenticated provider execution, per-agent session
  registration, and the coordinated conversation host.
- The HTTP server now uses that factory instead of maintaining a second,
  hand-written composition graph.
- The host HMAC key is rejected unless it is valid hex representing exactly
  32 bytes. A missing key leaves provider execution unavailable (fail closed).
- Adds production-composition tests for independent provider routing, both
  directions of a persisted round trip, per-agent attestations, disabled
  provider-call policy, missing assignments, and invalid/missing host keys.
- CI also reruns the existing HTTP, session bridge, browser client, panel, and
  conversation runtime regression suites.

## Runtime configuration

The server process must be configured by its operator with:

- `AI_PROVIDER_HOST_HMAC_KEY_HEX`: exactly 32 bytes encoded as 64 hex chars.
- `MESSENGER_AI_PROVIDER_MAP`: explicit map, e.g.
  `{"AI-USER":"openai","AI-PEER":"anthropic"}`.
- The corresponding provider API key and explicit provider-call policy switch
  for each assigned provider.
- Two separate authenticated AI identities, each registering its own session
  in the same private room containing exactly those two identities.

Credentials stay server-side. Never put provider keys or bearer tokens in
browser storage, reports, fixtures, or PR comments.

## Operator sequence for the first real test

1. Deploy the reviewed commit to a private staging service (separate approval).
2. Configure the runtime environment and validate provider readiness without
   exposing credentials.
3. Create or select a private room with exactly AI-USER and AI-PEER.
4. Sign in independently as each AI identity and register each own session.
5. Confirm each identity maps to a different intended provider.
6. Obtain explicit operator authorization for provider API calls and the
   bounded first-turn test.
7. Send one message AI-USER → AI-PEER, verify the persisted reply, then one
   response AI-PEER → AI-USER. Stop after the first complete round trip.
8. Preserve redacted request IDs, timestamps, provider IDs, message authorship,
   HTTP statuses, and attestation verification results as evidence.

## Evidence boundaries

- CI uses fake adapters only. No real provider API calls, credentials, staging
  deployment, room creation, session registration, or live messages are used.
- `MATCHED` readiness is not proof of external provider connectivity, billing,
  quota, account validity, or successful model inference.
- The session registry remains in process memory with bounded TTL; a process
  restart clears registrations. This mission does not add a durable session
  vault or multi-process session replication.
- A successful simulated round trip is not a real two-AI conversation.
- Deployment, secret provisioning, provider-call activation, and live execution
  remain separate operator-authorized actions.
