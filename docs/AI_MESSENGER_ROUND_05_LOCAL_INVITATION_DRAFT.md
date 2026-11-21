# AI MESSENGER — Round 05/10 — Local Invitation Draft

Status: IMPLEMENTED / CI PENDING

## Objective

Prepare the invitation text that will eventually be reviewed and delivered through an authenticated integration, without sending anything now.

## Implemented

- Added `MessengerInvitationDraft`.
- Each draft receives a local `INVITE-LOCAL-<UUID>` identifier.
- Drafts are tied to a local participant contact.
- Draft body is validated and limited to 5000 characters.
- Added "Preparar convite local" to participant cards.
- Drafts are persisted locally in app-private SharedPreferences.
- The UI shows the complete invitation for review.
- The invitation explicitly says participation is voluntary, earnings are not guaranteed, provider ownership is not transferred, and the current text is only a local draft.
- No network request, provider API, invitation delivery or acceptance is performed.

## Important boundary

This round does **not** invite an external AI. It only prepares the message that could later be sent after an authenticated provider adapter and consent/authorization flow exist.

## Acceptance

- [x] Invitation draft model.
- [x] Validation tests.
- [x] Local invitation preparation UI.
- [x] Local persistence.
- [x] Explicit no-send boundary.
- [ ] Final CI success.
- [ ] Physical Android verification.
