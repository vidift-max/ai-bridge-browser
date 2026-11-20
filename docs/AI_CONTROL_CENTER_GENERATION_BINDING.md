# AI Control Center — Generation State Binding

## Purpose
Bind one independent generation state machine to each registered AI panel. The registry supports up to six active AI tabs.

## Per-panel contract
- Each panel owns its own `ChatGPTGenerationMonitor` instance.
- Starting a new mission resets only that panel's monitor.
- Observations are routed by the stable `tabId` + `profileId` pair.
- `GENERATING` maps to `RESPONDING`.
- `RESPONSE_COMPLETE` maps to `RESPONSE_COMPLETE` only after the monitor's completion rule.
- An unrecognized or insufficient observation maps to `UNKNOWN`; it must never authorize report confirmation.
- One panel's observations cannot change another panel's response state.

## Current implementation boundary
This is an in-memory model and testable state binding. MainActivity does not yet poll WebViews, read response text, capture the final two lines, infer context fullness, or send messages automatically. No live ChatGPT DOM selector has been validated on the physical tablet.

## Verification
Unit tests cover panel isolation and refusal to confirm reports when the generation signal is unknown. Android CI remains the build gate for each commit.
