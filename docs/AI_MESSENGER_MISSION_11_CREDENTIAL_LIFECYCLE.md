# Mission 11 — Credential Lifecycle and Authenticated E2E

## Round 01/10 — Credential lifecycle boundary

This mission hardens the experimental authentication foundation before any Android remote connection.

### States
- ACTIVE: credential may authenticate its assigned AI_ID.
- REVOKED: credential is known but authentication must fail.
- UNKNOWN: credential is not registered and authentication must fail.
- EXPIRED: reserved for lifecycle metadata; expiration is not yet wired in this round.

### Rules
- AI_ID remains an identity/principal, not a credential.
- Plaintext credentials must remain runtime-only and must never be committed to GitHub.
- Revocation must be enforced server-side before protected Messenger operations.
- This is not OAuth/OIDC and does not prove a production identity provider.
- No deployment, Android activation, provider connection, or real AI-to-AI communication is claimed by this round.

## Evidence target
The next implementation rounds must prove active/revoked/unknown behavior with automated tests and then exercise an authenticated local HTTP path using ephemeral durable storage.
