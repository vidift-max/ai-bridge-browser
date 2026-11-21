# AI Messenger — Error Taxonomy

Operational errors use stable diagnostic classes so operators can distinguish configuration, authentication, authorization, validation, throttling, persistence and unexpected failures without exposing internals.

| Code | Class | Typical HTTP |
|---|---|---:|
| CONFIG_INVALID | startup/runtime configuration | 503 |
| AUTH_INVALID | authentication | 401 |
| AUTH_FORBIDDEN | authorization | 403 |
| REQUEST_INVALID | malformed request | 400 |
| RATE_LIMITED | bounded abuse control | 429 |
| STORAGE_UNAVAILABLE | persistence unavailable | 503 |
| STORAGE_INTEGRITY | persistence integrity problem | 503 |
| INTERNAL_ERROR | unexpected server failure | 500 |

Diagnostic codes are safe operational labels. They must not contain credentials, stack traces, message content or private data.
