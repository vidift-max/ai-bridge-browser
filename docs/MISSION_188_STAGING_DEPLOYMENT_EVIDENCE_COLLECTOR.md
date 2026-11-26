# Mission 188 — Staging Deployment Evidence Collector

## Objective

Collect operator-supplied staging deployment metadata into a deterministic, allowlist-based report. Reuse the M187 deployment contract and make it easier to inspect evidence without copying arbitrary input fields.

## Data handling

The collector copies only the explicitly allowlisted deployment metadata fields. Unknown fields are discarded, and their values are never echoed. This is intended to prevent API keys, bearer tokens, cookies, environment dumps, request bodies, or unrelated payloads from entering the report.

The collector:
- performs no network or filesystem I/O;
- does not deploy, probe health, or execute rollback;
- does not access environment variables or secret stores;
- does not call model providers;
- does not create rooms, register sessions, or send messages.

## Report integrity

The report contains the M187 contract state and checks, allowlisted evidence, a SHA-256 fingerprint of the canonical JSON evidence, and a count of discarded unknown fields. The fingerprint detects accidental changes to the collected record; it is not a signature, trusted timestamp, external attestation, or proof that the evidence is true.

validate_collected_report() checks the schema version, allowlist, fingerprint, and safety flags. A valid report is still only a metadata artifact.

## Operator workflow

1. Obtain deployment evidence through the operator's approved hosting workflow.
2. Remove credentials and secret values before submitting metadata.
3. Pass only the metadata object to the collector with the expected approved commit SHA.
4. Inspect each contract check and resolve every BLOCKED item.
5. Preserve the redacted report and fingerprint for review.
6. Do not interpret READY_FOR_STAGING_HANDOFF_REVIEW as permission to execute a live AI conversation.

## Proof boundary

CI proves the deterministic collector and its validation logic against test fixtures. It does not prove that a deployment exists, that the URL resolves, that health was actually checked, or that rollback is operational. No staging environment or external service was contacted by this mission.
