# Mission 182 — Staging Evidence and First-Test Execution Checklist

## Objective

Define a machine-readable, non-secret evidence contract for the first controlled
two-AI exchange. M182 does not execute the exchange.

## Ten rounds

1. Close M181 CI and record its exact SHA/run/job.
2. Audit the M180 → M181 branch chain and Draft/unmerged state.
3. Define non-secret execution evidence.
4. Bind evidence to the expected deployed commit.
5. Require exact staging identity and endpoint metadata.
6. Require exactly AI-USER and AI-PEER with one own session per AI.
7. Require provider assignments to match the expected mapping.
8. Define first-turn evidence fields and stop conditions.
9. Run deterministic tests with provider network access disabled.
10. Final audit: implementation PASS only; live execution remains separately authorized.

## Evidence fields

Record only metadata: deployed SHA, staging identifier, staging endpoint,
room ID, AI IDs, provider IDs, request/correlation IDs, timestamps, and response
status codes. Never record provider API keys, bearer tokens, cookies, or prompt/
response content in the evidence object.

## First-turn boundary

If a future operator receives explicit authorization to execute the live test:

1. Verify the deployed SHA exactly matches the approved SHA.
2. Verify the staging endpoint and private room identity.
3. Verify both AI sessions are independently registered.
4. Verify provider assignments.
5. Run one short user-to-peer turn.
6. Record non-secret request/correlation/status metadata.
7. Stop immediately after the first successful round trip.
8. Do not send a second turn unless separately authorized.

Any identity mismatch, unexpected participant, provider mismatch, timeout,
authentication failure, or unexpected status is a stop condition.

## Current safety boundary

M182 CI is offline with respect to providers. It does not deploy, provision
secrets, create rooms, register sessions, enable provider calls, or send real
messages. A VALID evidence result is a validation result, not proof that a
live exchange occurred.
