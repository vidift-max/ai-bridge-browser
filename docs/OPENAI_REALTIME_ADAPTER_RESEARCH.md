# OpenAI adapter research — digital AI audio bridge

Date: 2026-11-23
Status: DOCUMENTATION ONLY; no API call, credentials, service, or deployment created.
Target branch: `feat/digital-ai-audio-bridge-contract`
Base contract commit: `4871c374ea989ab6a1f69c3597284e6d8ef27de4`

## Official documentation reviewed

- Realtime getting started: https://developers.openai.com/api/docs/guides/realtime
- Realtime WebRTC: https://developers.openai.com/api/docs/guides/voice-webrtc
- Realtime WebSockets: https://developers.openai.com/api/docs/guides/voice-websockets
- Realtime conversations: https://developers.openai.com/api/docs/guides/realtime-conversations
- Client secrets reference: https://developers.openai.com/api/reference/resources/realtime/subresources/client_secrets/methods/create
- Create call reference: https://developers.openai.com/api/reference/resources/realtime/subresources/calls/methods/create
- Pricing: https://platform.openai.com/pricing/

## Confirmed OpenAI-side capabilities

1. The current official Realtime API exposes speech-to-speech sessions with audio input and audio output.
2. Current documented examples identify `gpt-realtime-2.1` as a Realtime model.
3. A Realtime session can be created using the unified WebRTC call endpoint `POST /v1/realtime/calls`, or by creating a short-lived client secret using `POST /v1/realtime/client_secrets`.
4. OpenAI recommends WebRTC for client-side/mobile connections. The standard API key must remain on a trusted backend; mobile client should receive only a short-lived client secret if that flow is selected.
5. For a backend-owned audio stream, official WebSocket transport is supported. Audio is sent/received as audio events over the server connection.
6. Realtime session state and audio turn events are separate from the user's existing ChatGPT consumer conversation. This adapter would create a new API session; it does not attach to this ChatGPT chat.

## Important architecture decision for digital AI-to-AI audio

The existing Android `WebRtcVoiceEngine` is a microphone-to-peer-call engine. It is not, by itself, a digital audio injection/relay implementation for an AI provider.

For a server-mediated bridge, the most direct candidate is:
- backend owns OpenAI Realtime WebSocket session and provider credentials;
- backend receives audio payload from the other provider's adapter;
- backend sends it as documented Realtime input-audio events;
- backend receives OpenAI generated audio output events;
- backend relays those bytes to the other provider's supported audio-input API.

This is a candidate architecture only. The exact audio event schema, PCM framing, sample rate, and turn-finalization behavior must be pinned against the selected GA API reference and the other provider's input format before implementation.

A mobile-to-OpenAI WebRTC session remains an alternative, but routing arbitrary remote provider audio into its local audio track requires a verified native custom-audio source path; the existing microphone-backed engine does not prove that capability.

## Billing and zero-cost guardrail

OpenAI Realtime API usage is paid. The official pricing page currently lists Realtime audio token rates and GPT-Live session rates; prices vary by model and modality. Therefore:
- OpenAI API adapter remains disabled by default.
- No API call or billable session was initiated during this research.
- No API key was requested or stored.
- No paid usage is authorized.
- Do not promise a zero-cost voice bridge using OpenAI Realtime.

A free implementation can still proceed through simulator adapters and test fixtures, but real OpenAI audio integration cannot be activated under the current zero-cost restriction unless the user explicitly authorizes a budget.

## Integration gates still open

- Obtain second provider/model/API report.
- Confirm second provider accepts programmatically supplied audio and returns audio, rather than only accepting microphone capture in its consumer UI.
- Confirm compatible audio formats, sample rates, chunking, turn completion, session duration, and authentication.
- Choose a server deployment only after user authorizes one; no hosting provider is assumed.
- Decide whether user permits paid OpenAI API usage. Until then, OpenAI live adapter stays disabled.
- Implement provider adapters and tests only after the two-provider interface is known.

## Verdict

OpenAI side: API capability confirmed; current ChatGPT session is not directly attachable; Realtime API is a separate paid API session.
Bridge: BLOCKED for real two-provider audio until the second provider contract and cost/hosting authorization are known.
APK: no new binary generated.
