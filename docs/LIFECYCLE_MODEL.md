# Activity Lifecycle Model

Leaving the app pauses automation. Returning does not silently resume automation.

Current lifecycle states:
- RUNNING
- PAUSED
- RECOVERING

The user must explicitly resume after recovery. This protects tablet use from unexpected automated actions.
