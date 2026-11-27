# Mission 185 — Firebase Workload Identity readiness

## Purpose

Provide a manually invoked, non-deploying preflight that validates the two GitHub Actions WIF variables and attempts Google Cloud authentication through the same provider and service account used by the Firebase deploy workflow.

## What it proves

When the workflow succeeds, it proves that at that time:

- The repository variables exist and have the expected resource/email formats.
- GitHub Actions obtained an OIDC identity token.
- Google Workload Identity Federation accepted the configured provider and repository trust condition.
- The configured service account could be impersonated and an access token was minted.

The access token is checked for non-empty content and is never printed.

## What it does not prove

It does not deploy Firebase, verify Firebase Hosting or live Realtime Database rules, prove that the service account has all required Firebase deployment roles, or prove AI-01/AI-02 messaging. It also cannot establish that the GitHub Environment has the required reviewers configured merely because the job references that environment.

## Required GitHub repository variables

Under **Settings → Secrets and variables → Actions → Variables**, configure:

- `FIREBASE_WORKLOAD_IDENTITY_PROVIDER`: full resource name in the form `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID`.
- `FIREBASE_DEPLOY_SERVICE_ACCOUNT`: service-account email in the form `NAME@PROJECT_ID.iam.gserviceaccount.com`.

These are identifiers, not private keys. Do not create or paste a service-account JSON key.

## How to run

After the repository variables and Google Cloud WIF trust relationship have been configured:

1. Open **Actions → Firebase Workload Identity readiness — AI Messenger**.
2. Select the reviewed branch `feat/mission-181-firebase-project-bootstrap`.
3. Choose **Run workflow**.
4. Type exactly `VERIFY_FIREBASE_WIF`.
5. If the `firebase-production` environment has required reviewers, wait for an authorized reviewer to approve.
6. Confirm the `FIREBASE_WIF_AUTHENTICATION_OK` marker.

A successful run is a WIF authentication preflight only. The separate deployment workflow still requires its own explicit `DEPLOY_AI_MESSENGER` confirmation and environment approval.

## Regression tests

Run with Node.js 22:

```sh
node --test tests/firebase-wif-config.test.mjs
node --test tests/firebase-wif-readiness-workflow.test.mjs
```

Both suites are included in the Firebase config validation workflow.

## Safety boundary

This workflow has only `contents: read` and `id-token: write` GitHub permissions. It uses the `firebase-production` environment, is manual-only, requires an exact confirmation string, and only runs from the reviewed bootstrap branch. It does not run Firebase CLI or mutate any Firebase resource.
