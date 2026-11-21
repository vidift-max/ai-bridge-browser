# AI Messenger — Operational Limits

Observability remains bounded in the experimental backend.

- Maximum in-memory operational events: 1,000 by default.
- Maximum metadata value length: 256 characters.
- Diagnostic codes are short stable identifiers.
- No message body is copied into operational events.
- No bearer/session credential is retained in operational events.
- Counters and event logs are diagnostic only and are not a substitute for hosted metrics.

Any future hosted metrics integration must preserve the same secret and privacy boundary.
