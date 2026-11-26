# Mission 206 — AI-01 ↔ AI-02 browser interaction

Status: IMPLEMENTED IN CODE / PHYSICAL TEST PENDING

## Objective
Allow the user to explicitly start a real two-tab ChatGPT conversation where AI-01 and AI-02 alternate turns. The active scope is exactly two identities; future capacity remains separate.

## Ten engineering rounds
1. Audit the existing M205 Android baseline and the existing two-agent server proof.
2. Add a guarded ChatGPT DOM bridge with multiple composer/send selectors.
3. Add an Android wrapper for installing and invoking the bridge.
4. Add an explicit AI-01 ↔ AI-02 orchestrator with bounded turns and response polling.
5. Expose the feature from the Android browser only after two isolated profiles and ChatGPT pages are verified.
6. Require an explicit user action and a non-empty initial prompt before automation starts.
7. Alternate the response from one tab as the next prompt to the other tab; never cross target identities.
8. Stop on timeout, missing DOM controls, lifecycle destruction or explicit stop; do not claim completion on a stale response.
9. Add deterministic JS tests for composer/send/response observation and fail-closed behavior.
10. Run exact-SHA CI and publish a Draft PR without merge, deployment or account activation.

## Safety boundary
- The browser does not log in, bypass MFA, read passwords, or obtain credentials.
- Automation only starts from an explicit user click.
- AI-01 and AI-02 must already have separate verified WebView profiles.
- No third AI is activated by this mission.
- No external provider API is contacted by the bridge itself.
- DOM selectors are provider/UI-dependent; physical ChatGPT testing remains required.

## Evidence boundary
Passing CI proves compilation and automated tests only. It does not prove that two real ChatGPT accounts are logged in, that current ChatGPT DOM selectors work on a physical Android device, or that a real AI-01 ↔ AI-02 conversation completed.
