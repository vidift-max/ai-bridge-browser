# Mission 31 — Guest Messenger Reliability

## Objective
Harden the browser guest messenger against transient polling failures, tab visibility changes, and duplicate delivery without adding a new permission path or requiring WebSocket infrastructure.

## 10 rounds
1. Audited the Mission 30 polling/presence lifecycle and preserved its authenticated room scope.
2. Replaced fixed polling intervals with bounded one-shot scheduling.
3. Added exponential backoff from 4s to a maximum of 30s after polling failures.
4. Reset polling delay to 4s after a successful retrieval.
5. Added message-id deduplication so repeated server delivery cannot duplicate visible messages.
6. Kept inbound sequence advancement independent from the outbound send response to avoid skipping unseen messages.
7. Paused scheduled polling while the document is hidden and resumed immediately when visible.
8. Preserved the existing 15s visibility-aware presence heartbeat and explicit leave behavior.
9. Added regression tests for deduplication, backoff bounds, source safeguards, and existing security constraints.
10. Added dedicated CI covering browser, backend, and Android validation.

## Security / scope boundaries
- Uses the existing authenticated guest session and authorized single-room contract.
- No new public endpoint or privilege escalation.
- Guest bearer token remains memory-only.
- Untrusted message bodies continue to render through textContent, not HTML.
- No provider identity verification, external AI automation, deployment, or physical-device test is claimed.
- No WebSocket or push transport is claimed; this mission improves the existing polling transport only.

## Acceptance gate
PASS requires the dedicated Mission 31 workflow to complete successfully on the final branch SHA.
