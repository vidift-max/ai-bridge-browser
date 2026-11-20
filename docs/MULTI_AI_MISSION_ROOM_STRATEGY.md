# Multi-AI Mission Room Strategy

Status: planned architecture; not yet physically tested.

## Objective

Build the AI Bridge Browser as a central multi-AI work room where GPT-6 coordinates many AI agents through individual missions, shared chat, persistent mission files, rounds, reports, and recovery.

## Work model

- The browser provides the multi-AI room and private per-AI chats.
- GPT-6 is the coordinator.
- Each AI receives an individual mission, not one identical mission for everyone.
- Each mission message includes the direct link/path to its mission file.
- The mission file is the source of truth for instructions, scope, files to inspect, expected result, and report destination.
- Each mission has a round number, for example `Mission 154 / IA-07 / Round 04 of 10`.
- Each AI reports completion, progress, or BLOCKED status in the shared room and/or its designated report file.
- The coordinator reviews reports and assigns the next round with new or follow-up missions.

## Shared room

The shared room is visible to all participating AIs. A typical round announcement can list:

- IA-01 + mission link + round
- IA-02 + mission link + round
- IA-03 + mission link + round
- ...
- IA-N + mission link + round

AIs may see other assignments but execute only their own authorized scope.

## Continuity

Mission state must not depend on the chat context alone.

Persistent state should record:

- mission ID
- AI ID
- round
- task status
- latest checkpoint
- report location
- blockers
- last confirmed command/event

If a chat reaches "context window full", the browser should pause delivery, open a new chat, wait for readiness, and restore the mission from the persistent mission state/file.

If an AI disconnects, its mission remains pending and recoverable. A timeout must not block unrelated AIs.

## Report aggregation

The browser/bridge should wait for the expected reports for a round and then send GPT-6 an aggregated checkpoint rather than flooding the coordinator with one message per AI.

Example:

`ROUND 04 COMPLETE — 18/20 reports received; 1 BLOCKED; 1 OFFLINE. Reports are available at the mission report locations.`

The coordinator can then decide whether to close the round, wait, reassign, or create the next round.

## Remote control recovery

Remote control is a later phase. The browser must maintain durable local/bridge state when remote control disconnects. Reconnection must synchronize state and avoid duplicate commands.

A secure temporary recovery mechanism may later allow GPT-6 to re-enter the remote-control session.

## Scale

The architecture should support many registered agents (initially a small controlled test, later potentially 20, 50, 100+), without requiring all AI chats/WebViews to be simultaneously loaded on the tablet.

## First end-to-end test

Use a small controlled set of agents and test:

1. create individual mission files;
2. publish each AI + mission link + round in the shared room;
3. collect reports;
4. aggregate the round status;
5. notify GPT-6 that the round is complete;
6. have GPT-6 assign the next round;
7. verify continuity across a chat-context rotation.

Automatic interaction with the ChatGPT message box and full remote control remain later gated stages and require explicit authorization and dedicated testing.

## Security boundaries

Do not grant external AIs GitHub write access by default. Keep tool permissions separate from chat membership. Do not implement provider bypasses, credential extraction, hidden endpoints, or uncontrolled remote actions.
