# Mission 161 — Provider Audit External Checkpoint & Independent Integrity Anchor

## Ten engineering rounds

1. Audited M160 PR #161 and exact-head CI; confirmed it remains Draft/open/unmerged and run 45682330302 passed 37 tests on the exact HEAD.
2. Created isolated branch from M160 HEAD `78b7029da165a74e026ac0f39654ead03a8de04c`.
3. Inspected the v15 audit chain, its store connection boundary, and its existing integrity verifier.
4. Designed a separate signed checkpoint document containing schema version, anchored audit_id, event_hash, creation timestamp, and HMAC-SHA256 signature.
5. Implemented strict 32-byte-minimum signing-key validation; key material is never written to SQLite or checkpoint JSON.
6. Implemented atomic checkpoint file replacement with restricted 0600 permissions, file fsync, and best-effort directory fsync.
7. Implemented verification of checkpoint signature, full current chain, anchored event existence/hash, and database rollback behind the checkpoint.
8. Added restart, tail deletion, database rollback, signature tampering, wrong key, tampered-chain fail-closed, same-file rejection, permissions, and short-key tests.
9. Added Python 3.12 CI combining checkpoint tests with chain, audit lifecycle, request-store, and multiprocess recovery regressions.
10. Added this mission report and opened a Draft PR without merge or deployment.

## Operating model

The checkpoint file must be placed on storage independent from the SQLite database (for example, a separately controlled volume or object store), and the HMAC key must be supplied from a separate secret store or operator-managed secret. The implementation rejects using the exact same filesystem path as the database, but cannot prove that two different paths reside on different physical media or administrative trust domains.

Checkpoint creation first verifies the entire chain, then captures the current head under a SQLite read transaction, signs the canonical JSON payload with HMAC-SHA256, and atomically replaces the checkpoint file. Verification checks the signature, validates the full local chain, and requires the checkpoint's anchored event and hash to remain present. If the database is restored to a state before the checkpoint, verification fails closed.

## Security boundaries

The HMAC signature protects checkpoint contents against modification by parties without the key. The key is never persisted by this module. The checkpoint detects deletion of events at or before its anchored head, including deletion of the then-current tail, and detects rollback of the database behind that head.

This is not a remote service integration or immutable storage implementation. A party able to roll back both the database and the external checkpoint file to an older valid pair can still cause rollback; preventing that requires a separately managed monotonic/append-only checkpoint registry or trusted remote anchor. Events appended after the most recent checkpoint are not protected against tail deletion until a newer checkpoint is successfully written. Operators must checkpoint on a defined cadence and protect the checkpoint destination and key independently.

Tests use temporary local files, synthetic key material, and SQLite. They do not prove cross-device independence, production secret management, remote object-lock/WORM guarantees, live provider inference, paid API usage, deployment, physical device activation, or AI-to-AI communication.
