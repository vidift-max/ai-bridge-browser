# Mission 183 — First-Turn Protocol Contract

## Objective

Make the future first real AI-USER → AI-PEER exchange explicitly one-turn,
evidence-driven, and fail-closed. This mission does not authorize or execute
the live exchange.

## Ten rounds

1. Audit M182 final CI and exact SHA.
2. Correct provider evidence to include provider IDs, not only AI IDs.
3. Require room identity metadata.
4. Require exact two participants and two own sessions.
5. Bind each AI to a non-empty provider ID.
6. Require expected provider mapping when supplied by the operator.
7. Require first-turn direction AI-USER → AI-PEER.
8. Require an explicit stop marker after the first successful round trip.
9. Test stale SHA, extra participant, duplicate session, provider mismatch,
   missing provider, wrong direction and missing stop evidence.
10. Final audit: code/CI PASS only; live execution remains blocked without
    separate operator authorization.

## Execution boundary

A valid evidence object proves that supplied metadata satisfies the contract.
It does not prove that a real provider was contacted unless the operator later
supplies independent live execution evidence.

No provider credential, bearer token, cookie, prompt, or response body belongs
in the evidence object.

## Stop conditions

Stop without retrying the live turn on any identity mismatch, unexpected
participant, provider mismatch, authentication failure, timeout, unexpected
status, or successful first round trip. A second turn requires a new explicit
authorization.
