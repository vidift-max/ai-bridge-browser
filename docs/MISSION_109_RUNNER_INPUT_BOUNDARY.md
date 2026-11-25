# Mission 109 — Runner input boundary hardening

## Ten-round execution record

1. Reviewed M108 CI and traced the initial backend failure to acceptance of an HTTPS URL with an empty port.
2. Patched M108 to reject an empty explicit port; added explicit negative tests for send-response message ID and recipient mismatches.
3. Started M109 from the corrected M108 source checkpoint while its final CI run was still pending.
4. Audited the shared HTTPS-origin normalizer and found that a trailing colon could still represent an empty port.
5. Hardened the shared normalizer to reject empty ports and percent-encoded authority components.
6. Added a regression case for an HTTPS origin ending in an empty port.
7. Audited the first-contact runner's own entry point rather than assuming the offline preflight is always invoked first.
8. Hardened runner validation for blank, oversized and control-character conversation IDs, plus blank or CR/LF-bearing credentials.
9. Added tests proving these invalid values are rejected before any network call and registered M109 in CI branch filters.
10. Kept the mission offline-safe: no Render activation/deploy, no secret creation, no real message, no physical device activation and no merge.

## Evidence boundary

M109 strengthens local input validation only. It does not prove a live service, real AI sessions or AI-01-to-AI-02 communication. HTTP Long Poll remains the only realtime transport; staging remains Free, ephemeral and manual-deploy only.
