# Multi-AI Mission Room

## Purpose

Define the browser-side contract for a shared work room where many AI participants can receive different missions while GPT-6 acts as coordinator.

## Room model

The room is shared. Each participant receives an individual mission assignment:

- AI identity (IA-01, IA-02, etc.)
- mission identifier
- round number and total rounds (1/10, 2/10, ...)
- mission-file link
- report-file link
- status: PENDING, RUNNING, BLOCKED, or DONE

The browser is responsible for presenting and tracking this state. The mission contents remain in durable mission files rather than being treated as chat memory.

## Example room message

GPT-6 — RODADA 01

IA-01 → LINK DA MISSÃO 01
IA-02 → LINK DA MISSÃO 02
IA-03 → LINK DA MISSÃO 03
...
IA-20 → LINK DA MISSÃO 20

Each AI works on its own assignment and publishes its report to the shared room when complete.

## Context recovery

If an individual chat reaches "Janela de contexto cheia", the browser must preserve the assignment state, open a new chat through the later authorized UI-control layer, wait for readiness, and re-deliver the mission link plus minimal continuation state.

The mission file is the source of truth; the chat is a transport and collaboration surface.

## Round completion

The browser should eventually aggregate assignment states and reports. It should not send a completion checkpoint to GPT-6 until the configured completion condition is satisfied, or until a timeout policy explicitly marks missing participants.

## Scope boundary

This document does not authorize DOM automation, provider API access, remote control, GitHub write access for external AIs, or audio capture. Those are later, separately authorized phases.
