# Mission 207 — AI-01 ↔ AI-02 roundtrip proof

## Scope
Only AI-01 and AI-02 are active. The architecture may support more identities, but this mission does not activate AI-03 or any additional account.

## 10 rounds
01. Audit M206 relay state and response observation.
02. Make the 10-turn roundtrip limit explicit in the Android control.
03. Add deterministic policy tests for exactly two identities and bounded turns.
04. Centralize the two-AI allowlist and fresh-response gate.
05. Enforce that policy inside the orchestrator.
06. Keep user-started operation and isolated WebView profiles as prerequisites.
07. Keep timeout/fail-closed behavior for missing controls and stale responses.
08. Record the last delivered response for evidence/debugging without storing credentials.
09. Prepare CI for the exact branch and Android/JVM verification.
10. Leave the work in an OPEN Draft PR; no merge, release, deployment, login automation, or physical-device claim.

## Evidence boundary
Code/tests do not prove a real ChatGPT-to-ChatGPT conversation. Physical Android verification with two already-authenticated, isolated accounts remains the final gate.
