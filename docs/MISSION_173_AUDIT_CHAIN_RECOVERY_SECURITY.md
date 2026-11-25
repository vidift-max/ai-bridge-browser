# Mission 173 — Audit Chain Recovery and Security

## Scope

This mission hardens the SQLite reference adapter's history verification. It
adds an optional independently retained head witness, explicit comparison of
two independently obtained adapter copies, and fail-closed results for corrupt
stored records. It does not add automatic repair, history rewriting, or a
production remote service.

## Ten engineering rounds

1. Audit the Mission 172 PR, exact-SHA CI, and current chain/adapter behavior.
2. Identify the suffix-truncation blind spot when verification has no external
   expected head.
3. Define a strict trusted-head witness: sequence, record digest, and checkpoint
   audit ID, validated without accepting booleans as integers.
4. Implement full-history verification against that witness.
5. Convert malformed stored JSON/records into an explicit integrity failure.
6. Add two-copy verification that rejects invalid copies and divergent heads.
7. Add corruption fixtures for old-record tampering and malformed JSON.
8. Add rollback/truncation fixtures, including deletion of the entire history.
9. Prove matching copies pass, divergent/corrupt copies fail, and verification
   does not silently repair or rewrite the remaining head.
10. Run compile and targeted/full relevant CI, inspect exact final-SHA jobs, and
    document residual limits.

## Security behavior

- A caller-supplied trusted head detects suffix truncation and rollback.
- A chain's own surviving rows cannot prove that its tail was not deleted.
- Two copies are compared by their verified sequence and terminal digest.
- A malformed record or failed copy causes a fail-closed result.
- No repair, restore, truncation, or rewrite is attempted. Preserve the damaged
  evidence for operator-led investigation.

## Evidence boundary

The tests use temporary SQLite files only. The expected head is useful only if
it is retained independently and protected by a separate trust domain.
Comparing two SQLite files does not make them independent if one administrator
can alter both. Hash chaining does not prove external authenticity, signer
identity, consensus, or remote durability.

No external endpoint, production credential, cloud resource, paid API,
deployment, route activation, or device is used. Production recovery remains
unproven and requires independently administered replicas, backup/restore
drills, and operational evidence.
