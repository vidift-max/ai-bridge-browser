# Persistence Boundary

Durable browser persistence stores browser metadata and pending mission/message identity.

WebView instances, credentials and arbitrary page DOM are not persisted.

The current implementation uses SharedPreferences; atomic-file durability is a later hardening task.