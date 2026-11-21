# AI MESSENGER — Offline Queue, Reconnection and Recovery

Status: SPECIFIED / NOT IMPLEMENTED
Mission 02 — Round 05/10
Repository: `vidift-max/ai-bridge-browser`
Branch: `v2-saas-alpha`

## 1. Purpose and evidence boundary

Define reliable message storage and recovery when an AI-PHONE loses internet connectivity and later reconnects over Wi-Fi or another internet connection.

This is a design contract only. It does not implement a server, database, background worker, WebSocket, Android offline store or provider adapter. No live message delivery is claimed.

The messenger is internet-based and does not require a SIM card or telephone number. Wi-Fi is one supported network transport; the protocol is independent of the access network.

## 2. Two different kinds of pending content

The client must distinguish:

- LOCAL_DRAFT: text created on a device but not yet accepted by the service. It exists only in local application storage and is not visible to recipients.
- SERVER_QUEUED: a message durably accepted by the service, assigned a stable `messageId` and recipient delivery records, but not yet acknowledged by the target application.

A draft must never be displayed as SENT, DELIVERED or ACKNOWLEDGED. When offline, the user may keep editing a local draft. The client may submit it after connectivity returns, using its original `clientRequestId`.

The server acceptance response is the boundary between local draft and server-owned message. If the response is lost, the client must retry with the same idempotency key rather than create a new logical message.

## 3. Durable server-side storage

Accepted messages and their delivery state must be stored durably before the service reports successful acceptance.

Minimum logical records:

- `messages`: canonical message envelope, sender, conversation, sequence number, server creation time, expiry and payload reference.
- `message_deliveries`: one row per recipient, with recipient AI_ID, state, attempt count, next attempt time, delivery/acknowledgement timestamps and last error code.
- `idempotency_records`: sender AI_ID, clientRequestId, canonical payload hash and resulting message ID.
- `conversation_cursors`: recipient/conversation progress or an equivalent durable cursor model.
- `delivery_attempts`: auditable attempt metadata, outcome and timestamps.

The database must enforce uniqueness for `(senderAiId, clientRequestId)` and for the relevant message-recipient pair. A browser tab, Android process memory or local cache is never the authoritative queue.

The service must commit the message, idempotency record and recipient delivery rows atomically. If the transaction fails, no success response is returned and no partial message is exposed as accepted.

## 4. Submission and idempotency recovery

1. The client creates a `clientRequestId` before the first submission attempt.
2. The authenticated service derives `senderAiId` from the verified session.
3. The service validates conversation membership, recipients, payload and expiry.
4. In one transaction, it creates the canonical message, delivery rows and idempotency record.
5. The service returns the original `messageId`, server sequence and acceptance state.
6. If the client times out or loses the response, it retries with the same `clientRequestId`.
7. The service returns the original result for an identical payload.
8. Reuse of the same key with a different canonical payload returns a conflict and creates no second message.

Retries must preserve the original `messageId`; transport retries are not new messages.

## 5. Recipient-specific queue behavior

Each recipient has an independent delivery record. A disconnected participant must not block other room members from receiving the same room message.

Suggested states:

`QUEUED → RETRY_WAIT → SENT → DELIVERED → ACKNOWLEDGED`

Terminal or exceptional states:

- `FAILED`: permanent error or retry budget exhausted.
- `EXPIRED`: server expiry reached before acknowledgement.
- `CANCELLED`: valid cancellation occurred before delivery under the applicable policy.

State meanings remain strict:

- QUEUED: durably stored and waiting for an attempt.
- RETRY_WAIT: transient failure; a future attempt is scheduled.
- SENT: an attempt was initiated; not proof of receipt.
- DELIVERED: authenticated recipient transport/adapter confirmed receipt.
- ACKNOWLEDGED: recipient application explicitly acknowledged receipt.
- READ, UNDERSTOOD and EXECUTED are separate future events and must never be inferred from delivery or acknowledgement.

One recipient's FAILED or offline state must not rewrite another recipient's delivery state.

## 6. Reconnection and cursor recovery

After internet connectivity returns, the client must:

1. establish or refresh an authenticated session;
2. verify that its AI_ID is still ACTIVE and its grants remain valid;
3. submit its last durably acknowledged cursor (or per-conversation cursor);
4. request only deliveries authorized for that authenticated recipient;
5. receive pending items in stable server order, with pagination;
6. process each item idempotently and persist it locally before acknowledging it;
7. acknowledge only the specific message/delivery successfully persisted by the recipient application;
8. continue from the returned cursor until caught up, then resume live delivery or periodic polling.

A cursor is a recovery position, not a permission token. The server must independently re-check identity, membership and authorization on every reconnect and fetch.

Acknowledging one message must not implicitly acknowledge later messages. A gap, expired cursor or lost local state must trigger a safe resynchronization from a server-defined checkpoint without exposing unauthorized history.

## 7. Duplicate handling and crash recovery

- The recipient client stores a unique processed-delivery key, such as `(messageId, recipientAiId)`.
- Receiving the same delivery more than once must not create duplicate visible messages or repeat an application side effect.
- The client acknowledges only after the message is durably recorded in its local message store.
- If the app crashes after local persistence but before acknowledgement, redelivery is safe because the unique key detects the existing item; the client can acknowledge it again.
- If the app crashes before local persistence, the server redelivers it.
- Mission execution is never triggered solely by message redelivery. Mission commands require a separate authorization and execution idempotency contract.
- Database workers must claim deliveries atomically (for example, lease/claim with expiry) so concurrent workers do not independently process the same active attempt. Any duplicate transport attempt must still be harmless through recipient idempotency.

## 8. Retry policy and operational limits

Only transient errors should be retried automatically, such as temporary network failures, timeouts, rate limits or provider unavailability.

Use bounded exponential backoff with jitter, a configurable maximum attempt count, and a maximum message age/expiry. Respect provider retry hints such as Retry-After when available. Permanent authorization, invalid-recipient or malformed-payload errors must not loop indefinitely.

The service must define configurable limits for message size, queue depth per recipient, delivery concurrency, retry budget, retention and maximum expiry. When a limit is reached, return an explicit error or move the delivery to a reviewable FAILED/dead-letter state; never silently discard accepted messages.

A dead-letter record retains safe diagnostic metadata and a reason code, not credentials or unnecessary private message content. Requeueing requires an authorized operation and an audit event.

## 9. Expiry, cancellation and retention

- The server is authoritative for `expiresAt`; clients cannot extend it by changing local clocks.
- Expired messages transition to EXPIRED and are excluded from future delivery.
- Cancellation is allowed only while policy permits and must be serialized against concurrent delivery attempts.
- Retention and deletion rules must be documented separately for message bodies, delivery metadata and audit records.
- Deletion must not leave a delivery worker able to send a deleted/cancelled message.
- A message that has already been acknowledged cannot be represented as never delivered; any recall feature would be a separate user-visible event.

## 10. Wi-Fi, network changes and live delivery

The same authenticated protocol works over Wi-Fi, mobile data or another internet connection. Switching networks may interrupt a connection; the client reconnects and resumes from its acknowledged cursor.

WebSocket or another persistent transport may provide prompt live updates, while HTTPS polling can serve as a simpler fallback. Neither transport replaces durable server storage. If a socket disconnects, pending messages remain in the server queue.

The AI-PHONE must not claim an AI is ONLINE merely because Wi-Fi is connected. Presence requires a valid authenticated session and a recent heartbeat/adapter signal. A message can be queued even when the recipient provider is unavailable.

Voice calls are not part of this text-queue contract. Future VoIP/WebRTC signaling may use the same identity and authorization model, but live audio cannot be treated as an offline message; missed-call notifications and optional voicemail/audio messages require separate specifications and explicit provider/audio support.

## 11. Security and privacy

- Authenticate every submission, reconnect, fetch, delivery and acknowledgement.
- Derive sender and recipient authority from trusted server state, never from client-supplied role fields.
- Re-check ACTIVE status, conversation membership and recipient grants when recovering pending messages.
- A revoked or suspended identity cannot fetch or acknowledge deliveries using an old session.
- Keep provider credentials, API keys, bearer tokens, cookies and session secrets out of GitHub, message bodies and logs.
- Encrypt network traffic; protect stored content and backups according to the service's security design.
- Avoid logging message bodies in general operational logs.
- Audit acceptance, retry, delivery, acknowledgement, expiry, cancellation, dead-letter and authorization-denial events.

## 12. Minimum implementation acceptance tests

- [ ] Accepted message survives service process restart before delivery.
- [ ] Failed database transaction never returns successful acceptance.
- [ ] Same sender and clientRequestId with same payload returns one original message.
- [ ] Same idempotency key with a different payload returns conflict.
- [ ] Offline recipient receives its pending delivery after authenticated reconnect.
- [ ] Room recipients progress independently.
- [ ] Cursor pagination neither skips unacknowledged messages nor acknowledges later messages.
- [ ] Crash before local persistence causes safe redelivery.
- [ ] Crash after local persistence but before acknowledgement causes no duplicate visible item or side effect.
- [ ] Concurrent workers cannot corrupt delivery state or lose a queued item.
- [ ] Expired/cancelled deliveries are not sent.
- [ ] Revoked identity cannot recover pending messages.
- [ ] Queue limits and retry exhaustion produce explicit, auditable outcomes.
- [ ] Wi-Fi loss and network switching recover without creating duplicate logical messages.
- [ ] No delivery state is mislabeled READ, UNDERSTOOD or EXECUTED.

## 13. Round result

This round specifies the durable offline queue, recipient-specific delivery records, idempotent submission, reconnect cursors, crash recovery, retry limits, expiry and security requirements.

It does not implement or test a running messenger, database, server, Android storage, WebSocket, Wi-Fi delivery, voice calling or external AI integration. Those require subsequent implementation and runtime evidence.
