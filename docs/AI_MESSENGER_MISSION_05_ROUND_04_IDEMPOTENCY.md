# Mission 05 — Round 04 — Idempotency

The remote contract uses a client request idempotency key together with the authenticated sender identity.

Rules:
- retrying the same logical submission reuses the same idempotency key;
- the same key with the same payload may return the existing server result;
- the same key with a different payload is a conflict;
- a local operation ID is not a server idempotency key;
- messageId and idempotency key have different purposes;
- the server, not the Android client, is authoritative for acceptance.

No server-side idempotency store is implemented in this round.
