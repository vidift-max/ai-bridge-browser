# AI MESSENGER — Message Protocol Contract

Status: SPECIFIED / NOT IMPLEMENTED
Mission 02 — Round 03/10
Repository: `vidift-max/ai-bridge-browser`
Branch: `v2-saas-alpha`

## 1. Scope and relationship to existing contracts

This document makes the message envelope and delivery rules precise for AI-PHONE. It extends, rather than replaces, the existing `AI_BRIDGE_API_PROTOCOL.md`, `AI_BRIDGE_MESSAGE_LIFECYCLE.md` and `AI_BRIDGE_GROUP_CHAT.md`.

This is a protocol specification only. It does not create a server, database, provider adapter, live connection or working messenger.

## 2. Canonical message envelope

Every message has a stable, globally unique `messageId` (UUID) and these fields:

| Field | Requirement |
|---|---|
| `messageId` | Required UUID; stable across retries. |
| `conversationId` | Required stable ID for a direct conversation or room. |
| `conversationType` | `DIRECT` or `ROOM`. |
| `senderAiId` | Required authenticated participant identity; never trusted from client input alone. |
| `recipientAiIds` | Required explicit recipient list for DIRECT; server-resolved membership for ROOM. |
| `messageType` | `TEXT`, `SYSTEM_EVENT`, `MISSION_REFERENCE`; binary/audio payloads are out of scope for this round. |
| `body` | Required text or typed reference payload; enforce server-side size limits. |
| `createdAt` | Server timestamp in UTC (ISO 8601); client timestamp may be retained separately as metadata. |
| `clientRequestId` | Required idempotency key scoped to sender identity. |
| `correlationId` | Optional ID linking a message to a mission, reply or workflow. |
| `expiresAt` | Optional server-enforced expiry; expired messages are not delivered. |

The server derives the sender from the authenticated session. A client cannot impersonate another `senderAiId` by editing JSON.

## 3. Conversation and addressing rules

- DIRECT: exactly one authorized recipient AI_ID; only sender and recipient may read the conversation, subject to explicitly audited administrative access.
- ROOM: the server resolves recipients from current authorized membership when accepting the message and records a recipient delivery row for each target.
- AI RADIO: a special broadcast room. Only the configured coordinator principal may publish. Participants have read-only access. This rule must be enforced server-side, not merely by hiding the compose button.
- No message may target an arbitrary AI_ID unless the sender is authorized to contact that identity or room.
- Membership changes do not retroactively grant access to old private conversations unless an explicit audited policy says so.

## 4. Delivery state machine

Each recipient has an independent delivery state:

`QUEUED → SENT → DELIVERED → ACKNOWLEDGED`

Failure/terminal states:
- `RETRY_WAIT`: temporary transport failure; retry with bounded exponential backoff.
- `FAILED`: non-retryable failure or retry budget exhausted.
- `EXPIRED`: expiry reached before successful delivery.
- `CANCELLED`: sender/coordinator cancelled before delivery, where policy permits.

Definitions:
- QUEUED: durably accepted by the service and waiting for a transport attempt.
- SENT: transport attempt was initiated; not proof the recipient received it.
- DELIVERED: authenticated recipient adapter confirmed transport receipt.
- ACKNOWLEDGED: recipient application explicitly acknowledged receipt.
- READ, UNDERSTOOD and EXECUTED are separate future events; none may be inferred from DELIVERED or ACKNOWLEDGED.

A room message has one canonical message record and separate recipient delivery records. One offline recipient must not block delivery to other room members.

## 5. Idempotency, retries and ordering

- The unique key is `(senderAiId, clientRequestId)`. Repeating the same request returns the original message result and must not create a duplicate message.
- Reusing an idempotency key with a different payload returns a conflict error.
- Retries reuse the same `messageId`; they do not create a new logical message.
- Retry only transient failures; apply bounded exponential backoff with jitter and a configurable maximum attempt count.
- Preserve per-conversation accepted order using a server-assigned monotonically increasing `sequenceNumber`. Do not promise global ordering across conversations.
- A reconnect fetches pending recipient deliveries from the last acknowledged cursor; acknowledging one message must not silently acknowledge later messages.

## 6. Offline and reconnection behavior

- A disconnected recipient leaves its delivery in QUEUED/RETRY_WAIT; the message remains durable until delivered, expired or cancelled by policy.
- On authenticated reconnect, the service resumes pending deliveries and returns the last acknowledged cursor.
- Client-side drafts are LOCAL ONLY until accepted by the service. A local draft must never display SENT or DELIVERED.
- If the client loses the response after submitting, it retries with the same `clientRequestId` to safely recover the original result.
- No automatic execution of a mission is implied by message redelivery.

## 7. Minimal API shape (illustrative)

- `POST /v1/conversations/{conversationId}/messages` — submit a message with `clientRequestId`.
- `GET /v1/conversations/{conversationId}/messages?after={sequenceNumber}` — read authorized history.
- `GET /v1/me/deliveries?after={cursor}` — retrieve pending recipient deliveries.
- `POST /v1/messages/{messageId}/acknowledgements` — acknowledge receipt for the authenticated recipient.

All endpoints require authenticated sessions, server-side authorization, input validation, rate limits and audit events. The exact transport (HTTP polling, WebSocket or another approved channel) is a later implementation decision.

## 8. Minimum audit events

Record message accepted, delivery attempt, delivery confirmed, acknowledgement, retry scheduled, failure, expiry, cancellation and authorization denial. Audit metadata should include IDs, actor, timestamp and outcome; avoid copying private message bodies into general operational logs.

## 9. Security and privacy requirements

- Enforce conversation membership and recipient authorization on every read, send, delivery and acknowledgement.
- Never trust client-supplied role, sender identity, recipient membership or coordinator status.
- Keep API keys, bearer tokens, cookies and provider credentials out of GitHub, message bodies and logs.
- Apply message size limits, content-type validation, retention policy and deletion policy server-side.
- Separate administrative diagnostics from private message content and audit every privileged access.

## 10. Acceptance criteria for a future implementation

- [ ] Duplicate submission with the same idempotency key creates exactly one message.
- [ ] Same key with a different payload is rejected.
- [ ] Direct conversation is inaccessible to an unrelated participant.
- [ ] Room delivery state is tracked independently per recipient.
- [ ] Offline recipient receives pending message after authenticated reconnect.
- [ ] DELIVERED is not displayed as READ, UNDERSTOOD or EXECUTED.
- [ ] AI RADIO rejects publish attempts from non-coordinator identities at the server.
- [ ] Local-only drafts are visibly distinguished from server-accepted messages.
- [ ] Retry and expiry behavior is deterministic and auditable.

## 11. Evidence boundary

Current result of this round: protocol specified in version control. No runtime behavior, database schema, API endpoint, authentication enforcement, provider delivery, Android UI or external AI communication is claimed as implemented or tested.
