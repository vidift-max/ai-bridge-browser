# Continuous Work Model

The project is designed for continuous cooperative work without silently executing unsafe actions.

## Loop

1. Browser starts.
2. Durable state is restored.
3. Tabs recover to their saved URLs and stable identities.
4. The user explicitly resumes automation when appropriate.
5. The future AI Bridge reconnects authorized participants.
6. Messages remain durable while a participant is loading, paused, rate-limited, or disconnected.
7. Work continues from durable mission/message state after recovery.

## Boundaries

Continuous does not mean uncontrolled. The system must preserve explicit authorization for remote actions, tool access, account access, GitHub writes, and provider integrations.

## Current stage

Only the browser foundation and provider-neutral API contracts exist. Automatic provider communication is not implemented yet.