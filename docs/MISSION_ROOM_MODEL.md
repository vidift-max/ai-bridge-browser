# Mission Room Model

## Purpose

The browser needs a deterministic local model for a shared room containing many individual AI assignments.

## Invariants

- A room has a stable non-blank `roomId`.
- An assignment is unique by `missionId + aiId + round`.
- Different AIs may receive different missions in the same round.
- Assignment status remains one of `PENDING`, `RUNNING`, `BLOCKED`, or `DONE`.
- A round is complete only when it contains at least one assignment and every assignment in that round is `DONE`.
- A blocked or missing participant does not silently become complete; timeout/exception policy belongs to a later coordination layer.
- The model does not send messages, automate provider UIs, control WebViews, or grant tool/GitHub permissions.

## Why this is the next boundary

This model lets the browser determine when a configured round has actually finished before a future coordinator/checkpoint layer sends an aggregated result to GPT-6.

It deliberately does not implement that transport yet. The current phase is state modeling and testable invariants only.
