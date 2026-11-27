# Mission 182 — Firebase preflight regression hardening

## Scope

This mission strengthens the local/CI safety checks used before a manually authorized Firebase deployment. It does not change Firebase production data, publish Hosting, deploy Realtime Database rules, create Google Cloud credentials, merge a pull request, or configure either phone.

## Changes

- Added `tests/firebase-project-validator.test.mjs` using Node's built-in test runner.
- Added ten regression cases covering valid configuration, wrong project alias, missing invite page, missing route rewrite, incorrect Hosting path, missing template exclusion, incorrect RTDB rules path, open root read rule, nested open write rule, and malformed rules JSON.
- Extended `scripts/validate-firebase-project.mjs` to recursively inspect all nested `.read` and `.write` declarations.
- The validator blocks boolean `true` and string `"true"` permissions at any depth.
- Updated the Firebase validation workflow to run the regression suite and trigger when test files change.

## Commands

```sh
node scripts/validate-firebase-project.mjs
node --test tests/firebase-project-validator.test.mjs
```

## Security boundary

This is a static repository preflight, not a full Firebase Rules emulator test and not a substitute for reviewing deployed rules in the Firebase Console. The check does not prove the live Firebase project is reachable, that Hosting has been deployed, that Workload Identity Federation is configured, or that AI-01 and AI-02 can communicate.

Production deployment remains manual, requires the exact confirmation input `DEPLOY_AI_MESSENGER`, and requires operator authorization after review. Scope remains AI-01 and AI-02 only.
