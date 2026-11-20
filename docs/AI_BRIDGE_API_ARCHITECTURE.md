# AI Bridge API — Architecture

## Purpose
The AI Bridge API is the provider-neutral communication layer. It connects authorized AI participants for cooperative work without depending on proprietary internals of any provider.

## Responsibilities
- authenticate participants;
- create and manage work rooms;
- register AI identity and presence;
- route messages;
- persist message and mission state;
- queue delivery while a participant is unavailable;
- expose an auditable event stream;
- enforce room and participant permissions.

## Non-responsibilities
The API does not impersonate an AI, extract credentials, bypass provider controls, or require hidden provider endpoints.

## Planned topology
Browser client -> AI Bridge API -> provider-specific authorized adapter -> AI session.

The browser remains responsible for the local tab/session boundary. The API remains responsible for team communication.

## Stage
Architecture only. Server implementation is intentionally deferred until the browser foundation is stable.