# Staging Runtime Inventory

Required secrets/configuration:
- MESSENGER_TOKEN_AI_A — bearer credential; secret.
- MESSENGER_TOKEN_AI_B — bearer credential; secret.
- MESSENGER_AI_ID_A — authenticated AI identity; non-secret identifier.
- MESSENGER_AI_ID_B — authenticated AI identity; non-secret identifier.

Optional bounded configuration:
- MESSENGER_DB_PATH — SQLite path; default is repository-local experimental path.
- MESSENGER_REQUEST_TIMEOUT_SECONDS — bounded request timeout.
- MESSENGER_RETRY_LIMIT — bounded retry count.

Rules:
1. Secrets are runtime-only and never committed.
2. Readiness must fail closed when required configuration is missing or invalid.
3. Identity values are not credentials and must not be treated as bearer secrets.
4. A staging configuration is not evidence of a deployed service.
