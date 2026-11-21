# Mission 03 — AI MESSENGER — Round 02/10

Status: IMPLEMENTED / CI PENDING
Branch: `v2-saas-alpha`

## Objective

Add a local conversation directory and isolate message history by conversation, without inventing remote participants or implying that a local room is a live group chat.

## Implemented

- Added immutable `MessengerConversation` model.
- Every newly created local conversation receives a generated `LOCAL-<UUID>` identifier.
- Added title validation (required, maximum 60 characters) and positive timestamp validation.
- Added a conversation directory in `MessengerActivity`.
- Added creation and selection of local conversations.
- Persisted the local conversation directory separately from message records in app-private SharedPreferences.
- Messages are stored with their conversation ID and only the selected conversation's history is rendered.
- Clearing history now removes messages from the selected conversation only; other local conversation histories remain.
- The default initial item is `LOCAL-DEMO` / "Rascunho local".
- Added JVM tests for unique local IDs, local-only metadata and invalid inputs.

## Honest participant and room representation

There is no remote participant directory in this build. No AI_ID is shown as connected, no invitation is sent, and no group membership is fabricated. A local conversation title is a user-created label only. All conversations and messages are marked `LOCAL_ONLY` / `LOCAL_SANDBOX`.

The app does not yet support authenticated direct chats, server-managed group rooms, participant discovery, delivery status, online presence or synchronization across devices.

## Acceptance

- [x] Conversation directory visible in Messenger.
- [x] Create a local conversation with a distinct ID.
- [x] Switch between local conversations.
- [x] Store messages with their conversation ID.
- [x] Display only the selected conversation's messages.
- [x] Clear only the selected conversation's messages.
- [x] Unit tests added for conversation model.
- [ ] CI success for final commit.
- [ ] Physical Android device verification.

## Next

Round 03 should add a local participant/profile directory model and UI states that distinguish "registered in local demo" from "authenticated/connected". Remote discovery and identity verification remain blocked on a backend and provider authorization.
