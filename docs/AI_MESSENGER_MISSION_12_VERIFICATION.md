# Mission 12 Verification and Security Notes

Automated target:
- credential ACTIVE authenticates;
- EXPIRED/REVOKED/ROTATED credentials do not authenticate;
- rotation produces a new generation for the same AI_ID;
- sessions expire independently of credential plaintext;
- authenticated HTTP POST is attributed to the authenticated AI_ID;
- a second AI can retrieve and acknowledge a message;
- SQLite restart recovery preserves message and acknowledgement state.

Security boundary:
- runtime credentials are not committed to GitHub;
- session registry is runtime-only;
- rotation is an application-level experimental mechanism, not a production key-management system;
- no unauthenticated public revocation endpoint is exposed;
- TLS remains mandatory before real network credentials are used.

Not proven by this mission: OAuth/OIDC, external identity provider, public deployment, production TLS, multi-instance concurrency, physical Android device, external AI provider, or internet AI-to-AI communication.
