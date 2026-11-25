# Mission 145 — Provider Recovery and CI Hardening

## Ten-round scope

1. Audited PR #145/M144 and inspected the failed CI job rather than declaring PASS.
2. Fixed a variable-shadowing defect in HMAC attestation verification.
3. Corrected durable-store regression expectations for retryable FAILED requests.
4. Added direct regression coverage for expected-context attestation verification.
5. Added cross-connection coverage for durable request claiming.
6. Added a Python compile gate to the existing integrity workflow.
7. Added a dedicated Mission 145 CI workflow.
8. Documented the failure-first validation boundary and recovery semantics.
9. Created a Draft PR from the corrected branch; no merge or deployment.
10. Final CI status must be checked on the final SHA before declaring PASS.

## Evidence boundary

M145 is a CI/reliability hardening mission. It does not create API keys,
enable paid provider calls, deploy infrastructure, activate devices, access
private browser sessions, or prove live provider inference.

A FAILED durable request can be reclaimed with the same payload digest. A
COMPLETED request remains replayable from durable state. A changed payload
for an existing request ID remains a conflict.

The attestation verifier now keeps the cryptographic expected signature
separate from the optional expected-context dictionary, preventing the
verification context from being overwritten internally.

No merge is authorized by this mission.
