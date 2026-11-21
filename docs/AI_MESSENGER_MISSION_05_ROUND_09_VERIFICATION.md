# Mission 05 — Round 09 — Verification Checklist

Automated Android verification must cover:
- remote envelope required-field validation;
- session identity required-field validation;
- idempotency key validation;
- same/different payload fingerprint behavior;
- existing local-only message states remain separate from remote states.

CI success proves compilation/tests for the repository only. It does not prove a remote server, network delivery, authenticated external AI, or physical Android device.

Historical failures remain visible and are not overwritten by later green runs.
