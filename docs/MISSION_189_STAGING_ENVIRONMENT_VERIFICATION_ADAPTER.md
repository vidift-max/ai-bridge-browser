# Mission 189 — Staging Environment Verification Adapter

## Purpose

Add an offline adapter for structured staging-verification records supplied by an operator or by an external probe system. The adapter checks declared environment, service identity, HTTPS URL, exact approved commit, artifact digest, timezone-aware observation time, integer 2xx status, health result, verifier identity, source kind, and canonical record digest.

## Provenance boundary

A matching record is labelled MATCHED_UNATTESTED. The SHA-256 digest detects changes to the canonical record; it is not a digital signature and does not authenticate the submitter, prove that a probe ran, or prove that the target is controlled by this project. The adapter performs no probe and does not contact the URL.

`automated_probe_record` is a declared source category only. The adapter checks that the record claims a probe was executed, but does not independently verify that claim. `operator_supplied` records must not claim that this adapter performed a probe.

## Safety

- Unknown fields are discarded and never echoed.
- URL credentials, query strings, and fragments are rejected.
- HTTP status booleans and strings are rejected.
- All safety flags remain false: no probe, deployment, secret access, provider call, or live-test authorization.
- Tampering with the record after hashing causes the digest check to fail.

## Test boundary

CI uses synthetic fixtures only. A MATCHED_UNATTESTED result is not a staging deployment, live health check, independent attestation, rollback proof, or authorization for a two-AI conversation. The M188 collector remains the deployment-evidence contract gate; this adapter supplies a separately validated observation record for human review.
