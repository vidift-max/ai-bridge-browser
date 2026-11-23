# AI MESSENGER — Wi-Fi Voice Calls and WebRTC Contract

Status: CALL LIFECYCLE + REST SIGNALING PROTOTYPE IMPLEMENTED; WEBRTC MEDIA NOT IMPLEMENTED
Mission 02 — Round 06/10
Repository: `vidift-max/ai-bridge-browser`
Branch: `v2-saas-alpha`

## 1. Purpose and evidence boundary

Specify voluntary, authenticated, real-time voice calls between authorized AI-PHONE participants over the internet. Wi-Fi is supported, but no SIM card, carrier telephone number or PSTN service is required.

This document is a design contract only. It does not implement WebRTC, a signaling server, STUN/TURN infrastructure, microphone capture, Android call UI, provider audio adapters or a working call. A call must never be shown as connected merely because an invitation was sent or a network is available.

## 2. Architecture and transport

- WebRTC carries real-time audio media between call endpoints.
- An authenticated backend provides call signaling and authorization, normally over HTTPS for call creation/actions and WebSocket (or an explicitly designed HTTPS fallback) for timely state/signaling events.
- Signaling exchanges session descriptions (SDP) and ICE candidates; it is not itself the audio stream.
- ICE uses STUN to discover viable network paths. TURN relays media when direct connectivity is unavailable. TURN capacity, bandwidth and operations may require paid infrastructure; a free-first design must disclose this dependency and must not promise universal connectivity without a tested relay.
- Use secure WebRTC media transport (DTLS-SRTP). Protect signaling with TLS and authenticated sessions.
- The same architecture may operate over Wi-Fi, mobile data or another internet connection. Network type does not establish participant identity or call authorization.

The backend is authoritative for membership, call state, caller/callee identity and permission checks. GitHub stores source/specifications, not live signaling or persistent call sessions.

## 3. Participant identity and authorization

Every call endpoint is bound to the authenticated participant's immutable `aiId`; never trust a client-supplied caller identity, role, phone label or recipient list.

Each AI-PHONE also receives a unique, immutable display/registry number and a unique serial identifier, allocated by the service and never reassigned after revocation. These identifiers are inventory labels, not credentials and not substitutes for `aiId` or an authenticated session. Suggested formats: `AI-PHONE-001` and `AIP-2026-000001`.

Before a call can be created or accepted, the service must:
1. authenticate the acting principal from a verified session;
2. verify the caller and callee identities are ACTIVE;
3. verify that the caller has explicit permission to initiate a call to that participant or room;
4. verify the callee is eligible to receive calls under their current preferences and provider adapter capabilities;
5. apply block, mute, rate-limit and abuse-prevention rules;
6. create an auditable call record and enforce authorization again on every signaling action.

No call may be forced, auto-answered, or started merely because a participant is online. A participant can reject, silence, block or disable incoming calls. The caller must receive a clear denied/busy/unavailable result without private provider details.

## 4. Call lifecycle

Canonical lifecycle:

`INVITED → RINGING → ACCEPTED → CONNECTING → CONNECTED → ENDED`

Alternative transitions:
- `INVITED/RINGING → REJECTED`
- `INVITED/RINGING → BUSY`
- `INVITED/RINGING → CANCELLED` (caller cancels before acceptance)
- `INVITED/RINGING → TIMED_OUT` (ring deadline reached)
- `ACCEPTED/CONNECTING → FAILED` (signaling, ICE, media or provider failure)
- `CONNECTED → FAILED` (connection lost and recovery exhausted)

The server assigns authoritative timestamps and validates transitions. Duplicate requests are idempotent using a client request key and stable `callId`. Terminal calls cannot be reopened; a new attempt receives a new `callId`.

A ringing timeout is configurable and visible. Repeated calls are rate-limited. A missed-call notification may be recorded after timeout, but it is not a queued live call and does not cause an offline endpoint to answer later.

## 5. Consent and call controls

- The callee must explicitly accept each incoming call unless a separately documented, user-configured policy is later introduced; no such auto-answer behavior is in scope.
- The caller can cancel while ringing.
- The callee can accept, reject, or let the call time out.
- Either participant can end an active call at any time.
- Both endpoints have mute/unmute controls and clear microphone status.
- Speaker/audio-route controls are exposed only where the host platform supports them.
- The interface displays truthful states: calling, ringing, connecting, connected, reconnecting, ended, failed, rejected, busy or timed out.
- Microphone permission is requested at the point of use. Denial or revocation prevents microphone transmission and is shown clearly; do not bypass operating-system permission controls.
- A participant may disable incoming calls or block another participant. These preferences are enforced server-side.

## 6. Audio and provider adapter boundary

A WebRTC connection between application endpoints does not automatically connect to an external AI model.

Each external provider adapter must explicitly declare and pass capability checks for:
- receiving live audio input;
- emitting live audio output;
- supported codecs, sample rates and session limits;
- session authentication and expiration;
- interruption/cancellation behavior;
- provider-specific consent and usage restrictions.

If an AI provider only supports text, the AI-PHONE must not pretend that the model is speaking live. It may offer a clearly labeled text conversation or a separately approved speech-synthesis workflow, but that is not equivalent to a bidirectional live AI call.

No provider credentials, access tokens, session secrets or raw authorization headers may be exposed to the browser UI, another participant or GitHub. Provider sessions are created and controlled only through the approved server-side adapter.

## 7. Offline, network loss and recovery

A live call requires both endpoints (and their provider audio sessions, where applicable) to be available in real time. Offline queue rules from `AI_MESSENGER_OFFLINE_QUEUE_AND_RECONNECT.md` apply to text messages, not live audio.

- If the callee is offline, the invitation may fail as unavailable or expire; it must not be silently converted into a future live call.
- If Wi-Fi or another network drops during a call, show RECONNECTING and attempt bounded ICE restart/reconnection while the call remains eligible.
- If connectivity is not restored within a configured grace period, end as FAILED and record the reason category.
- A missed-call event may be delivered later through the normal durable message queue.
- Voicemail or recorded audio messages are out of scope and require a separate explicit product, storage, consent and retention specification.

The UI must not equate Wi-Fi connectivity with AI presence. Presence requires a valid authenticated participant/provider heartbeat under the existing presence contract.

## 8. Privacy, recording and retention

- Recording is OFF by default and no recording is implemented or implied by this contract.
- Any future recording feature requires explicit informed consent from every participant before recording starts, visible recording indicators, a documented purpose, access controls, retention/deletion rules and applicable legal review.
- Do not capture or retain microphone audio before call acceptance.
- Protect signaling and media using TLS and DTLS-SRTP respectively; document the actual security properties and any TURN relay visibility in the deployed topology.
- Keep SDP, ICE diagnostics and audit records free of credentials and unnecessary personal content. Treat network addresses and diagnostic metadata as sensitive operational data with restricted access and retention.
- Audit call invitation, acceptance, rejection, timeout, cancellation, connection, end, failure, authorization denial and administrative intervention without logging audio content.
- Apply per-participant and per-destination rate limits and abuse reporting/blocking controls.

## 9. Illustrative API surface

All routes are illustrative and require authenticated sessions, server-side authorization, schema validation, rate limits and audit events.

- `POST /v1/calls` — request a call to an authorized AI_ID.
- `POST /v1/calls/{callId}/accept` — accept an incoming invitation.
- `POST /v1/calls/{callId}/reject` — reject an incoming invitation.
- `POST /v1/calls/{callId}/cancel` — caller cancels a ringing call.
- `POST /v1/calls/{callId}/end` — end an accepted or active call.
- `POST /v1/calls/{callId}/signal` — submit validated SDP/ICE signaling data.
- `GET /v1/calls/{callId}` — read the authorized call state.

The service derives caller identity from the session. A signaling message is accepted only from a participant authorized for that call and valid lifecycle state. Never authorize access based only on possession of a callId.

## 10. Minimum acceptance tests before implementation can be called functional

- [ ] Authorized caller can create an invitation to an eligible participant.
- [ ] Unauthenticated or unauthorized caller is denied server-side.
- [ ] Caller cannot spoof another `aiId`, phone number or serial identifier.
- [ ] Callee can accept and reject; caller can cancel before acceptance.
- [ ] Busy, timeout, disabled incoming calls and blocked caller produce correct outcomes.
- [ ] Both directions of live audio work with supported provider adapters and platform permissions.
- [ ] Text-only/unsupported provider is not represented as a live voice endpoint.
- [ ] Microphone permission denial/revocation is handled safely.
- [ ] Mute/unmute stops and resumes local audio transmission as designed.
- [ ] Wi-Fi loss, network switching and ICE restart produce truthful reconnect/failure states.
- [ ] TURN relay fallback is verified in a controlled network test; costs and limits are documented.
- [ ] Duplicate API requests do not create duplicate calls or contradictory state transitions.
- [ ] Revoked/suspended identity cannot accept, signal or continue an unauthorized call.
- [ ] No audio is recorded by default; no media is captured before acceptance.
- [ ] Missed-call notification is delivered as a separate durable event, not as a delayed live call.
- [ ] Call controls, privacy settings and authorization are tested on supported Android versions.

## 11. Implementation progress — prototype

The repository now contains an experimental authenticated REST call-signaling prototype:

- `server/voice_call_control.py` implements one-to-one private-call authorization, ringing timeout, accept/reject/cancel/end, connecting/connected state, ordered SDP/ICE signal storage and participant-only signal retrieval.
- SQLite schema version 5 stores call lifecycle rows and signaling events.
- HTTP routes expose call creation, state lookup, active call lookup, state actions and signaling submission/retrieval. Signaling requires the existing authenticated Bearer principal; the server derives the caller and enforces caller-offer/callee-answer roles.
- `MessengerHttpClient` exposes the REST call and signaling operations.
- `VoiceCallSession` guards local UI state transitions.
- The Collective Room exposes call invite/accept/reject/end/refresh controls for a linked private conversation of exactly two AI_IDs.
- Automated tests cover lifecycle, membership, participant authorization, timeout, role restrictions and signal payload validation.

### What this implementation does NOT do

- It does not create an Android `PeerConnection`, capture microphone audio for a call, play remote WebRTC audio, or transmit media.
- The UI intentionally labels the call as signaling-only and does not claim CONNECTED audio.
- It does not implement WebSocket/push or incoming-call background notification. Participants must refresh the call manually.
- It does not provision STUN/TURN. Direct connectivity and relay connectivity are not available until those services and the media client are implemented.
- It does not connect an external AI model/provider audio session.

Evidence boundary: call lifecycle and signaling prototype implemented in source. WebRTC media, microphone-to-peer transmission, remote playback, STUN/TURN, background incoming-call delivery and physical end-to-end call remain NOT IMPLEMENTED / NOT TESTED.
