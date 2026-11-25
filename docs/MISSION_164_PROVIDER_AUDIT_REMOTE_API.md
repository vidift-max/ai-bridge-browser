# Mission 164 — Provider Audit Remote Service API & Authentication Contract

## Ten engineering rounds

1. Audited M163 PR #164 and exact-head CI run 45685196436; verified 68 passing tests on HEAD 401411728cd195e33e818701227347e5e148004a.
2. Created an isolated branch from the exact M163 HEAD.
3. Inspected the M162 transport-neutral anchor interface and M163 durable reference adapter.
4. Defined authenticated API operations for reading the latest anchor and appending a checkpoint.
5. Implemented an injected bearer-token authentication and principal-authorization contract.
6. Added strict JSON parsing, duplicate-key rejection, body-size limits, and exact request schema validation.
7. Added atomic sequence/chain conflict handling and idempotent retry for the exact current latest record.
8. Added per-principal rate limiting, explicit HTTP error mapping, and fail-closed storage outage behavior.
9. Added endpoint schema, Python 3.12 CI, and tests for authentication, authorization, malformed requests, limits, replay, conflicts, and outage.
10. Opened a Draft PR and validated the exact final commit through CI.

## API contract

- `GET /v1/audit-anchor/latest`: authenticated read of the current latest anchor record.
- `POST /v1/audit-anchor/checkpoints`: authenticated append request with JSON body:
  `{"expected_sequence": 0, "record": { ...anchor record... }}`.

The service calls an injected `authenticate_token(token)` function, which must return a stable principal ID or a falsey value. An `authorize_principal(principal)` callback must return exactly boolean `True`; if it is omitted, the service denies access by default. Tokens are not stored, logged, provisioned, or created by this module.

The append path validates the complete M162 record, uses the backend's atomic compare-and-append, and returns HTTP 409 for stale sequence or chain conflicts. A retry that exactly matches the current latest committed record returns HTTP 200 with `replayed: true`; it does not append a second row. An older retry after a newer record has been appended returns a conflict.

## Security controls

- Bearer credential is required for both endpoints.
- Authentication and authorization are injected. Authorization fails closed by default; production must supply an explicit policy callback.
- Strict UTF-8 JSON, duplicate-key rejection, non-finite JSON constant rejection, exact request keys, and bounded body size.
- Per-principal in-memory sliding-window rate limit.
- TLS belongs to the eventual HTTP transport/deployment wrapper; this module is a request/response contract and is not mounted in the application server.
- Storage errors fail closed with HTTP 503.

## Evidence and limitations

Tests use temporary local SQLite files and injected fake token validators. This proves service-contract behavior in CI, not a deployed HTTP listener, TLS termination, production identity provider, credential rotation, persistent distributed rate limiting, or remote service availability.

The service is intentionally not mounted into `server/http_server.py`. No external network service, domain, secret, credential, cloud account, deployment, paid API, device activation, or merge was performed. A real deployment must provide TLS, a secret manager, durable identity and authorization, persistent distributed rate limiting, monitoring, and an independently administered anchor backend.

The final hardening pass changed the default authorization policy to deny and added tests for missing or invalid authorization callbacks. This prevents a correctly authenticated identity from receiving access merely because the deployment forgot to configure authorization.
