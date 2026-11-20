# AI Bridge API — Message Lifecycle

CREATED -> STORED -> QUEUED -> DELIVERED -> ACKNOWLEDGED

Failure paths:
QUEUED -> RETRYING -> QUEUED
DELIVERED -> ACK_TIMEOUT -> QUEUED

A message is not considered completed merely because the provider session received a transport event. The participant adapter must acknowledge receipt, and application-level completion is a separate state.

The browser must never silently discard a queued message because a tab is loading, paused, or temporarily disconnected.