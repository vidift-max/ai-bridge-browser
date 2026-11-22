# Mission 42 — Persistent storage readiness and staging gate

**Branch:** `v2-saas-alpha`  
**Starting HEAD:** `439b477eb1c19a0b000c1e9a578a24e37893ff78`  
**Scope:** backend readiness contract, tests, Render Blueprint safety, operator runbook.  
**No deployment or hosting-resource changes authorized or performed.**

## Ten rounds

1. Added explicit storage modes: `local`, `persistent`, and `ephemeral`; persistent mode requires an absolute root and a database path contained below it. Commit `51645f2`.
2. Added configuration tests for invalid mode, ephemeral rejection, persistent-root/path containment, and malformed root. Commit `af27dda`.
3. Changed `/readyz` to enforce the storage contract and report the selected mode only when configuration passes. Commit `2c0a13c`.
4. Added HTTP regression test proving ephemeral hosted storage is not ready. Commit `a1d34be`.
5. Added HTTP test for a declared persistent root and reported storage mode. Commit `5bf7961`.
6. Updated the experimental Render Blueprint to declare `ephemeral`, ensuring it cannot accidentally claim durable readiness. Commit `4b535f0`.
7. Added the staging-storage operator runbook, approval boundary, secret handling, restart test sequence, and rollback constraints. Commit `1c2226f`.
8. Updated backend documentation with the fail-closed storage contract and its limitations. Commit `ed2b573`.
9. Wired the HTTP test fixture to operational storage verification and added a corrupt-database readiness rejection test. Commit `a0bb92d`.
10. Final same-HEAD workflow verification is required after this report/README verification marker. CI outcomes and exact final SHA are recorded in the closing mission result, not assumed in advance.

## Important technical boundary

A `persistent` readiness result validates an operator-declared absolute writable directory and path containment. It does **not** independently prove that the hosting provider mounted a durable disk. The hosting dashboard, disk attachment, mount path, service identity, and restart persistence must be verified separately.

The current `render.yaml` deliberately sets `MESSENGER_STORAGE_MODE=ephemeral`. It is preparation-only and must remain not-ready for real AI traffic until a persistent disk is explicitly approved and provisioned.

## Not done

- No Render service/disk/database created, modified, deployed, or restarted.
- No secrets or AI credentials requested, read, changed, or committed.
- No two real AI identities provisioned.
- No HTTPS endpoint, cross-device, or cross-network communication test.
- No Android UI/device test, background sync, WebSocket, push, WebRTC, or voice calling.

## Acceptance

Code acceptance requires Messenger Backend Test and Android Build to succeed on the exact final branch HEAD. Hosted staging and real two-AI communication remain blocked until persistent storage is approved and independently verified, two distinct credentials are provisioned securely, and a real send/receive/ACK/restart test passes.
