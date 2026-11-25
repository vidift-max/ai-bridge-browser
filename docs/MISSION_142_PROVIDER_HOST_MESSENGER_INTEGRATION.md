# Mission 142 — Provider Host and Messenger Integration

## Objective

Mount the M141 authenticated provider host behind an authenticated HTTP route and use the existing Messenger backend to persist and deliver the provider response to the other member of an exact two-person PRIVATE room.

## Ten rounds

1. **Runtime audit:** traced the existing HTTP authentication, private-room membership, SQLite message persistence, and Long Poll delivery paths.
2. **Host wiring:** added an optional server-owned `provider_host` dependency to the HTTP handler; the endpoint fails closed with 503 when it is not configured.
3. **HTTP endpoint:** mounted `POST /v1/ai/provider/respond` with strict JSON parsing and bounded request size.
4. **Principal binding:** authenticated the bearer token using the existing request context and revalidated the credential generation before work.
5. **Private-room policy:** host authorization requires the authenticated principal to equal the requested agent identity, the room kind to be PRIVATE, and exactly two registered members.
6. **Provider policy:** server bootstrap resolves the existing OpenAI adapter only for registered AI identities and only when both an API key is configured and `OPENAI_API_CALLS_ENABLED=true`. No provider name or credential is accepted from the browser.
7. **Messenger persistence:** the response is submitted using the same authenticated bearer token, so the Messenger backend derives the sender identity; recipients are computed from authoritative room membership.
8. **Long Poll delivery and audit:** persisted messages enter the existing message queue/history path; a provider-response audit event records the message ID, provider, and model.
9. **Adversarial HTTP tests:** added fake-provider integration tests for successful persistence/delivery, missing auth, agent impersonation, GROUP room rejection, unknown fields, disabled host, oversized output, and provider errors.
10. **CI and handoff:** added a dedicated Python 3.12 workflow and documented operational configuration, limitations, and proof boundaries.

## Implemented

- `POST /v1/ai/provider/respond` in `server/http_server.py`.
- Optional server host configuration through `AI_PROVIDER_HOST_HMAC_KEY_HEX` (hex-encoded key, at least 32 bytes).
- The provider route is unavailable unless the HMAC key is configured.
- Provider execution remains disabled unless `OPENAI_API_CALLS_ENABLED=true` and `OPENAI_API_KEY` are both configured.
- The route accepts only `conversationId`, `agentId`, `requestId`, and `prompt`.
- The authenticated participant can request only its own agent identity; the server determines the peer recipient.
- Provider text is persisted as a normal Messenger message under the authenticated AI identity. The peer receives it through the existing pending/history/Long Poll mechanisms.
- The initiating HTTP response includes the host attestation. The server audit event records the message ID, provider, and model.
- Tests use a deterministic fake provider; they do not call a paid API.

## Important limitations

- The production bootstrap currently maps registered AI identities to the same configured OpenAI project adapter. This does **not** establish separate provider accounts or independent model identities for each AI. It is a shared project credential, and paid calls remain disabled by default.
- No free provider or free inference quota is assumed. A local/free provider adapter still needs a separately reviewed integration.
- The HMAC attestation is returned to the requesting participant but is not yet stored as a durable attachment to the Messenger message. The peer receives the persisted response body through Long Poll, not the attestation object. Durable attestation storage and peer-side verification remain a follow-up.
- The host replay registry is process-local and one-time. A retry after a completed request currently receives a duplicate-request response rather than a replayed cached result. Durable end-to-end idempotency and recovery after a process restart remain required.
- The route currently has no independent provider budget/quota ledger; global rate limiting is inherited from the Messenger HTTP handler. Add per-agent/provider budget controls before enabling paid calls.
- CI results must be observed for the final commit before PASS can be declared.
- Unit tests use fake providers and an in-memory SQLite store. They do not prove a live provider request, production HMAC key custody, a deployed server, two separate provider accounts, or physical-device delivery.

## Required runtime configuration

- `AI_PROVIDER_HOST_HMAC_KEY_HEX`: server-only hex key of at least 32 bytes; do not expose it to browser code.
- `OPENAI_API_KEY`: optional server-side provider credential.
- `OPENAI_API_CALLS_ENABLED`: must remain `false` unless the owner explicitly authorizes paid API use.
- If the host key is absent, the endpoint returns `provider_host_not_configured` and no provider request occurs.
- If the provider is not explicitly enabled/configured, provider resolution fails closed and no request occurs.

## Status

Implementation: **PARTIAL PASS** — authenticated HTTP-to-Messenger path and fake-provider tests authored.  
CI: **PENDING** until a successful Actions run for the final PR commit is observed.  
Real provider inference: **NOT PROVEN**.  
Two independent provider identities: **NOT IMPLEMENTED**.  
Peer delivery via a deployed Long Poll server/device: **NOT PROVEN**.

No secret was generated or configured. No paid API call, deployment, service creation, device activation, merge, or publication was performed. No browser cookies or private ChatGPT sessions are accessed.
