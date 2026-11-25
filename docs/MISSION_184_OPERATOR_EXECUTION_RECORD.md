# Mission 184 — Operator Execution Record

## Objective

Separate the **authorization state** for the first live AI-USER → AI-PEER turn from evidence that a turn actually executed.

The contract has three states:

- `BLOCKED`: required authorization/evidence is absent or inconsistent.
- `AUTHORIZED_FOR_OPERATOR_EXECUTION`: both explicit authorizations exist, but no execution is claimed.
- `EXECUTED_FIRST_TURN`: execution markers and valid first-turn evidence are present, including the explicit stop after the first successful round trip.

## Required boundary

Authorization is not execution. A record in `AUTHORIZED_FOR_OPERATOR_EXECUTION` MUST report `executionPerformed: false` and `providerCallsPerformed: false`.

This mission does not create a room, register sessions, enable provider calls, deploy staging, contact providers, or send a real message.

## Operator sequence for a future live test

1. Verify the exact deployed commit.
2. Verify the staging identity and endpoint.
3. Verify the private room contains exactly AI-USER and AI-PEER.
4. Verify each AI owns its registered session.
5. Verify the exact (AI_ID, provider_ID) mapping.
6. Evaluate the controlled authorization gate.
7. Obtain explicit operator authorization.
8. Obtain explicit provider-call authorization.
9. Execute exactly one AI-USER → AI-PEER round trip.
10. Stop immediately after the successful first round trip and record evidence.

Any identity mismatch, provider mismatch, authentication failure, timeout, unexpected status, or failed first turn is a stop condition. Do not retry inside the same authorization.

## Evidence binding

When evidence is supplied, the record can be checked against:

- deployed SHA;
- room ID;
- exact participant IDs;
- exact session AI IDs;
- provider mapping;
- correlation ID.

No credentials, bearer tokens, cookies, prompts, or response bodies belong in the record.

## Scope of proof

CI proves the state machine and its fail-closed checks. It does **not** prove provider connectivity or a real two-AI conversation.
