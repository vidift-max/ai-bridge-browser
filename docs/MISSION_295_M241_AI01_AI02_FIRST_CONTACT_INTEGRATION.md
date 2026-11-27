# Mission 295 — M241 + AI-01 / AI-02 first-contact integration

## Baseline and boundaries

- Base branch: `feat/mission-241-updater-backport-v2-saas-alpha`
- Base SHA: `d2861ab8e257cd07e095c31de708fe4264c89bd2`
- Integration branch: `feat/mission-295-m241-ai-first-contact-integration`
- Source implementation: `feat/mission-224-ai-first-contact-launch`
- Active identities: AI-01 and AI-02 only. AI-03 remains disabled/out of scope.
- The updater and signing configuration from M241 are retained; no signing secrets or certificate values are read or changed.

## Ten rounds

1. **Baseline reconciliation** — use M241 as the parent and avoid merging the divergent M224 branch.
2. **Runtime components** — selectively port the DOM bridge, two-session orchestrator, launch policy, evidence model, and account/session policies.
3. **Control center** — retain the 20-account architecture ceiling while limiting this mission's active panel set to two.
4. **Profile isolation** — assign a unique WebView profile before other WebView operations and read the profile name back; fail closed on mismatch or unsupported multi-profile.
5. **User confirmation** — add a visible first-contact action, preflight both ChatGPT tabs, and require explicit confirmation of the two distinct accounts.
6. **DOM readiness correction** — require a composer, a present send button, an enabled send button, and no active generation before allowing the confirmation step.
7. **Response completion hardening** — require observed generation followed by three identical, fresh, non-generating response reads before relaying a response.
8. **Lifecycle safety** — stop the relay when automation is paused, a tab navigates, a tab closes, the renderer crashes, or the activity leaves the foreground.
9. **Regression coverage and CI** — port policy/evidence/session tests and enable Android CI for this integration branch.
10. **Review boundary** — retain the change as an open Draft PR against M241; no merge, release, install, deploy, or physical-device claim.

## Validation limits

- Unit tests and Android build are CI evidence only.
- A successful build does not prove that ChatGPT DOM selectors work against the live website.
- A physical acceptance test must still verify two independently authenticated ChatGPT accounts, distinct WebView profiles, a manually confirmed first prompt, and ten alternating completed responses on the Android device.
- The relay is fail-closed if the visible generation indicator is not observed; this may cause a timeout on a future ChatGPT UI change rather than incorrectly forwarding a partial response.
- No credentials, cookies, tokens, or full response text are included in the evidence summary.

## Prohibited actions for this mission

No merge, release publication, deployment, installation/update on the user's device, cache/data clearing, or changes to signing secrets/certificates.
