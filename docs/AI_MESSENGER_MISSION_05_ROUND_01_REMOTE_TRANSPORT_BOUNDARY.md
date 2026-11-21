# AI MESSENGER — Mission 05 — Round 01/10 — Remote Transport Boundary

Status: SPECIFIED / NOT IMPLEMENTED
Repository: vidift-max/ai-bridge-browser
Branch: v2-saas-alpha

## Objective

Define the internal boundary between the Android Messenger and a future authenticated remote transport without coupling the UI directly to HTTP, WebSocket or a provider.

## Required transport operations

A future transport implementation must expose these logical operations:

- submit message using the canonical message envelope and an idempotency key;
- fetch pending deliveries after an acknowledged cursor;
- acknowledge a received message;
- report transport/session state;
- close or invalidate a session locally.

The concrete network mechanism is deliberately deferred.

## Boundary rules

The Messenger UI may create local drafts and local operations, but it must not mark a message as SENT, DELIVERED or ACKNOWLEDGED merely because a transport method was called.

A remote state may only be applied after a response from an authenticated server/adapter supplies evidence for that state.

The transport layer must never accept a client-supplied sender identity as authoritative. Sender identity comes from the authenticated session.

## Failure behavior

The transport boundary must represent at least:

- unavailable/offline;
- authentication required or rejected;
- authorization denied;
- temporary transport failure;
- server conflict for reused idempotency key with different payload;
- permanent rejection;
- successful server acceptance.

Failures must not silently convert a local message into a delivered message.

## Security

- credentials are never stored in source control;
- credentials are not included in ordinary message logs;
- conversation authorization remains server-side;
- provider credentials are isolated from Messenger UI code;
- transport implementations must not bypass AI_ID authorization.

## Current evidence boundary

This round defines the boundary only. No HTTP request, WebSocket connection, server endpoint, authentication flow, remote queue, provider integration or physical-device communication is implemented by this document.

## Acceptance

The next implementation rounds may choose HTTP polling or WebSocket after the server architecture is established. The Messenger UI should depend on the boundary rather than a specific network library.
