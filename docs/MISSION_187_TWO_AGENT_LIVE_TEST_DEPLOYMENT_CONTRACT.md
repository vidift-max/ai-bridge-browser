# Mission 187 — Two-Agent Live-Test Deployment Contract

## Purpose

Define the minimum redacted evidence needed to review a staging deployment before any controlled two-agent test. The contract is an offline validator, not a deployer or health-probe client.

## Required evidence

- Explicit environment `staging`; production targets are rejected.
- Deployment ID and service ID.
- HTTPS staging URL with no embedded credentials, query string, or fragment.
- Exact deployed commit SHA matching the approved SHA.
- SHA-256 digest of the deployment artifact.
- Timezone-aware deployment timestamp.
- Successful post-deployment health evidence: a 2xx integer status and timezone-aware timestamp.
- A distinct, verified rollback commit.
- Explicit operator approval.
- An explicit declaration that no secrets are included in the evidence.

## States

- `BLOCKED`: any required field is missing, malformed, or mismatched.
- `READY_FOR_STAGING_HANDOFF_REVIEW`: all supplied metadata passes structural validation. This is not permission to deploy, probe, rollback, access credentials, or start the AI conversation.

The evaluator always reports `deploymentPerformed: false`, `healthProbePerformed: false`, `rollbackPerformed: false`, `providerCallsPerformed: false`, and `liveTestAuthorized: false`.

## Operator evidence checklist

- [ ] Confirm the deployment is in the staging environment, not production.
- [ ] Record the deployment and service IDs.
- [ ] Record the HTTPS staging URL without tokens or query parameters.
- [ ] Confirm the deployed commit equals the approved commit exactly.
- [ ] Record the artifact SHA-256 digest.
- [ ] Record deployment and health-check timestamps with timezone offsets.
- [ ] Record a successful post-deployment 2xx health result from independent evidence.
- [ ] Identify and verify a distinct rollback commit.
- [ ] Record operator approval for staging handoff review.
- [ ] Remove credentials, bearer tokens, cookies, environment values, and request/response bodies from evidence.

## Stop conditions

Stop the staging handoff review if the target is production or ambiguous, the commit is stale, the URL exposes credentials, health evidence is absent or older than deployment, rollback is unverified, secrets appear in evidence, or any identity is inconsistent.

## Proof boundary

Tests exercise supplied metadata only. They do not prove a staging service exists, that the URL resolves, that a deployment occurred, that health was probed, or that rollback works. No Render or other hosting deployment was triggered by this mission. No secrets, provider APIs, rooms, sessions, or real messages were accessed or created.
