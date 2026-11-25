# Mission 156 — Provider Lease Concurrency & Recovery Stress Tests

## Ten rounds

1. Audited M155 PR #156 and verified its exact-head CI before making changes.
2. Created an isolated M156 branch from the audited M155 HEAD.
3. Inspected SQLite transaction boundaries for claim, renew, fail, reclaim, and completion operations across independent connections.
4. Added an eight-connection simultaneous initial-claim stress test, repeated across twelve request IDs; exactly one contender must acquire each generation.
5. Added an eight-connection expired-lease reclaim stress test, repeated across twelve request IDs; exactly one contender may advance the generation.
6. Added a synchronized renewal-versus-reclaim race test and asserted both possible serializations preserve a single valid owner.
7. Added a completion-versus-reclaim race test proving an old attempt cannot complete after a newer generation takes ownership.
8. Added a failure-versus-reclaim race test proving a stale failure cannot change the reclaimed generation.
9. Added a duplicate-completion race across two independent connections and asserted both callers observe the same durable completed result.
10. Added a dedicated Python 3.12 CI workflow and this evidence-bound mission record.

## Invariants under stress

- One durable owner per request generation.
- Only one contender can reclaim a given expired generation.
- Renewal and reclaim serialize to one valid outcome; no dual ownership.
- Completion/failure from a stale generation cannot overwrite a newer generation.
- Duplicate completion returns the durable first result rather than creating a second result.

## Evidence boundary

The tests use local SQLite files, independent database connections, barriers, and concurrent Python threads. They validate database-level serialization and fencing in this test environment; they do not establish multi-host production behavior, synchronized distributed clocks, live provider inference, paid API use, deployment, physical device activation, or real AI-to-AI communication. No merge or deployment was performed.
