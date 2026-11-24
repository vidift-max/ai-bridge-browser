# Mission 14 — Provider Connector & Authorized Session Handshake

## Ten rounds
1. Rechecked Mission 13 PR #11 and its corrected CI run; the initial test defect was fixed and a later run passed.
2. Created a separate branch from the Mission 13 adapter branch; no PR was merged.
3. Defined a provider-neutral, challenge-response handshake contract for a future trusted host adapter.
4. Added short-lived challenges scoped to session, provider, exact origin, audience, nonce and timestamps.
5. Added one-time nonce and challenge consumption to prevent replay.
6. Added an injected proof-verification boundary; authentication fails closed when no trusted verifier confirms proof.
7. Added capability allowlisting for READ_STATUS, SEND_MESSAGE and REQUEST_RECONNECT; arbitrary capabilities are rejected.
8. Added expiry, claim binding, revocation and shutdown behavior.
9. Added privacy-limited audit events that exclude nonce, proof, credentials and message content.
10. Added ten deterministic tests, a dedicated CI workflow and this integration contract.

## Security contract
A real connector must verify a provider-controlled cryptographic proof using a trusted verifier and an independently established provider key/identity. The test verifier is a stub and does not establish real provider identity. The protocol does not authorize browser scraping, automated login, CAPTCHA/2FA bypass, cookie extraction, or violation of provider terms.

## Current limits
- No ChatGPT, Gemini, Claude or other external provider has implemented this handshake in this repository.
- No provider public key, OAuth integration, account token or external credential is present.
- This is protocol groundwork only; it does not claim a real provider connector or live account connection.
- No physical device, real browser session or remote message was tested.
- No paid service, merge or deployment was activated.

## Validation
Run `node --test web/ai-provider-handshake.test.mjs`. Tests use a deterministic nonce factory and fake proof verifier; they validate protocol logic only.
