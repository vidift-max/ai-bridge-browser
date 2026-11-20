# Browser Foundation Architecture

This phase builds the browser before remote control, external AI access, or audio.

Layers:
1. App shell and lifecycle
2. Tab registry and tab state
3. Navigation/WebView surface
4. Durable browser state
5. User safety controls
6. Future control/integration layers

Rules:
- No remote control implementation in the foundation.
- No provider credentials.
- No DOM auto-submit.
- No audio capture.
- Every future layer must consume explicit contracts from this foundation.
