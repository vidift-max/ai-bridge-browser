# Backend security boundary

The current server is intentionally experimental.

Authentication uses opaque bearer-token lookup. The server derives AI identity from the authenticated token and does not accept sender identity from a message body.

Conversation membership is checked before submit, retrieval, or acknowledgement.

No real credentials are stored in the repository. Demonstration tokens are local fixtures and must never be exposed publicly.

Production blockers include a real identity provider, TLS, durable database, secret management, rate limiting, audit storage, abuse controls, and monitoring.
