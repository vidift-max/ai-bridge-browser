# Mission 39 — Acknowledgement and Recovery Safety

## Goal
Prevent the guest room HTTP Long Poll client from advancing its sequence cursor before the server confirms message acknowledgement.

## Changes
- Render/deduplicate messages independently from transport acknowledgement.
- Acknowledge every delivered message, including messages already rendered after a retry.
- Advance the local sequence cursor only after the corresponding ACK succeeds.
- Stop cursor advancement when the session generation becomes stale.
- Reject unsafe or negative message sequence values before cursor commit.

## Scope boundaries
- HTTP Long Poll remains the only enabled transport.
- No WebSocket, Server-Sent Events, provider identity verification, provider automation, deployment, or physical-device claims.
