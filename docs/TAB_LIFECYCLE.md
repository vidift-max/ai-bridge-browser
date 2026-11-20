# Tab Lifecycle

States:
- CREATED
- LOADING
- READY
- ERROR
- PAUSED
- CLOSING

A tab can only receive future automated actions after it reaches READY and the action is authorized.

Closing a tab is a user action protected by the lock state.
