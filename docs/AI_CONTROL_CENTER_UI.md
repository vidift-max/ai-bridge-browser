# AI Control Center UI

## Included in the browser shell
- A dedicated "Central IA" view can be opened from the browser controls and toggled back to the WebView area.
- The view renders six individual AI panel slots.
- Registered browser tabs are associated with panel identities and display response/context states.
- Selecting a populated panel returns to its bound browser tab.
- A separate GPT-6 coordination text box is displayed below the six panel slots.

## Current limits
- The GPT-6 box is currently a UI input only; it is not connected to this assistant or a remote orchestration service.
- Panel response/context values are model state and are not yet updated by live WebView observation.
- No mission dispatch, automatic message submission, DOM extraction, context-window measurement, external AI provider adapter, or background orchestration is active.
- Panel association is local to the browser process; it is not a proof of isolated provider accounts or authenticated AI identities.

## Next integration steps
1. Persist coordinator drafts and panel registry state safely.
2. Connect each panel to its own WebView observation lifecycle.
3. Add an explicit mission review/approval gate before dispatch.
4. Connect the coordinator input to a durable mission/event service only after its authorization model is implemented.
