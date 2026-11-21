# Authentication Guardrails

- Tokens are runtime secrets and must never enter Git.
- AI_ID identifies the authenticated principal but is not a password or token.
- One configured token maps to one configured AI_ID.
- Authentication failure is distinct from authorization failure.
- The current implementation is an opaque token lookup, not OAuth/OIDC.
- Token rotation, revocation, expiration and external IdP validation are not implemented.
- TLS must be provided by a trusted deployment layer before real credentials traverse a network.
- Android must remain disconnected until authenticated end-to-end verification exists.
