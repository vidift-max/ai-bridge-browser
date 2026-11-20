# Loading Model

Navigation is asynchronous.

The browser must wait for page readiness before any future automated delivery. A queued action must remain queued while a page is loading.

No timeout may silently discard a queued action. Recovery and cancellation are separate decisions.
