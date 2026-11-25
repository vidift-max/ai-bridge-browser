# Mission 158 — Repeated Crash Recovery & Recovery Contention

## Ten engineering rounds

1. Audited M157 PR #158 and its exact-head CI; confirmed M156 PR #157 and its concurrency test evidence.
2. Created an isolated branch from M157 HEAD `5a062a969a2045a6ba2f972e42579bf4f11d2f92`.
3. Reviewed M157's spawned-process helpers, durable claim state, and attempt-generation fencing.
4. Parameterized process crash/recovery workers to use controlled monotonic test timestamps.
5. Added repeated abrupt process exits across successive lease generations using the same persistent SQLite file.
6. Reopened the database after each exit and asserted PROCESSING state, generation, and timestamp durability.
7. Added final recovery after three simulated crashes and verified generation 4 acquisition.
8. Added a five-process recovery race after a crash; asserted exactly one generation-2 claimant and four observers.
9. Verified final durable state through a separately opened SQLite connection and bounded all process/queue waits.
10. Added dedicated Python 3.12 CI and this mission evidence record.

## Evidence boundary

Tests use Python's spawn multiprocessing context, independent OS processes, temporary local SQLite storage, and controlled timestamps. Abrupt exits are simulated with process termination after the claim method commits; this is not a hardware power-loss test, production filesystem durability certification, or multi-host deployment proof. No production code, provider secrets, paid inference, deployment, device activation, or merge is included.
