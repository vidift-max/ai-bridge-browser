# Mission 12 — Session, Expiration and Rotation

## Scope
Build the next authentication layer without deployment or Android activation.

## Rules
- Credentials and sessions are distinct.
- Plaintext runtime credentials are never persisted by the session layer.
- Session state is runtime-only experimental state.
- ACTIVE, REVOKED, EXPIRED and ROTATED are explicit lifecycle outcomes.
- Rotation invalidates the previous credential/session lineage.
- No OAuth/OIDC, public TLS endpoint, physical Android test or external AI provider is claimed.

## Verification target
Prove lifecycle behavior in automated tests, then prove an authenticated local HTTP path using ephemeral SQLite before any future hosted connection.
