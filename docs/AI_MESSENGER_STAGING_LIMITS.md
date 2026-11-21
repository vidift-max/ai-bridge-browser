# Staging Operational Limits

Current bounded experimental limits:
- request timeout: 1–120 seconds;
- retry limit: 0–5;
- request body: maximum 10,000 bytes in the current HTTP boundary;
- rate limiting remains conservative and in-memory.

These limits reduce accidental resource consumption but are not a complete production capacity model. Load testing, distributed rate limiting, connection pooling, and production observability remain future work.
