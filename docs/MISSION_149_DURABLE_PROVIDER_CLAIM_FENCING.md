# Mission 149 — Durable Provider Claim Fencing

## Ten-round scope

1. Revalidated M148 final PR and CI before starting this branch.
2. Created an isolated branch from the M148 final commit.
3. Audited the durable provider request ledger for abandoned PROCESSING claims.
4. Identified that a permanently PROCESSING row had no lease-based recovery path.
5. Added schema v13 with durable attempt generations and an index for processing-state inspection.
6. Added a bounded lease policy: a PROCESSING claim can be reclaimed only after its lease expires; FAILED claims can be retried.
7. Incremented the attempt generation whenever a new attempt takes ownership.
8. Fenced message completion and failure transitions by the attempt generation, so stale workers cannot complete or fail a newer attempt.
9. Added deterministic store tests for stale-attempt fencing and prevention of premature lease stealing, plus dedicated CI.
10. Opened a Draft PR without merge, deployment, paid provider calls, or device activity.

## Claim semantics

- A new request starts at generation 1.
- A matching PROCESSING request remains owned by its current generation until its lease expires (default 120 seconds).
- A matching FAILED request can be reclaimed immediately.
- Every reclaim increments `attempt_generation`.
- Completion and failure must present the generation returned by the successful claim.
- A stale generation cannot mark a newer attempt FAILED or persist its provider message.
- COMPLETED requests remain immutable and replay through the existing durable response path.

The lease is a recovery mechanism, not a guarantee that an external provider call has stopped. Fencing prevents a late worker from committing after a newer attempt has acquired the request.

## Evidence boundary

Tests exercise SQLite and fake provider-independent store operations. They do not prove live provider inference, deployment behavior, physical AI-to-AI communication, or operation of any Android device. No API key, paid provider call, deployment, private browser session access, or merge was performed.
