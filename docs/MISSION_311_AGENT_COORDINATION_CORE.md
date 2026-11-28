# M311 — GPT-6 agent coordination core

Date: 2026-11-28  
Branch: `feat/mission-311-agent-coordination-core`  
Base: `feat/mission-295-m241-ai-first-contact-integration` at `b76024e5335837cedfba83474ec4f56aa8e60599`.  
Draft PR: #245.

## Ten rounds
1. **PASS — audit:** inspected agent identity, session policy, MainActivity, Messenger backend and prior mission records.
2. **PASS — reconciliation:** documented that M310's claimed AgentRoster, AgentRosterCodec and AgentMissionQueue files were absent at its audited HEAD; see `MISSION_310_AGENT_AUDIT_CORRECTION.md`.
3. **PASS — isolation:** created the M311 branch from the audited M310 HEAD without changing the base branch.
4. **PASS — roster:** added a synchronized logical-agent registry with canonical IDs, 20-agent capacity and status validation.
5. **PASS — codec:** added strict schemaVersion 1 JSON encode/decode with duplicate, malformed, unknown-schema and invalid-state rejection.
6. **PASS — queue:** added FIFO mission scheduling, unique mission IDs, bounded instructions, pending cancellation and a two-session cap; only AI-01/AI-02 can claim provider work.
7. **PASS — roster tests authored:** added capacity, duplicate, malformed ID, busy-session scope and removal tests.
8. **PASS — codec/queue tests authored:** added round-trip, schema rejection, duplicate identity, malformed JSON, FIFO, cancellation and scope tests.
9. **PASS — coordinator:** added `AgentCoordinator` with GPT-6 as the declared coordinator, registration, mission assignment, dispatch and completion state transitions.
10. **BLOCKED — CI evidence:** Android Build workflow filters were extended for the M311 push branch and M295 PR base; draft PR #245 was opened. The available GitHub workflow-run query returned no run and combined commit status returned no statuses for the observed head. Therefore tests are **authored but not confirmed executed**; no CI PASS is claimed.

## Current implementation boundary
- Logical roster ceiling: 20 identities (AI-01…AI-20).
- Current provider-session scope: AI-01 and AI-02 only; at most two concurrent sessions.
- AI-03…AI-20 may exist as logical records and queued work, but cannot claim provider sessions in this phase.
- GPT-6 is the central coordinator for mission assignment, dispatch decisions, review and evidence aggregation.
- Roster and queue are in-process models in this increment. Android persistence/UI integration and remote room transport are not included here.
- `BUSY` means scheduler-owned work, not proof of live provider login or a connected model.

## Safety and deployment boundary
No Tool Hub work, paid hosting, merge, Release, deployment, installation, credential changes, or device operation. PR #245 remains Draft / OPEN / not merged.
