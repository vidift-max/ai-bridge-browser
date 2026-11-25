# Mission 175 — Independent Trusted Witness and Replication Contract

## Scope — 10 engineering rounds
1. Audit PR #176 and its exact-SHA push/PR workflow runs.
2. Review the local witness, durable anchor and remote-anchor adapter contracts.
3. Define a transport-neutral structural witness interface.
4. Validate witness identity, head shape and quorum parameters strictly.
5. Implement idempotent head replication with explicit per-witness outcomes.
6. Make partial writes visible and safely retryable; never report partial quorum as success.
7. Implement read-quorum verification with stale replicas distinguished from forks.
8. Test timeouts, unavailable and unauthorized witnesses, invalid acknowledgements, replay, rollback and divergent heads.
9. Document trust boundaries, quorum constraints and deployment requirements.
10. Run compile and focused/regression CI; inspect exact final-SHA jobs.

## Contract

A witness implements `read_latest() -> None | head` and
`record_head(head) -> acknowledgement`. The head is the exact triple
`sequence`, `record_digest`, `checkpoint_audit_id`. Implementations must
atomically enforce monotonic compare-and-append, durable commit, strict schema
validation, exact-retry idempotency and authorization. Network adapters must
apply finite connection/read/write deadlines themselves. This repository does
not implement a network transport.

`replicate_trusted_head` records every acknowledgement/failure. A partial
write quorum is explicitly marked because some witnesses may have committed;
retrying the identical head is required to complete safely. A read quorum
requires the exact head. Older replicas are reported as stale; any observed
same-sequence fork or newer divergent head fails closed.

## Quorum and consistency caveats

For a deployment with N distinct witnesses, choose write quorum W and read
quorum R so that W + R > N; require 2W > N for intersecting write quorums.
These arithmetic conditions are necessary design constraints, not proof of
consensus, Byzantine fault tolerance, or linearizability. Witnesses must have
distinct administrative control, credentials, storage and recovery paths.
A quorum of replicas under one administrator is not an independent trust
boundary. Membership changes, epoch transitions, key rotation and replica
recovery need a separately reviewed protocol before production use.

A witness response is not cryptographically authenticated by this module.
Production adapters must authenticate server identity and clients, authorize
principals per operation, protect transport, bind requests to tenant/project
and protocol version, and audit administrative changes. Fail closed on
timeouts, malformed data, unauthorized responses, conflicting heads or
insufficient quorum.

## Evidence and limits

Tests use deterministic in-memory fakes only. They validate the orchestration
contract and failure handling, not a remote service, actual network timeout,
TLS, durable remote storage, separate administration, distributed consensus,
quorum recovery, disaster recovery, or RPO/RTO. No service, credential, paid
API, deployment, device, or production data is used. No merge is performed.
