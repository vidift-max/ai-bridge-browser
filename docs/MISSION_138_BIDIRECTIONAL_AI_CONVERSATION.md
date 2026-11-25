# M138 — Bidirectional AI Conversation Controller

Status: implementation committed; automated validation is running on the draft PR. Live provider integration is explicitly out of scope for this branch.
Base: M137 branch head `09904a8312eac7a85a3859c757286eff20c6f867`.
Branch: `feat/mission-138-bidirectional-ai-conversation`.

## Objective

Build a bounded conversation-loop controller for a two-identity PRIVATE room. The controller alternates target AI identities, validates every response identity and body, delivers each accepted turn through an injected authorized transport adapter, exposes observable state, and supports a stop request. The loop has a default of six turns and a hard maximum of twenty.

## Ten rounds

1. Verified M137 PR #138 remains open, draft, unmerged, and mergeable; both M137 text-bridge CI and Android Build completed successfully on its final commit.
2. Audited the existing authenticated Messenger, message ACK/history/long-poll behavior, and GPT-6 server-owned agent. Confirmed existing text transport can carry conversation history, but no generic second-provider runtime is registered.
3. Defined a strict two-member PRIVATE-room precondition. GROUP rooms, non-members, and rooms with any other member count cannot start a two-party loop.
4. Implemented `web/ai-conversation-loop.js` with injected responder and delivery adapters; no provider credentials or private browser sessions are read.
5. Added alternating target selection between the two authorized AI identities, validated sender identity, non-empty text and 5,000-character response bound.
6. Added bounded turn policy: default six, minimum two, hard maximum twenty; invalid or unbounded turn counts are rejected.
7. Added explicit stop/abort behavior, prevention of overlapping runs, context-change cancellation, and provider-error cleanup.
8. Added observable lifecycle snapshots and subscription callbacks for IDLE, RUNNING, and STOPPED states.
9. Added deterministic Node tests covering alternating turns, turn caps, stop during pending response, overlap rejection, private-room authorization, invalid content/identity, context changes, state notifications, and provider failures. Added CI workflow to run M138 tests plus M137 UI/backend regression tests.
10. Added this evidence record and opened a draft PR. No merge, deployment, provider activation, or external communication.

## Critical integration boundary

- The controller is an orchestration component. Its `respond` and `deliver` adapters must be supplied by an authorized provider/runtime and server transport.
- The current Rooms page does not yet instantiate this controller, and the repository does not yet register two independently authenticated AI provider runtimes that can answer on behalf of both identities. Therefore this mission does **not** claim that two live AIs automatically converse in the tablet today.
- The existing GPT-6 agent is a server-owned participant with a gated provider API; it is not the same thing as the private ChatGPT session open in the user's browser tab.
- Tests use fake responders and delivery adapters. They prove loop policy and lifecycle behavior only, not live inference or live delivery.
- No browser-session scraping, cookie access, paid API activation, secrets, Render deployment, domain, microphone streaming, or device activation.

## Acceptance criteria for this component

- Only an authorized two-member PRIVATE room can start.
- Turns alternate between the two identities and each responder identity is checked.
- Default and hard maximum turn limits are enforced.
- Stop prevents pending responses from being delivered after the stop request.
- Concurrent runs, context changes, malformed responses, and provider failures fail closed.
- CI passes M138 tests and M137 regression tests.