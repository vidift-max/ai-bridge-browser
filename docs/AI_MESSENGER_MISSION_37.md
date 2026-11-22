# Mission 37 — Private conversations and 20-participant rooms

Branch: `v2-saas-alpha`

## Delivered

1. Added a server-side maximum of 20 members per conversation.
2. Added authenticated conversation creation in `MessengerBackend.create_conversation`.
3. Added `PRIVATE` conversations with exactly two provisioned participants.
4. Added `GROUP` conversations with 2–20 provisioned participants.
5. Required the creator to be a member of the conversation.
6. Rejected duplicate member IDs, unknown/unprovisioned AI identities, invalid types, malformed IDs, and conversation ID collisions.
7. Persisted new conversation membership through the existing SQLite messenger store.
8. Added authenticated `POST /v1/conversations` with audit event `CONVERSATION_CREATED`.
9. Added backend and live HTTP tests for membership boundaries, authorization, message delivery and persistence.
10. Documented the API and its operational limits.

## API example

`POST /v1/conversations` with Bearer authentication and JSON body:

```json
{
  "conversationId": "team-alpha",
  "kind": "GROUP",
  "memberAiIds": ["AI-ALPHA", "AI-BRAVO"]
}
```

A successful creation returns HTTP 201.

## Important limits

The server can create a room for up to twenty identities only when those identities already have server-provisioned credentials. This does not onboard arbitrary external AI providers. The Android AI Messenger screen is still local-only and has not yet been connected to the conversation and message APIs. No WebSocket/push presence, real voice calls, WebRTC, production deployment, or physical-device test is claimed.

## Verification

The Messenger Backend Test workflow passed on intermediate commits during implementation. Final verification must use the final mission HEAD after all changes; Android Build is tracked separately and does not test the server's live network behavior.
