# Mission 141 — Authenticated Provider Host

## Objective

Define and implement the server-side security boundary required before two independently authenticated AI agents can exchange provider-generated responses in a private room.

## Ten rounds

1. **Baseline audit:** confirmed M139 supplies injected provider/attestation interfaces and M140 mounts the conversation panel, but neither supplies a production provider host.
2. **Trust boundary:** specified that the browser may request an agent turn but cannot assert its sender identity, provider identity, or authorization.
3. **Bearer authentication:** added a host contract that authenticates a bearer token through an injected server authenticator before provider execution.
4. **Room/agent authorization:** added an injected authorization gate binding the authenticated principal to the exact private conversation and its own agent identity.
5. **Strict request schema:** reject unknown fields, blank identifiers, invalid request IDs, and prompts over 5,000 characters.
6. **Server-side provider resolution:** provider selection is resolved by the server from the authorized agent; browser-supplied provider names and credentials are not accepted.
7. **Response attestation:** HMAC-SHA256 statement binds conversation, agent, request, principal, server identity, provider, model, issue time, and response SHA-256.
8. **Replay and capacity controls:** reject duplicate principal/request pairs and stop accepting new requests at the bounded in-memory request ceiling.
9. **Adversarial contract tests:** cover unauthenticated calls, cross-agent impersonation, schema injection, replay, oversized prompts, unavailable providers, key strength, and tampered response/attestation.
10. **CI and handoff:** add a dedicated Python 3.12 workflow and document the integration requirements and proof boundary.

## Implemented

- `server/ai_provider_host.py` is a transport-neutral, server-owned host contract.
- Authentication, room authorization, and provider invocation are injected dependencies; the module does not trust browser claims.
- Attestations use a minimum 32-byte server-held HMAC key and bind the response body digest.
- `server/test_ai_provider_host.py` contains deterministic unit tests with fake providers and authenticators.
- `.github/workflows/mission-141-authenticated-provider-host.yml` runs the isolated contract suite.

## Security and proof boundaries

- The module is **not yet mounted** as an HTTP endpoint and is not yet composed with the Rooms runtime or the existing messenger persistence/delivery path.
- The current tests use fakes. They prove the module's local contract only; they do not prove a live provider request, production key custody, independent real-world AI identities, message persistence, cross-device delivery, or a real AI-to-AI conversation.
- HMAC is a symmetric server-side integrity mechanism, not a public-key signature. The verifier must remain in a trusted server boundary. A browser must never receive the HMAC key.
- The replay set is process-local and in-memory. Production deployment requires durable idempotency, expiry/retention, distributed coordination, rate limits, audit events, and bounded memory.
- A provider failure currently consumes the request ID for the life of the host instance; retry semantics must be designed with durable idempotency before production.
- A real provider adapter must be explicitly configured and authorized. No free provider availability is assumed.
- No browser cookies, private ChatGPT sessions, session scraping, or UI automation are used.
- No API key, paid request, secret, service, deployment, device activation, merge, or publication was created or performed.

## Required next integration

1. Mount a strict authenticated HTTP route in `server/http_server.py` using the repository's existing request authentication and rate limiting.
2. Bind the host's authorization callback to authoritative room membership and the authenticated principal's registered agent identity.
3. Resolve only explicitly enabled provider adapters from server configuration; keep paid calls disabled by default.
4. Persist the provider response and verified attestation as a server-owned message, then deliver through the existing authenticated long-poll messenger.
5. Add end-to-end tests proving that two distinct principals can exchange messages in one private room without client-controlled sender identity.
6. Only after that, test with two separately authorized provider identities and record exact request IDs, response IDs, message IDs, and device evidence.

## Status

Implementation: **PARTIAL PASS** (isolated host contract and tests authored).  
CI: **PENDING** until a GitHub Actions run for the final commit is observed.  
Production integration / live AI communication: **BLOCKED** pending the integration steps above.
