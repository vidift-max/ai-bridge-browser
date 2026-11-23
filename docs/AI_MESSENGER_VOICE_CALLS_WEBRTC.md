# AI MESSENGER — Wi-Fi Voice Calls and WebRTC Contract

Status: ANDROID AUDIO-ONLY PEER ENGINE + FOREGROUND APP SIGNALING ORCHESTRATION IMPLEMENTED IN SOURCE; PHYSICAL NETWORK E2E PENDING
Mission: Android WebRTC media foundation
Repository: `vidift-max/ai-bridge-browser`

## 1. Purpose and evidence boundary

Specify voluntary, authenticated, real-time voice calls between authorized AI-PHONE participants over the internet. Wi-Fi is supported, but no SIM card, carrier telephone number or PSTN service is required.

The backend remains authoritative for membership, call state, caller/callee identity and permission checks. GitHub stores source/specifications, not live signaling or persistent call sessions.

## 2. Transport architecture

- WebRTC carries real-time audio media between call endpoints using DTLS-SRTP.
- The authenticated backend exchanges SDP and ICE signaling through the existing HTTPS REST routes.
- ICE server configuration is injected by the application; no public STUN/TURN endpoint is silently selected.
- With an empty ICE server list, the engine can gather host candidates only. Connectivity across NATs or different networks is not promised.
- TURN relay capacity, bandwidth and operations may require infrastructure and costs. TURN must be provisioned and tested separately before claiming broad internet reachability.
- Video is explicitly disabled in the audio constraints.

## 3. Android media engine

The Android app pins `io.github.webrtc-sdk:android:150.7871.08` from Maven Central. The library is a precompiled Android WebRTC SDK; the upstream repository documents the Maven coordinate and package usage: https://github.com/webrtc-sdk/android

`WebRtcVoiceEngine` now provides:
- explicit RECORD_AUDIO permission gate; it never requests permission itself;
- one PeerConnection with Unified Plan semantics and caller-supplied ICE servers;
- local microphone AudioSource/AudioTrack creation;
- SDP offer/answer creation and local/remote description handling;
- ICE candidate callbacks and remote candidate insertion;
- remote audio track delivery to the application listener;
- local microphone enable/disable;
- idempotent close/disposal of PeerConnection, tracks, source, factory and audio device module.

`VoiceSignalPayload` validates and encodes the REST payload shape expected by the backend, including bounded SDP, ICE candidate metadata and end-of-candidates.

## 4. Signaling contract

- Caller sends `OFFER`; callee sends `ANSWER`.
- Each endpoint sends `ICE_CANDIDATE` events as candidates are gathered.
- `ICE_COMPLETE` is represented by an empty JSON object.
- Signal retrieval is cursor-based and the server returns only signals authored by the other participant.
- The app polls authenticated call state and signal cursors while the call screen is active.
- The client applies the remote description before adding queued ICE candidates; `VoiceIceCandidateBuffer` preserves arrival order and is cleared when the call ends.
- The caller creates an offer after server-side acceptance; the callee creates an answer after applying the offer.
- ICE `CONNECTED`/`COMPLETED`, not SDP exchange, triggers the server-side CONNECTED transition.

## 5. Consent, privacy and lifecycle

- The callee must explicitly accept each incoming call.
- The Android runtime permission remains under OS control. Denial prevents engine construction.
- Microphone transmission can be stopped locally through the audio track's enabled state; the call UI includes an explicit in-call mute/unmute control.
- No recording is created by this engine.
- Either endpoint must close the peer and disable the local track when a call ends, fails, is rejected or the Activity is destroyed.
- Leaving the call Activity stops local media immediately and attempts to terminate the server call; background audio continuity is intentionally not supported in this iteration.
- The application must not mark a call CONNECTED merely because an offer or answer was exchanged. It must wait for the WebRTC ICE connection to reach CONNECTED/COMPLETED and confirm server-side state.

## 6. Current implementation boundary

Implemented in source:
- REST call lifecycle and authenticated signaling server;
- Android PeerConnection factory, audio source/track, SDP offer/answer and ICE candidate exchange;
- call buttons connected to create/accept/reject/cancel/end actions and the foreground signaling poll loop;
- ordered buffering of ICE candidates until the remote SDP is applied;
- local microphone permission gate, microphone track transmission control and Android communication audio mode;
- bounded JSON payload codec and JVM tests for payload validation and ICE queue ordering (`VoiceSignalPayloadTest`, `VoiceIceCandidateBufferTest`).

Not yet implemented or proven:
- background/persistent incoming-call delivery and foreground-service audio continuity;
- explicit STUN/TURN configuration/deployment and relay fallback (current app passes an empty ICE-server list and gathers host candidates only);
- physical two-device audio test, cross-network connectivity, mute/route UX validation;
- external AI provider live audio adapter.

Therefore the source now contains an integrated foreground WebRTC call flow, but this is not yet evidence of working calls between physical AI-PHONEs. CI compilation/unit tests prove only source/build correctness, not microphone behavior, acoustic routing or network connectivity. Two-device E2E and STUN/TURN remain mandatory gates.
