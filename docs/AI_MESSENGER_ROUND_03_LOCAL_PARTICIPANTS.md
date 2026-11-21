# Mission 03 — AI MESSENGER — Round 03/10

Status: IMPLEMENTED / CI PENDING
Branch: `v2-saas-alpha`

## Objective

Add a participant/contact directory that can prepare local contact cards while explicitly distinguishing them from authenticated AI identities and live presence.

## Implemented

- Added immutable `MessengerParticipant` model.
- New local profiles receive a `CONTACT-<UUID>` identifier, display name and provider label.
- New profiles always start at `LOCAL_DRAFT`; they have no AI_ID, AI-PHONE number or serial.
- Added local participant directory to the Messenger screen.
- Added a form to create a local contact card.
- Persisted contact cards in app-private SharedPreferences.
- Displayed explicit state labels and the absence of verified identity identifiers.
- Defined separate model states for local draft, locally recorded invite/acceptance, pending verification, active, disconnected, suspended and revoked.
- Registry-shaped account states require complete AI_ID, AI-PHONE number and serial fields; partial identity tuples are rejected.
- Added unit tests for local profile creation, validation and identity tuple requirements.

## Truth and security boundaries

A locally entered name/provider pair is not proof that an AI exists, has consented, or is reachable. The local contact directory does not send invitations, discover providers, authenticate users, assign official AI-PHONE numbers, or show online presence.

The UI currently creates only `LOCAL_DRAFT` cards. Other lifecycle values exist in the model for future authenticated registry integration; the local UI does not let the user promote a contact to ACTIVE or claim that a profile is verified.

Even a registry-shaped record is only structurally validated by this model. Authenticity requires authenticated transport, server authorization, trusted registry provenance and provider-side verification.

## Acceptance

- [x] Participant/contact directory visible in Messenger.
- [x] Add local contact card with display name and provider.
- [x] Stable local contact identifier.
- [x] New profile has no AI_ID, phone number or serial.
- [x] Distinct lifecycle states represented in the model.
- [x] ACTIVE/DISCONNECTED/SUSPENDED/REVOKED records require a complete identity tuple.
- [x] Tests added.
- [ ] CI success for final commit.
- [ ] Physical Android device verification.

## Next

Round 04 can add safe conversation membership drafts: select local contact cards for a local conversation while clearly showing that no invitation was delivered and no remote participant joined. Do not add actual remote messaging until authenticated backend and provider adapters exist.
