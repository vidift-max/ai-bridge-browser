# Mission 26 — Public Guest Intake & Approval Boundary

Status: implementation in progress; no merge or deployment is authorized.

## Objective
Allow a person or external AI operator using an ordinary browser to submit a room invitation without installing the native AI Bridge app or presenting a pre-provisioned AI bearer token. The request is an untrusted guest application, not an authenticated AI session.

## Security boundary
- The invite secret is a high-entropy, one-time-visible bearer secret; only its SHA-256 digest is persisted.
- Public intake accepts only invite secret, bounded display name, and an allowlisted provider claim. Provider claims are unverified labels, never proof of model/provider identity.
- A successful submission creates a pending guest application only. It does not create an authenticated principal, issue a session, join the room, send messages, start calls, or execute tools.
- Room administrators must explicitly approve or reject. Approval records intent only and remains pending credential provisioning; no access is granted by approval alone.
- Public responses do not reveal room membership, administrator identities, or whether a specific invite ID exists beyond generic unavailable errors.
- Rate limiting, payload bounds, idempotency, expiry, revocation, and audit metadata are required.
- No external provider API, browser automation, model invocation, paid service, or deployment is part of this mission.

## Acceptance
1. A guest can submit an invite from a standard web browser without a native app or existing AI bearer token.
2. The guest application remains isolated from room membership and messaging.
3. Admin-only review and decision operations are authenticated and room-scoped.
4. Invite validity, use limits, expiry, and revocation are enforced atomically.
5. Repeated submissions do not create duplicate pending applications.
6. Provider claims remain explicitly unverified.
7. Tests cover malformed input, abuse limits, replay, races, authorization, restart persistence, and no-access-before-provisioning.

## Non-goals
This mission does not authenticate ChatGPT/Gemini/Claude/Kimi, provision a usable AI identity credential, or prove that an external model can automatically open or operate a browser link. Those require separate provider-authorized integrations and explicit approval.

## Implemented in this branch
- Version 8 SQLite migration for pending guest applications.
- Strict public payload validation and provider-claim allowlist.
- Atomic invite-use consumption and duplicate application handling.
- Public `POST /v1/guest-applications` without an AI bearer credential.
- Authenticated room-admin review at `GET /v1/conversations/{conversationId}/guest-applications` and `POST /v1/conversations/{conversationId}/guest-applications/{applicationId}`.
- Guest invite page now submits a browser-only application without requiring native installation or a pre-provisioned AI token.
- Unit and HTTP tests cover validation, idempotency, authorization, and access isolation.

## Important limitations
- The provider claim is not provider authentication.
- `APPROVED_AWAITING_PROVISIONING` is deliberately not a usable session and does not add a room member.
- The existing invite status endpoint and current invitation token format remain unchanged.
- No physical Android/desktop browser test, external provider handshake, deployment, merge, or real guest conversation is claimed.
- Before production, the implementation still needs independent review of privacy/retention policy, abuse controls under distributed load, and an explicit credential-provisioning workflow.
