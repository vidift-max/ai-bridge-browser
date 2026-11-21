# Mission 05 — Round 08 — First Remote API Contract

Illustrative authenticated endpoints:

POST /v1/messages
GET /v1/conversations/{conversationId}/messages?after={cursor}
POST /v1/messages/{messageId}/ack

Requirements:
- authenticated session on every request;
- sender AI identity derived server-side;
- conversation membership checked server-side;
- client request idempotency key required for submission;
- server timestamp and sequence assigned by server;
- response explicitly states acceptance or rejection;
- no response may claim delivery to a recipient unless the server has evidence for that state.

This is an API contract only. No endpoint is live.
