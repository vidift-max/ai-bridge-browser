# Mission 208 — AI-01 ↔ AI-02 physical-evidence readiness

## Scope
Only AI-01 and AI-02 are active. AI-03 remains out of scope.

## 10 rounds
01. Re-audit M207 evidence boundary and keep physical verification as a separate gate.
02. Add a bounded in-memory evidence model for roundtrip turns.
03. Record only turn number, sender identity, and response length; do not persist response text or credentials.
04. Add tests for ten alternating turns.
05. Add a hard cap on evidence events.
06. Strengthen readiness policy so both AI-01 and AI-02 must have verified isolated profiles.
07. Add regression tests for the isolated-pair gate.
08. Wire evidence capture into the orchestrator after a fresh assistant response is accepted.
09. Add dedicated Android/JVM CI for M208.
10. Keep the PR OPEN/DRAFT; no merge, release, login automation, deployment, or physical-device claim.

## Physical gate
The implementation still does **not** prove that two real ChatGPT accounts are authenticated or that a real AI-01 ↔ AI-02 conversation completed on an Android device.

A valid physical test must demonstrate:
- AI-01 and AI-02 are two distinct authenticated ChatGPT sessions.
- Each session is bound to a different verified WebView profile.
- The user starts the conversation manually.
- Ten responses alternate AI-01 → AI-02 → ... → AI-02.
- The UI reports the final turn count and evidence summary.
- No AI-03 is activated.

Credentials, cookies, tokens, and full response text are outside the evidence model.
