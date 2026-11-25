# Mission 171 — Independent Remote Anchor Adapter Contract

## Objective and non-goals

Define the minimum adapter boundary for a future independently administered
Provider Audit anchor. This mission adds a structural Python interface and
local contract checks only. It does not implement a network client, select a
cloud/database vendor, provision a service, configure TLS/secrets, mount
routes, or activate production traffic.

## Interface

`server.provider_audit_anchor_protocol.ProviderAuditAnchor` defines:

- `read_latest() -> record | None`: return the complete committed head.
- `append_checkpoint(expected_sequence, record) -> record`: atomically
  compare the committed sequence and append exactly one next record.

The runtime-checkable Python Protocol proves only method shape. It does not
prove atomicity, durability, isolation, availability, independent ownership,
or security. A fake adapter and the SQLite reference adapter are local test
fixtures, not evidence of an independently administered service.

## Mandatory semantics for a production adapter

1. **Linearizable compare-and-append:** compare `expected_sequence` and commit
   the next sequence in one atomic transaction. Concurrent writers must not
   create forks, gaps, duplicate sequence numbers, or lost updates.
2. **Append-only history:** committed records cannot be updated, deleted, or
   silently replaced. Administrative repair must be separately audited and
   must not masquerade as ordinary append.
3. **Chain validation:** enforce schema/version, record digest, previous digest,
   strictly increasing sequence, and strictly increasing checkpoint audit ID.
4. **Read consistency:** `read_latest` must not return a stale head after a
   successful durable append has been acknowledged. Define the consistency
   guarantee across replicas and fail closed if it cannot be met.
5. **Durability acknowledgement:** success is returned only after the write
   meets the service's documented durability policy. Specify replication,
   quorum, fsync/commit behavior, and acknowledged-write loss bounds.
6. **Retry and idempotency:** the HTTP boundary may return success for an exact
   retry of the latest record. A conflicting record at the same sequence must
   return conflict; never treat a different payload as a replay.
7. **Failure contract:** distinguish validation/conflict from unavailable or
   indeterminate outcomes. Timeouts after a possible commit must be safely
   resolvable by reading the head and retrying the exact record.
8. **Resource limits:** bound request/record sizes, connection and operation
   timeouts, concurrency, retention/backup growth, and rate limits.
9. **Transport and identity:** production client/server communication must use
   authenticated TLS with certificate/hostname validation, scoped identities,
   explicit principal authorization, credential rotation/revocation, and
   auditable operator access. No plaintext or trust-on-first-use shortcut.
10. **Independent trust domain:** anchor compute, storage, administrative
    credentials, backups, and audit access must be controlled separately from
    the application host/database. A second file or process on the same
    privileged host is not sufficient.
11. **Recovery evidence:** document encrypted backups, immutable/offline copy,
    restore drills, RPO/RTO, key recovery, incident response, and detection of
    rollback/fork attempts.
12. **Operational controls:** monitoring, alerting, ownership, change review,
    version compatibility, data migration, retention policy, and a tested
    rollback/disable procedure are required before activation.

## Required conformance evidence before production approval

- Independent threat model and named service/storage ownership.
- Contract test suite against the actual remote service, including concurrent
  compare-and-append races, exact retries, stale writers, sequence gaps,
  forks, tampering, timeout-after-commit, restart, replica lag, and restore.
- Evidence of durable acknowledgement and read-after-write behavior.
- TLS certificate validation and authentication/authorization negative tests.
- Backup restoration and rollback/fork detection evidence.
- Separate operator review and explicit activation approval.

A passing local fake/SQLite suite is necessary for interface compatibility but
is not sufficient for any of the evidence above.

## Verification boundary

Tests run locally in temporary storage and validate only structural protocol
compatibility and the existing local adapter/service contract. No external
network, production credentials, paid API, cloud resource, deployment, or
physical device is used. Production activation remains blocked.
