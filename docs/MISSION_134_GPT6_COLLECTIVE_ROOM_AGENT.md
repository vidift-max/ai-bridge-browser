# Mission 134 — GPT-6 Collective Room Agent

## Ten rounds

1. Revalidated Mission 133 at commit `db6484647cd56c70b66ed86918343a7450402a83`; all four required CI jobs passed. Mission 133 remains an unmerged Draft PR.
2. Created an isolated Mission 134 branch from the validated Mission 133 head.
3. Added a server-owned internal participant identity, `AI-GPT6`, with display name `GPT-6`; it has no browser-visible bearer token.
4. Added a backend-only submission boundary that permits only registered internal identities and still enforces room membership and recipient authorization.
5. Added `GPT6RoomAgent` to validate that the authenticated caller and GPT-6 are members of the same room.
6. Added room-scoped user-message persistence and GPT-6 response fan-out to every other room participant.
7. Added deterministic message and idempotency identifiers; completed retries return the persisted GPT-6 reply without a second provider request. In-process locking prevents concurrent duplicate requests in one server process.
8. Added the authenticated `POST /v1/gpt6/room/respond` endpoint and explicit API-call readiness metadata. Paid API calls remain disabled unless explicitly enabled by server configuration.
9. Updated the GPT-6 web messenger to target a collective room, retain a request ID across retries, and render the persisted room response. Added service and HTTP contract tests.
10. Added this mission record and a dedicated CI workflow. No external provider request, secret setup, merge, deployment, or paid resource was used.

## Contract

- The user must be an authorized member of the selected conversation.
- The room must explicitly include `AI-GPT6`; the browser cannot impersonate this identity.
- User and assistant messages are persisted in the same conversation and delivered to the other authorized members.
- The provider key remains server-side. The paid API gate is fail-closed and disabled by default.
- The API-backed assistant is not the same authenticated private ChatGPT session running this conversation. Its model and context are controlled by server configuration.
- A completed retry reuses the persisted assistant message. The in-process lock does not claim exactly-once provider execution across a process crash between upstream response and message persistence.
- A successful CI run proves mocked/local contracts only; it does not prove a live API request, deployed service, or real-time conversation.

## Validation

```sh
python -m unittest server.test_gpt6_room_agent server.test_gpt6_room_agent_http server.test_openai_text_adapter server.test_provider_registry -v
node --test web/gpt6-messenger.test.mjs
```

## Safety boundary

No API key, provider credential, external network inference, paid usage, real invite, merge, deployment, or physical-device activation is performed by this mission.
