# AI Control Center Registry

The first control-center slice is a provider-neutral in-memory registry for 2–6 active AI tabs (maximum six). Each panel is bound by stable tabId and profileId, never by visual position.

Each panel owns an independent response state and two-line response tail, outgoing-message field, context observation state, and report-confirmation state.

Starting a new outgoing message clears only that panel's previous response tail and report confirmation. A response can be marked complete only after the caller has observed the response lifecycle. Report confirmation is separate and cannot be inferred from response completion.

Context states include UNKNOWN, NORMAL, CRITICAL, FULL, NEW_CHAT_REQUIRED, and NEW_CHAT_LOADING. These are observations/contracts only: this model does not inspect ChatGPT DOM, click controls, send messages, infer token usage, or open a new chat.

This is an initial model, not a functioning UI or remote automation integration. WebView capture and control require a separately implemented, tested, and policy-compliant adapter.