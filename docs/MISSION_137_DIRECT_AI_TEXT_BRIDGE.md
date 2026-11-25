# M137 — Direct AI Text Bridge and Explicit Linking

Status: implementation in progress; CI evidence is pending.
Base: `3dd805279a3d1119d042f3e7e40245a6a17608cd` (M136 Android APK readiness head).
Branch: `feat/mission-137-direct-ai-text-bridge`.

## Goal

Provide a clear **Vincular IA** action and a safe first text-only path between two already provisioned AI identities. Reuse the authenticated private-conversation and message transport instead of creating a second messaging protocol.

## Ten rounds

1. Audited PRs #133–#137 and verified that they remain open, draft, unmerged, and mergeable. Confirmed Android Build run `45590339497` succeeded on M136; debug build/unit tests and release-preparation succeeded, while final signing was skipped as expected without signing secrets.
2. Audited the existing Android tab registry, Rooms UI, private-conversation creation, authenticated `POST /v1/conversations`, `POST /v1/messages`, ACK and long-poll transport.
3. Defined the linking contract: a private link contains exactly the authenticated identity and one other provisioned identity; server membership is authoritative.
4. Added an explicit **Vincular IA** button to the Rooms conversation-creation panel. It switches the form to PRIVATE and guides the user to choose one authorized identity.
5. Added a dedicated `createPrivateLink` helper and stricter response validation, including exact returned membership; self-links, missing peers, and cross-linked responses are rejected.
6. Reused the existing text messenger for sending, receiving, history, acknowledgements, and idempotent retries. No new transport, provider credential, or browser-session access was introduced.
7. Added backend tests for private link creation, delivery to the selected peer, outsider rejection, recipient-scope enforcement, idempotent retry, and ACK redelivery behavior.
8. Added browser tests for the link button, private-mode selection, exact two-identity membership, invalid responses, and self-link rejection.
9. Run the repository CI and review every required check on this branch. Record exact workflow IDs and results here after completion.
10. Publish this evidence record and open a draft PR for review. No merge or deployment.

## Security and behavior boundaries

- Linking means creating a server-authorized private Messenger conversation between two provisioned AI identities. It does **not** sign into, inspect, scrape, or control ChatGPT browser sessions or cookies.
- Two ChatGPT tabs do not become linked merely by being open. The two identities must exist in the server directory and authenticate independently.
- Text is the only scope of M137. Existing audio/WebRTC features are not expanded or represented as AI-to-AI microphone streaming.
- No provider API key, paid inference, Render service, domain, secret, deployment, external invitation, or physical-device activation is configured by this mission.
- Automated tests use local test fixtures; they do not prove a live server, live AI response, or real communication from the user's tablet.

## Acceptance criteria

- A visible, accessible **Vincular IA** action is available in Rooms.
- The action guides the user into a private two-identity conversation.
- The server's returned membership must exactly match the authenticated identity and selected peer.
- Existing authenticated text send/receive and idempotent message handling remain in use.
- Outsiders and recipients outside the private room are rejected.
- Tests and CI pass before mission PASS is declared.
