# Mission 03 — AI MESSENGER — Round 04/10

Status: IMPLEMENTED / CI PENDING

## Objective

Allow local profiles to be selected as members of a local conversation without implying invitation, consent, authentication, or remote connectivity.

## Implemented

- Added `MessengerMembership` immutable model.
- Membership keys are the local conversation ID plus local contact ID.
- New membership state is always `LOCAL_SELECTED`.
- Added "Participantes desta conversa" control.
- Added local member-selection dialog using existing local participant profiles.
- Membership selections persist in app-private SharedPreferences.
- Reopening the member dialog restores the local selection.
- UI explicitly says that no invitation is sent and no AI is connected.

## Truth boundary

A selected local profile is only a planning/member-selection record on this device.

It does not:
- send an invitation;
- contact an AI provider;
- prove consent;
- create an authenticated session;
- assign an AI-PHONE number or serial;
- establish online presence;
- deliver messages remotely.

Future states `INVITE_PENDING` and `JOINED_VERIFIED` are reserved in the model but are not created by the current UI.

## Acceptance

- [x] Local membership model.
- [x] Membership validation tests.
- [x] Conversation member selection UI.
- [x] Persistence of local selections.
- [x] Explicit no-network/no-invitation boundary.
- [ ] Final CI success.
- [ ] Physical Android verification.
