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


## Follow-up verification: GPT-Live primary WebSocket

A second official-documentation pass on 2026-11-23 verified that GPT-Live is a distinct, documented server-side option. This section supplements the Realtime research above; it does not replace or silently change the original recommendation.

Official references:
- GPT-Live WebSocket guide: https://developers.openai.com/api/docs/guides/voice-websockets
- GPT-Live primary WebSocket reference: https://developers.openai.com/api/reference/resources/live/primary-websocket
- GPT-Live session management: https://developers.openai.com/api/docs/guides/live-conversations

Confirmed protocol details:
- Connect to `wss://api.openai.com/v1/live/sessions` with `Authorization: Bearer $OPENAI_API_KEY`; no query parameters.
- Send `session.start` first and wait for `session.started` before sending audio or application commands.
- The model shown in the official example is `gpt-live-1.1`.
- Select the audio format at session startup. The same format applies to input and output for that WebSocket session.
- Supported documented formats: mono signed PCM16LE at 24 kHz or 16 kHz; G.711 PCMU or PCMA at 8 kHz.
- Audio is raw bytes Base64-encoded in JSON events; do not include a WAV/container header. PCM16 chunks must have even byte length and preserve continuous ordering.
- Input event: `session.input_audio.append`.
- Output audio event: `session.output_audio.delta`; decode and queue deltas in delivery order.
- The guide explicitly says the primary WebSocket output has no timing fields and no output-audio-done event. Do not invent or wait for `session.output_audio.done`.
- Close using `session.close` and wait for `session.closed` before releasing the connection.
- The API key remains on the trusted backend. The official guide recommends WebRTC for GPT-Live audio connections, including server-to-server; WebSocket is supported as an alternative.

Architecture implications for this project:
1. GPT-Live WebSocket is a valid backend-owned digital-audio candidate, but the current report's event list must be corrected: do not assume `session.output_audio.done` exists.
2. Because the documented Live flow manages continuous listening/speaking, exact A/B turn boundaries and deterministic completion need a separate coordinator strategy. Transcript fragments are not a reliable substitute for a definitive audio-drained event.
3. Realtime and GPT-Live must remain separate adapters with separate event parsers, session lifecycle handling, and capability declarations.
4. No API call was made, no credentials were used, and no paid session was opened.

Updated assessment:
- GPT-Live API availability and PCM16/24 kHz transport: DOCUMENTED.
- GPT-Live exact strict turn-completion signal for an audio relay: NOT ESTABLISHED by the primary WebSocket guide; requires further design/validation.
- Realtime remains a strong candidate when explicit response lifecycle control is required.
- Final provider choice remains OPEN until the second AI provider's input/output contract is known and cost authorization is resolved.
