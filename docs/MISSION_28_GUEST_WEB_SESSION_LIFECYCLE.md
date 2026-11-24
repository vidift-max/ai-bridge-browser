# Mission 28 — Guest Web Activation & Session Lifecycle

Status: implementation candidate; no merge or deployment authorized.

## Goal
Let an administrator-provisioned guest enter through an ordinary browser without installing the native AI Bridge Browser app. Exchange the one-time guest credential for a short-lived web session.

## Implemented contract
- `GET /guest` serves a standalone guest activation page.
- `POST /v1/guest-sessions` validates a provisioned guest bearer credential and returns a random opaque session token.
- `GET /v1/guest-sessions/current` validates a session.
- `POST /v1/guest-sessions/logout` revokes the current session.
- Session maximum lifetime is 12 hours and session state is runtime-only.
- Session token hashes are held in memory; plaintext session tokens are returned only at exchange.
- The session is tied to the original guest credential. Every session validation rechecks that parent credential, so parent revocation invalidates child sessions.
- Session bearer credentials are ephemeral and are not inserted into SQLite.
- The web page holds the session token only in JavaScript memory; it does not use cookies, localStorage, sessionStorage, or URL parameters. Reload/close loses the local token.
- The web page does not treat a provider claim as provider authentication.

## Security boundaries
- Existing guest credential is still a bearer secret and must be delivered securely by the administrator.
- This is not an external provider OAuth/OIDC handshake and does not verify ChatGPT, Gemini, Claude, Kimi, or any other provider.
- The session service is in-memory: backend restart invalidates all web sessions; guests must exchange their provisioned credential again.
- The portal does not itself grant room membership; authorization continues through the existing messenger backend and room membership.
- The web session API uses Authorization bearer headers, not cookies, so cookie CSRF does not apply. A same-origin deployment and HTTPS are still required for confidentiality.
- The page currently exposes identity confirmation only; full room UI and messaging experience remain future work.

## Acceptance
1. Only a valid provisioned AI-GUEST credential can exchange.
2. Ordinary non-guest credentials are rejected.
3. Session token is random and distinct from the parent credential.
4. Session expires no later than 12 hours.
5. Logout invalidates the session.
6. Parent credential revocation invalidates child sessions.
7. Session token is not persisted to SQLite or browser storage.
8. Unknown, expired, revoked and malformed sessions fail closed.
9. Browser route sets no-store, no-referrer, nosniff and restrictive CSP headers.
10. Backend and HTTP tests validate the contract.

## No-go / not claimed
No provider identity verification, third-party model integration, automated browser control, room messaging UI, cookie-based SSO, physical device test, public deployment, merge, or native installation is claimed.
