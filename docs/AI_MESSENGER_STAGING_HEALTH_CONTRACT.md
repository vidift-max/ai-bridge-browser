# Staging Health Contract

`GET /healthz`
- Purpose: process-level liveness.
- Success: HTTP 200.
- Must not expose credentials, filesystem paths, database contents, or participant data.

`GET /readyz`
- Purpose: configuration/readiness gate.
- Success: HTTP 200 only when required runtime configuration passes validation.
- Failure: HTTP 503 with a generic safe error.
- Must not expose which secret is missing.

Neither endpoint proves:
- public network reachability;
- durable hosted storage;
- external AI connectivity;
- physical Android connectivity.
