# Browser State Model

`BrowserState` is the small in-memory model for tab identity, active tab and pause state.

It does not contain WebView objects, credentials, provider adapters, remote commands or audio state. This keeps the browser model testable and independent from Android view lifecycle.