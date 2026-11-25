# Mission 168 — Browser VM AbortController Test Context

## Finding

The inherited browser CI jobs use Node.js 22, where `AbortController` is available globally. The failures were not caused by a missing Node runtime feature.

`web/ai-conversation-loop.test.mjs` executes the browser-oriented controller source with `vm.runInNewContext(source, scope)`. A new VM context has its own global scope and does not automatically inherit Node's global `AbortController`. The production code correctly uses the browser global, but the test sandbox previously supplied only `window`, causing `ReferenceError: AbortController is not defined`.

## Fix

Both VM contexts in the test file now explicitly inject the runtime's `AbortController` constructor:

```js
const scope = { window: {}, AbortController };
vm.runInNewContext(source, scope);
```

This keeps the production controller unchanged and makes the test environment accurately provide the browser API dependency it exercises. The existing stop, abort, overlapping-run, provider-failure, and context-change tests exercise the behavior.

## Verification

The dedicated workflow pins Node.js 22, verifies that the runtime exposes `AbortController`, runs the conversation controller tests, and then runs the full `web/*.test.mjs` suite.

## Boundary

This is a test-harness correction only. It does not alter browser runtime code, provider integrations, Messenger networking, production services, or AI-to-AI connectivity.
