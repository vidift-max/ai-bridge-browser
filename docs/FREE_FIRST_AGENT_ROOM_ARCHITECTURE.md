# Free-first agent room architecture decision (M310)

Date: 2026-11-27
Status: architecture decision; no cloud project provisioned.

## Product constraint
The browser's essential features must not require a subscription, credit card, paid API, paid server, or paid storage. The app must remain useful offline.

## Decision A — local-first is mandatory
- Browser tabs, logical agent roster, mission queue, room history, and checkpoints must have a local source of truth on the Android device.
- Use Android private app storage and SQLite for durable structured records; do not treat process memory or a remote service as the only copy.
- Export/import and recovery must be possible without a cloud account.
- Remote synchronization is an optional transport adapter, never a prerequisite to open the browser or use local missions.

## Decision B — Firebase Spark is the first remote-room candidate, not an approved dependency
Official Firebase documentation currently describes Spark as no-cost and says no payment method is needed. Realtime Database Spark quota is 100 simultaneous connections, 1 GB stored data, and 10 GB/month downloaded. When a Spark quota is exceeded, that product is shut off for the remainder of the month rather than automatically billing overage. Firebase also warns that linking a Cloud Billing account upgrades the project to Blaze; paid Google Cloud products such as Cloud Run and Cloud Functions are unavailable on Spark.
- This capacity is sufficient on paper for a small 20-agent room, but quota is shared at project level and not a performance guarantee.
- Use only default Realtime Database instance and Spark-eligible services if later approved.
- Do not enable billing, attach a payment method, deploy Cloud Functions, Cloud Run, paid hosting, or other paid Google Cloud products.
- Before implementation, verify the actual Firebase project plan and exact database quota in console. Do not assume the user's project is already configured.
- Database Security Rules and authenticated identities are mandatory; never ship an open read/write database rule.

## Decision C — no Render backend for the free-first product
The M309 Render plan requires paid compute plus a persistent disk (documented estimate US$7.25/month) and returned `need_payment_info`. It is excluded from the free-first architecture. Do not sync its Blueprint or provision resources.

## Logical agents vs provider sessions
- Roster ceiling: 20 logical identities, AI-01 through AI-20.
- Logical agents can have mission descriptions, state, report history, and queue entries without opening 20 WebViews or 20 provider accounts.
- Current provider-account scope remains AI-01 and AI-02 only.
- Initial scheduler limit: at most two active provider sessions; the other agents remain queued/offline until a later authorized phase.
- No API is presumed free. External model providers remain optional and their own costs/quotas must be disclosed.

## Shared room event contract (version 1)
Every event must include:
- schemaVersion
- eventId (unique, stable idempotency key)
- roomId
- sequence (server-assigned for remote events; local monotonic sequence for offline log)
- senderAiId
- visibility: ROOM or PRIVATE
- recipientAiId only for PRIVATE
- eventType: MESSAGE, MISSION_ASSIGNED, MISSION_CHECKPOINT, REPORT, STATUS, ACK
- createdAt
- payload with bounded length

Rules:
1. Validate authenticated sender identity against senderAiId.
2. A private event is visible only to sender, recipient, and explicitly authorized coordinator.
3. Ignore duplicate eventId; do not duplicate messages after reconnect.
4. Clients persist locally before attempting sync.
5. ACK only after durable local acceptance; remote ACK after remote write confirmation.
6. Use bounded page sizes and cursor-based replay; never load the full room history at once.
7. Reconnection replays after last confirmed sequence and reconciles eventId to prevent duplicates.
8. Agent membership does not imply permission to execute tools or write GitHub.

## Persistence and recovery contract
Local tables (implementation target):
- agents(ai_id PRIMARY KEY, display_name, specialty, status, updated_at)
- missions(mission_id PRIMARY KEY, ai_id, instruction, state, created_at, updated_at)
- room_events(event_id PRIMARY KEY, room_id, sequence, sender_ai_id, visibility, recipient_ai_id, event_type, payload, created_at, sync_state)
- checkpoints(mission_id, ai_id, round_number, state, report_ref, updated_at)

Local state is authoritative while offline. Sync conflicts must preserve both records and require deterministic reconciliation; never silently overwrite a newer mission checkpoint.

## Performance and safety
- Do not instantiate 20 WebViews simultaneously.
- Limit provider WebViews to the existing two-account test scope.
- Queue tasks; pause scheduling when app is backgrounded or memory pressure is detected.
- Message payloads and retained history are bounded and paginated.
- No background remote control, auto-submit, or external provider automation is enabled by this architecture decision.

## Acceptance gates
- Spark project verified with no billing account.
- Rules emulator tests deny unauthenticated, wrong-room, and private-message reads/writes.
- 20 logical roster records survive process restart and export/import.
- 20 logical agents can queue missions; no more than two provider sessions are active.
- Offline send/reconnect replay produces no duplicate event IDs.
- Physical tablet memory and battery tests pass before increasing concurrency.
