# Future Control Seam

A future remote-control layer may request an action against a stable tab ID.

The foundation will expose only state and lifecycle boundaries. It will not grant unrestricted WebView access.

Every future action must carry:
- target tab ID
- action type
- authorization context
- request ID
- audit record
