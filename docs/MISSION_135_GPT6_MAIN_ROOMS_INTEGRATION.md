# Mission 135 — GPT-6 Integration in the Primary Collective Room

## Ten rounds

1. Revalidated Mission 134: its latest commit has successful dedicated and regression CI runs; PR #135 remains open and unmerged.
2. Created an isolated Mission 135 branch from the validated Mission 134 head.
3. Added a browser-side GPT-6 room bridge that requires authenticated room membership and explicit `AI-GPT6` membership.
4. Bound the bridge to the existing primary Rooms composer; no second browser tab or separate messenger page is required.
5. Added an explicit opt-in control to include the server-owned GPT-6 identity when creating a GROUP room; PRIVATE conversations remain unchanged.
6. Enforced the room member ceiling in the UI when GPT-6 is selected, leaving capacity for at most 18 additional selected identities plus the owner and GPT-6.
7. Routed messages in GPT-6-enabled rooms to the authenticated `/v1/gpt6/room/respond` endpoint using the existing stable retry request ID.
8. Reloaded the authoritative room message stream after the response so both the user message and GPT-6 reply render through the same history/ACK pipeline.
9. Added validation tests for the bridge, opt-in group membership, primary composer wiring, and safe serving of the new browser asset.
10. Added Mission 135 CI and this record. No API key, external inference call, merge, deploy, invitation, or paid resource was used.

## User-visible behavior

- Create a GROUP room and explicitly check “Incluir GPT-6 na sala coletiva”.
- Send messages from the existing composer in `/rooms`.
- The browser calls the server-side GPT-6 room agent and reloads the same room's persisted message stream.
- Other admitted room participants can read the user message and GPT-6 response from the same conversation.
- If GPT-6 is not a member, the normal room messaging path is unchanged.
- If the API is not configured or the server-side paid-call gate is disabled, the server returns a clear unavailable response; the browser does not receive provider credentials.

## Important boundaries

- The server-owned `AI-GPT6` API participant is not the private ChatGPT session in this conversation.
- The model, context, and API availability are determined by the server-side provider configuration.
- CI uses deterministic mocked provider responses. It does not prove live inference, real account linkage, hosted availability, or communication with another external AI.
- Existing rooms are not silently modified to add GPT-6; membership is explicit at room creation.
- No domain purchase, hosting deployment, secret configuration, or paid API use is part of this mission.

## Validation commands

```sh
python -m unittest server.test_gpt6_room_agent server.test_gpt6_room_agent_http -v
node --test web/ai-room-gpt6.test.mjs web/ai-room-creation.test.mjs web/ai-room-ui-messenger.test.mjs
python -m py_compile server/http_server.py server/gpt6_room_agent.py
```
