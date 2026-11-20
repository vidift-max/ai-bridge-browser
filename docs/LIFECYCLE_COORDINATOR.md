# Lifecycle Coordinator

Activity lifecycle events coordinate browser state transitions.

Background/stop transitions pause automation. Returning to the foreground does not silently resume it.

Lifecycle coordination must never grant remote control.