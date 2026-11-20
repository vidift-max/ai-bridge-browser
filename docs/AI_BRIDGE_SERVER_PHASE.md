# AI Bridge Server Phase

The server will be a separate service from the Android browser.

Initial implementation target:
- HTTPS API;
- authenticated participant sessions;
- room membership;
- durable messages;
- recipient delivery state;
- reconnect recovery;
- audit events.

The first server milestone will provide provider-neutral messaging only. Provider-specific adapters are enabled only after the transport and authorization contracts are tested.