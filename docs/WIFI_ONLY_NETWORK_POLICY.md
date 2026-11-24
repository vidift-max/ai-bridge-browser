# Wi-Fi-only network policy

The AI Bridge Browser must not fall back to cellular data. The optional browser-side gate in `web/wifi-only.js` is deliberately fail-closed:

- A network action is allowed only when the browser reports `navigator.onLine === true` AND the Network Information API reports `connection.type === "wifi"`.
- `unknown`, `cellular`, `ethernet`, offline, or any other value blocks the action.
- If the browser does not expose a trustworthy connection type, the gate blocks downloads instead of guessing.
- The module makes no requests, loads no model, and stores no prompts, tokens, or network data.
- A future model loader must call `window.AIBridgeWifiOnly.assertAllowed()` immediately before every download/request and must separately require a deliberate user click before downloading model weights.
- A Wi-Fi pass is not permission to download automatically. Model size, storage needs, and estimated transfer must be shown and confirmed first.
- If Wi-Fi is lost or the reported connection changes, in-progress model transfer must be aborted by the future loader.

## Current implementation boundary

This commit adds only the reusable network gate. It does not integrate WebLLM or Transformers.js, choose a model, download weights, or perform inference. The gate's `WIFI_READY` status means only that the browser reports Wi-Fi; it does not prove that a model is available or that the device can run it.

## Manual verification still required

Android Chrome and the target tablet must be tested on:
1. Wi-Fi connected and reported as `wifi`.
2. Mobile data only (`cellular`) — must block.
3. Offline — must block.
4. Browser/API that does not expose connection type — must block.
5. Switching from Wi-Fi to mobile data during a future download — transfer must stop.

Some browsers do not expose the connection type. In that case this strict policy intentionally makes model downloads unavailable until a reliable Wi-Fi-only mechanism exists. No cellular fallback is permitted.
