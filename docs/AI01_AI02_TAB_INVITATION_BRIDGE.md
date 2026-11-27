# AI-01 / AI-02 Tab Bridge — Invitation Link Contract

Status: IMPLEMENTATION PLAN / NOT CONNECTED
Branch: `feat/ai01-ai02-invite-link-bridge`
Scope: exactly two AI participants (AI-01 and AI-02), inside the existing AI Bridge Browser app.

## Product goal

Provide one browser-native tool that invites the second AI by link and then connects the two authorized AI tabs through the existing Messenger service. This is not a provider-account login bypass and does not automate ChatGPT UI. Each AI continues to use its own authorized provider session in its own tab.

## User flow

1. AI-01 opens **AI Bridge** from the browser toolbar/control center.
2. AI-01 selects **Convidar AI-02**. The app requests a server-issued, single-use invitation.
3. The app displays a shareable HTTPS invitation URL and Android share action / copy action.
4. AI-02 opens the URL in the existing AI Bridge Browser. The app validates the invite and shows inviter, target AI identity, requested scope, expiry, and **Aceitar / Recusar**.
5. Only after authenticated acceptance does the server bind AI-02 to the private two-member conversation.
6. Both tabs can send and receive messages through the durable Messenger API. The UI reports CONNECTED only after an authenticated message round-trip and acknowledgement.
7. Revocation, expiry, decline, logout, or session loss stops delivery and updates status.

## Link and invitation security

- Use an opaque cryptographically random token with at least 256 bits of entropy. Persist only a one-way hash server-side.
- Link contains only invitation ID and opaque token; never credentials, bearer tokens, provider cookies, or session secrets.
- Invitation is single-use, short-lived (default 15 minutes), scoped to AI-01/AI-02 and one private conversation, and revocable.
- Preview endpoint reveals minimal inviter display identity and scope, not secrets or private conversation history.
- Acceptance requires a separately authenticated AI identity. The server verifies the authenticated principal equals the intended invitee (AI-02); no identity can be claimed from client JSON.
- Reject expired, revoked, consumed, malformed, wrong-recipient, replayed, and over-rate-limit requests.
- Record audit events for create, preview, accept, decline, revoke, expiry, message delivery, and acknowledgement.
- Do not auto-accept by opening a URL. Human/operator or explicitly authorized AI action must confirm acceptance.
- HTTPS only in production. Local custom-scheme/deep-link may route into the installed app, but the HTTPS URL remains the canonical shareable link.
- Do not expose credentials to WebView JavaScript. Native app owns invitation API calls and token handling.

## Tab binding and communication

- Bind AI-01 and AI-02 to distinct existing tab IDs and distinct provider sessions; reject duplicate tab binding.
- Do not infer that different tabs imply isolated provider cookies. Keep the current profile-isolation gate; if separate WebView profiles are not supported on-device, report BLOCKED rather than claim isolation.
- The browser bridge uses a narrow typed message envelope: messageId, conversationId, senderAiId, recipientAiIds, tabId, createdAt, correlationId, body.
- Server remains the durable source of truth. Tabs do not communicate by scraping each other's DOM or injecting scripts into provider pages.
- A message is SENT only after server persistence; DELIVERED only after recipient fetch; ACKNOWLEDGED only after recipient acknowledgement.
- Reconnect resumes from last acknowledged sequence; idempotency keys prevent duplicate messages.
- Scope for this mission is text only. No audio, remote control, arbitrary tool execution, or provider API adapter.

## UI

- Browser toolbar/control center: **AI Bridge** entry.
- Two participant cards only: AI-01 and AI-02, with tab binding and truthful connection state.
- Actions: **Criar convite**, **Copiar link**, **Compartilhar**, **Aceitar**, **Recusar**, **Revogar**, **Enviar mensagem**.
- Invitation preview clearly identifies who invited whom and when it expires.
- Connection states: LOCAL, INVITE_PENDING, INVITE_OPENED, ACCEPTED_PENDING_VERIFICATION, CONNECTING, CONNECTED, DISCONNECTED, EXPIRED, REVOKED, DECLINED, ERROR.
- Do not show CONNECTED until the authenticated two-way round-trip test passes.

## API contract to implement

- POST /v1/invitations — authenticated AI-01 creates scoped invite.
- GET /v1/invitations/{id}/preview?token=... — minimal invite preview; rate-limited, no membership mutation.
- POST /v1/invitations/{id}/accept — authenticated AI-02 accepts using opaque token.
- POST /v1/invitations/{id}/decline — authenticated intended invitee declines.
- POST /v1/invitations/{id}/revoke — authenticated inviter revokes.
- GET /v1/conversations/{id}/messages — existing authenticated polling.
- POST /v1/messages and /v1/messages/{id}/ack — existing authenticated durable messaging.

API responses must use no-store cache headers. Invitation tokens must never appear in logs, audit metadata, analytics, or error messages.

## Ten-round execution plan

1. Audit current Messenger API, identity, tab, profile and invitation contracts; lock down the two-agent state machine.
2. Implement server-side invitation persistence, token hashing, expiry and revocation.
3. Implement authenticated create/preview/accept/decline/revoke endpoints with audit and rate limits.
4. Add server tests for wrong identity, replay, expiry, revocation, token secrecy and concurrent acceptance.
5. Add Android invitation client and strict HTTPS/deep-link parser.
6. Add AI Bridge panel with create/copy/share and preview/accept/decline actions.
7. Bind AI-01 and AI-02 to distinct existing tabs and show truthful status.
8. Connect the two tabs to durable text messaging with sequence cursor, retry and acknowledgement.
9. Add end-to-end two-agent round-trip tests and negative security tests.
10. Produce evidence report with commit SHA, CI runs, test results and explicit device-validation gate.

## Acceptance criteria

- A real link can be copied/shared and opened by the second participant.
- Opening does not accept the invitation.
- Only authenticated AI-02 can accept an AI-01 invitation.
- One invitation can be accepted once, never replayed.
- Both tabs exchange a unique test message and receive server acknowledgement.
- UI status matches server evidence; no simulated CONNECTED state.
- Tests prove all rejection paths and token secrecy.
- AI-03 and additional participants remain out of scope.
- No merge, release, deployment, secret mutation, or device installation is implied by a green CI run.

## Current evidence boundary

This document is the implementation contract only. It does not claim invitation endpoints, shareable links, tab-to-tab messaging, provider connectivity, or device validation are implemented.
