# Mission Coordinator

## Purpose
The browser-side coordinator observes a MissionRoom and turns assignment state into a deterministic round checkpoint.
It does not call ChatGPT, Claude, Kimi, Gemini, GitHub, or provider-specific browser automation.

## Checkpoint
For a round, the coordinator reports room ID, round number, total assignments, done, blocked, pending, running, and completion.

## Advance rule
A round can advance only when every assignment in that round is DONE. BLOCKED, PENDING, and RUNNING remain incomplete.

## Boundary
Current: MissionRoom -> MissionCoordinator -> checkpoint.
Future: checkpoint -> durable bridge event -> GPT-6 coordinator.
The bridge transport and provider adapters remain separate. No automatic message submission is implemented by this change.