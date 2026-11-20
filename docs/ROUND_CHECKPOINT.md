# Aggregated Round Checkpoint

The checkpoint is the compact handoff produced for GPT-6 after a mission round.

It contains the room, round, total-round label, and one entry per assigned AI. Each entry preserves the AI identity, mission identity, status, and report link.

The checkpoint is immutable after construction.

## Boundary

Individual reports remain separate source artifacts. The checkpoint is an index/summary for coordination; it is not a replacement for the reports.

Current flow:

MissionRoom -> MissionCoordinator -> RoundCheckpoint

Future flow:

RoundCheckpoint -> durable bridge event -> GPT-6

No provider API, browser DOM automation, audio, remote control, or GitHub write permission is introduced here.
