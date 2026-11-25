# Mission 172 — Remote Anchor Adapter Conformance

## Scope

Add reusable, local conformance checks for the current adapter contract. The
suite exercises the existing in-memory fake and SQLite reference adapter. It
does not claim either is a production remote service or independent trust
domain.

## Behaviors checked

- Initial append followed by read-after-write.
- Stale expected-sequence rejection without overwriting the committed head.
- Sequence-gap rejection without mutation.
- Two concurrent initial writers yield exactly one committed winner.
- Previous-digest forks and non-monotonic checkpoint audit IDs are rejected.
- Tampered record digests and boolean expected-sequence values are rejected.
- SQLite committed state remains readable after reopening the adapter.
- Exact HTTP retry of the latest committed record is idempotent.
- A different record targeting the same sequence returns HTTP 409.
- A simulated response timeout after durable commit returns HTTP 503; retrying
  the exact same record resolves the ambiguous outcome as a replay, without a
  second append.

The timeout test deliberately models a lost response after commit. It does
not simulate a real network, distributed consensus, replica failover, or
power-loss durability. The fake adapter's validation is aligned with the
reference backend so that both exercise the same expected-sequence input
contract.

## Evidence boundary

CI validates local adapter behavior only. Production acceptance still
requires running the same conformance suite against the actual independently
administered service, with concurrent clients, network fault injection,
restart/replica tests, TLS and identity tests, and independently reviewed
durability and recovery evidence.

No external endpoint, production credential, cloud resource, paid API,
deployment, route activation, or device is used. Production activation remains
blocked.
