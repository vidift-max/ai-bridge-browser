# AI Tool Bridge

An external AI may use tools only when the provider exposes an authorized interface.

The bridge should expose capability discovery, authentication requirements, tool invocation contracts, schemas, permission scope, and error/rate-limit handling.

Undocumented or unauthorized tool calls must be rejected.
