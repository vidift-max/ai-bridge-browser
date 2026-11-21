# Hosted Staging Checklist — AI Messenger

## Configuration
- [x] Bearer credentials are runtime-only.
- [x] AI identities are runtime-configured.
- [x] SQLite path is explicit.
- [x] Request timeout is bounded.
- [x] Retry count is bounded.
- [x] Invalid configuration fails closed at readiness.

## Transport
- [x] Request body content type and length are validated.
- [x] Cursor and limit parsing is deterministic.
- [x] Message/idempotency persistence is transactional.
- [x] Authenticated principal generation is enforced.
- [x] Rate limiting exists at the experimental HTTP boundary.
- [x] Health/readiness responses do not expose bearer credentials.

## Hosting
- [x] render.yaml is present as preparation only.
- [x] The start command binds to the hosting port.
- [x] Health check path is /healthz.
- [ ] Render deployment — not authorized/performed.
- [ ] Production persistent storage — not provisioned.
- [ ] TLS/public endpoint — not activated.
- [ ] OAuth/OIDC — not integrated.
- [ ] External AI provider — not connected.
- [ ] Physical Android activation — not performed.

## Evidence rule

A green CI workflow proves repository automation for its commit. It does not prove a public deployment, a reachable internet service, or physical-device execution.
