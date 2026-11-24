# Mission 13 — AI Session Adapter & Browser Tab Integration

## Objective
Define a safe host-side contract for registering browser sessions and provider adapters, with explicit consent, exact HTTPS origin allowlists, authentication confirmation, minimum status reads, and authorization-gated message sending.

## Ten rounds
1. Audited Mission 12 control-plane and current Rooms UI; confirmed there is no production connector to external AI browser tabs.
2. Created an isolated branch from Mission 12 without merging its PR.
3. Defined a provider adapter contract with explicit capabilities: connect, readStatus, sendMessage, and requestReconnect.
4. Added exact HTTPS origin allowlists; rejects non-HTTPS, credential-bearing, path/query/hash URLs, and unlisted origins.
5. Added explicit user-consent requirement before registering a tab session.
6. Added a deliberate connect operation; a tab is never auto-connected, and CONNECTED requires adapter authentication confirmation.
7. Added minimal status reads that require CONNECTED and expose only a state and observation timestamp.
8. Added message sending with a 4,000-character bound, explicit grant authorization callback, session binding, and capability checks.
9. Added lifecycle cleanup and audit events; no provider credentials, message bodies, or adapter secrets are persisted or emitted.
10. Added ten deterministic tests and a dedicated CI workflow; documented integration boundaries and limitations.

## Integration boundary
This registry is a host-side adapter contract, not a browser extension, content script, provider API client, or remote-control deployment. It does not inspect arbitrary tabs, inject scripts, scrape provider pages, automate login, defeat CAPTCHA/2FA, or bypass provider restrictions. A real adapter must be separately implemented, reviewed, authorized by the user, and connected by a trusted host.

## State semantics
- REGISTERED: user consent and origin policy accepted; no connection claim.
- CONNECTING: adapter connection attempt in progress.
- CONNECTED: adapter explicitly confirmed authenticated session.
- BLOCKED: adapter did not confirm authentication.
- CLOSED: session removed.

## Limits
- No external ChatGPT/Gemini/Claude account was accessed.
- No real browser tab, provider session, or remote message was exercised.
- No credentials are stored; authorization callback must verify a real short-lived grant at a trusted boundary.
- No paid services, merge, or deployment.
- This work does not claim a provider integration is complete.

## Validation
Run `node --test web/ai-session-adapter.test.mjs`. Tests use a fake adapter and verify local policy behavior only.
