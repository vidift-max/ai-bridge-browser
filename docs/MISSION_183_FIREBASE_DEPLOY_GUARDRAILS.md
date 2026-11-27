# Mission 183 — Firebase production deployment guardrails

## Scope

This mission hardens the manual GitHub Actions deployment path. It does not deploy Firebase, change Google Cloud IAM, create credentials, change live rules, merge pull requests, or configure AI-01/AI-02 devices.

## Repository-enforced controls

The workflow `.github/workflows/firebase-ai-messenger-deploy.yml` now requires all of the following:

- Manual `workflow_dispatch` execution only.
- Exact typed confirmation: `DEPLOY_AI_MESSENGER`.
- Dispatch from the reviewed branch `feat/mission-181-firebase-project-bootstrap` only.
- GitHub deployment environment named `firebase-production`.
- Minimal token permissions: `contents: read` and `id-token: write`.
- Static Firebase project validation before Google authentication.
- Google Workload Identity Federation; no service-account JSON key.
- Fixed Firebase project ID `ai-messenger-b97df`.
- Deploy scope limited to `hosting,database`.
- Twenty-minute job timeout and non-cancelling production concurrency.

A dispatch from another branch or with a different confirmation string will not enter the deploy job.

## GitHub administrator setup still required

Before any deployment is authorized, a repository administrator must open:

**GitHub → Settings → Environments → firebase-production**

Configure the environment with:
1. Required reviewers, selecting the authorized human reviewer(s).
2. Deployment branch policy allowing only `feat/mission-181-firebase-project-bootstrap`.
3. No environment secrets are required by this workflow; the two WIF identifiers remain repository Actions variables as documented in Mission 181.

The workflow's `environment` declaration alone does not create reviewer approval. The protection rules must be configured in GitHub Settings and verified by an administrator before deployment. If the repository plan or permissions do not offer required reviewers, deployment remains blocked until an equivalent approved control is established.

## Regression tests

Run:

```sh
node --test tests/firebase-deploy-workflow.test.mjs
node --test tests/firebase-project-validator.test.mjs
```

The deployment workflow guardrail suite checks manual-only triggering, exact confirmation, trusted branch, environment declaration, token permissions, fixed project, WIF authentication, restricted deployment targets, validation order, timeout, and concurrency.

## Follow-up live verification

After the operator has completed the required GitHub and Google Cloud setup and explicitly authorized deployment, use the separate read-only smoke workflow documented in [Mission 184](MISSION_184_FIREBASE_LIVE_SMOKE_VERIFICATION.md). That workflow checks the published invite routes and unauthenticated database-root denial; it does not deploy or prove device-to-device messaging.

## Evidence boundary

Passing these repository tests proves only that the checked-in workflow text contains the expected guardrails. It does not prove that GitHub Environment protection rules, WIF provider, IAM bindings, GitHub variables, Firebase Hosting, or live Realtime Database rules are configured correctly.

No deployment is authorized by this mission. Do not run the workflow until the operator explicitly authorizes publication after reviewing the PR and verifying the GitHub environment protections.
