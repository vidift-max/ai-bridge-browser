# Mission 05 — Round 07 — Server Storage Contract

The future server needs durable records for:

- messages keyed by messageId;
- idempotency records keyed by authenticated sender + client request key;
- conversation membership;
- delivery state per recipient;
- monotonically ordered conversation sequence;
- acknowledgement cursor;
- audit events.

Minimum delivery lifecycle:
QUEUED -> SENT -> DELIVERED -> ACKNOWLEDGED

Failure states remain distinct:
RETRY_WAIT, FAILED, EXPIRED, CANCELLED.

The Android local SharedPreferences store is not a substitute for this server store. No remote database or queue is created in this round.
