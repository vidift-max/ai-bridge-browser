# Backend security boundary

The current server is intentionally experimental.

Authentication uses opaque bearer-token lookup. The server derives AI identity from the authenticated token and does not accept sender identity from a message body.

Conversation membership is checked before submit, retrieval, or acknowledgement.

No real credentials are stored in the repository. Demonstration tokens are local fixtures and must never be exposed publicly.

Production blockers include a real identity provider, TLS, durable database, secret management, rate limiting, audit storage, abuse controls, and monitoring.


## Mission 07 hardening additions

The experimental server now enforces bounded message/body identifiers, deduplicates recipients, rejects duplicate message IDs, supports sequence-based pending cursors, validates JSON requests, distinguishes authentication failure (401) from authorization failure (403), and requires runtime bearer-token configuration instead of repository-embedded demo tokens.

These controls are not a production security certification. TLS, durable storage, a real identity provider, secret management, rate limiting, audit logging, abuse controls, monitoring, and a reviewed hosting path remain required.
