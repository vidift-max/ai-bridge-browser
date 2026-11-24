# Mission 97 — Repair Android CI checkout

## 10-round execution record

1. Retrieved the actual GitHub Actions run associated with M96.
2. Enumerated all four jobs and isolated the only failure to android-regression.
3. Retrieved the Android job log and confirmed Gradle ran in an empty workspace.
4. Inspected the M95 and M96 branch contents; the Gradle root files exist at repository root.
5. Compared job steps and found android-regression omitted actions/checkout@v4.
6. Created this isolated branch from M96 without changing or merging earlier PRs.
7. Added actions/checkout@v4 before Java and Gradle setup.
8. Added a regression test that enforces checkout-before-Gradle ordering.
9. Included the regression test in backend-invite-e2e and retained the existing four jobs and staging safety assertions.
10. Prepared a Draft PR; final CI must be checked from GitHub Actions before claiming validation.

## Evidence and boundaries

- M96 head: de6c120d2442f16a756978c26b8ab0e02859c1bb.
- Observed workflow run: 45494520596, completed with failure.
- android-regression failed because the workspace did not contain a Gradle build.
- backend-invite-e2e, browser-invite-contract, and activation-boundary succeeded on that run.
- Android Gradle root files were confirmed in the M95 base and M96 head.
- No merge, deployment, Render service creation, paid resource, credential, or physical device activation.
- CI is not considered passing until the new branch's actual run is retrieved and all required jobs succeed.
