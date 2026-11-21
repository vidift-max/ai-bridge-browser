# AI MESSENGER — Mission 09: Durable Storage Foundation

## Scope
Replace the experimental backend's process-only message state with a small SQLite persistence layer while preserving the existing transport contract.

## Guardrails
- No deployment.
- No Android remote activation.
- No real credentials in GitHub.
- SQLite is a local/hosted-runtime persistence mechanism, not proof of production readiness.
- Authentication remains the existing opaque runtime-token boundary; provider/IdP integration is not implemented in this mission.
- Schema migrations must be explicit and testable.

## Target
Persist conversations, messages, idempotency keys and acknowledgements so a process restart can recover message state.

## Exit evidence
Backend unit tests must cover persistence and restart recovery. HTTP contract tests remain structural unless an authenticated end-to-end runtime is explicitly executed.
