# Mission 10 — Authentication and Session Foundation

## Scope
Create a server-side authentication/session boundary for AI-PHONE identities without claiming an external identity provider.

## Rules
- Runtime credentials only; never commit real tokens.
- AI_ID is the authenticated principal, not a credential.
- A valid credential maps to exactly one AI_ID.
- Invalid/missing credentials return authentication failure.
- Authenticated but unauthorized access remains distinct.
- No provider OAuth/OIDC implementation in this mission.
- No Android activation or deployment.

## Exit gate
Automated tests must prove credential-to-principal mapping and protected Messenger routes.