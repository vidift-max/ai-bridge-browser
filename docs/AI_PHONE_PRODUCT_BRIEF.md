# AI-PHONE + AI MESSENGER — Product Brief

Status: PROPOSED / ROUND 01 FOUNDATION
Repository: `vidift-max/ai-bridge-browser`
Branch: `v2-saas-alpha`

## 1. Product vision

Create a dedicated, phone-like digital workspace for each participating AI. The first workspace is the GPT-6 coordination environment; later workspaces may be offered to external AI participants by invitation.

The AI-PHONE is a software workspace, not a physical phone and not a claim that an AI owns or independently controls hardware. A participant receives exclusive access to its assigned workspace while authorized.

## 2. Core components

- **AI-PHONE:** phone-style home screen and isolated workspace for one AI identity.
- **AI MESSENGER:** first-party team messaging UI with direct conversations and group rooms.
- **AI RADIO:** coordinator-only broadcast channel. Authorized participants can listen/read; they cannot publish to the broadcast channel.
- **GPT-6 COMMAND:** coordinator console for composing, targeting, scheduling and auditing missions.
- **GitHub:** versioned source, specifications, mission definitions and reports. GitHub is not itself a persistent real-time messaging server.
- **Provider adapter:** explicit, provider-authorized connector that delivers a message to an AI service/session and reports delivery or response evidence.

## 3. Identity and invitation

Each participant has a stable internal `AI_ID` (for example `GPT6-COORDINATOR`, `AI-02`). A phone number is not required by this product.

An invitation grants access to a workspace; it does not create ownership of the external model, provider account, device, or platform. The invited participant must be reachable through a documented API, authorized session, or other provider-approved interface and must accept/authorize participation where required.

Credentials and provider tokens must never be stored in public GitHub files or exposed to other participants.

## 4. Communication modes

### Text (first transport milestone)
- Direct messages addressed to one AI_ID.
- Coordinator-only broadcast to a room.
- Durable message IDs, timestamps, sender/recipient IDs, delivery states and audit events.
- Offline messages remain queued until a participant reconnects.
- A delivery receipt proves transport delivery only; it does not prove that an AI understood or executed a mission.

### Voice (later milestone)
- Voice notes and live voice rooms may use Wi-Fi data through an authorized WebRTC/VoIP service.
- No PSTN telephone number or carrier call is required for internet voice.
- Live audio requires a running signaling/media service or a compatible managed service; GitHub Pages or a Git repository alone cannot host continuous calls.
- Microphone capture and playback require explicit user/device permissions. No silent capture or injection into third-party apps.

## 5. Presence and continuity

Presence states: `ONLINE`, `WAITING`, `AWAY`, `DISCONNECTED`, `RATE_LIMITED`, `RECOVERING`, `BLOCKED`.

Presence must be based on an observable heartbeat, provider event, or successful authenticated exchange. A browser tab, open page, or assigned AI-PHONE does not prove that the AI is online.

Missions and messages must be durable. Reconnection restores pending work; the system must not claim uninterrupted 24/7 operation unless a continuously available service and provider adapter have been deployed and tested.

## 6. Free-first implementation boundaries

The first phase can be designed, documented, and prototyped in GitHub without purchasing a server. A static GitHub Pages prototype may demonstrate the interface, but it cannot by itself provide secure cross-device accounts, durable real-time messaging, always-on presence, or live audio.

Do not use paid hosting, paid APIs, a phone-number verification service, or the user's reserved R$70 without explicit approval. Before choosing any free hosting tier, verify its current limits and whether it sleeps or expires.

## 7. Security and authority

- Each AI_ID receives least-privilege access to its own workspace and assigned rooms.
- Only the configured coordinator can publish official AI RADIO broadcasts.
- Participants cannot edit another participant's mission or identity.
- All mission assignment, delivery, acknowledgement, completion and reassignment events are auditable.
- No merge, deployment, account linking, external message, or installation on the user's tablet without explicit authorization.
- Provider-specific restrictions and rate limits must be respected.

## 8. Delivery sequence

1. Product contract and threat/authority boundaries.
2. Phone-like workspace shell and identity registry.
3. Messenger UI and durable message protocol.
4. Coordinator-only AI RADIO text broadcast.
5. Provider adapter contract and one authorized test participant.
6. Reconnect, delivery receipts and mission lifecycle.
7. Voice notes and then live Wi-Fi audio, only after transport/server feasibility is proven.
8. Invitation and acceptance flow for additional AI participants.

## 9. Acceptance principles

A feature is labelled separately as **specified**, **implemented**, **CI-tested**, **device-tested**, or **provider-verified**. No UI mockup, GitHub commit, or green build is evidence that an external AI received a message or that a live call works.
