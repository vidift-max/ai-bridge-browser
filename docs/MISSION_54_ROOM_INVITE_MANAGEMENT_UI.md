# Mission 54 — Room Invite Management UI

## Objective
Replace the one-shot browser prompt for room invitations with a room-scoped admin panel that uses the existing authenticated invite APIs.

## Ten work rounds
1. Audited the Rooms page invite flow and the server routes for list/create/revoke and join-request decisions.
2. Confirmed the backend requires the authenticated room administrator for listing, creating, and revoking invitations.
3. Confirmed invite secrets are returned only at creation; stored rows expose metadata, not the raw token.
4. Added a room-scoped invite management panel with explicit open/close behavior.
5. Added bounded expiry choices (1 hour, 24 hours, 7 days) and a maximum-use control bounded to the room capacity.
6. Replaced the prompt flow with the authenticated create endpoint and a one-time secret link display.
7. Added copy-to-clipboard with a manual selection fallback; token remains in the URL fragment.
8. Added invite listing with active/expired/exhausted/revoked status, usage, expiry, and authenticated revoke action.
9. Added regression tests for secure-context gating, secret handling, admin-only visibility, bounded settings, listing, and revocation.
10. Added CI and mission documentation; PR remains Draft with no merge or deployment.

## Security and scope
- Server authorization remains authoritative; UI visibility is not an access control.
- Raw invite token is shown only in the create response and link fragment; the list never renders token material.
- HTTPS is required outside localhost.
- The invitation remains a request for admission; it does not automatically provision or authenticate an AI identity.
- No external provider was connected; no physical phone was activated; no deployment was performed.
