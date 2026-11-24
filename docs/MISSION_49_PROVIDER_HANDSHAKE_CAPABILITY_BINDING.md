# Mission 49 — Provider handshake capability binding and resource bounds

## Objective

Ensure that an external provider handshake can authenticate only the capabilities explicitly granted by the trusted host, while bounding short-lived challenge and nonce state.

## Ten rounds

1. Confirmed Mission 48 PASS on its exact CI run and SHA.
2. Audited the existing provider handshake implementation and its trust boundary.
3. Identified that a provider response could claim any globally allowed capability, even if the host had not granted it for that session.
4. Identified unbounded pending-challenge and nonce tracking collections, plus an expiry-boundary comparison that accepted the exact expiry instant.
5. Created an isolated branch from the Mission 48 verified head; no merge or deploy.
6. Bound each challenge to a non-empty, unique, allowlisted capability grant supplied by the trusted host.
7. Rejected response capabilities that exceed the challenge grant; the proof verifier receives only the verified, granted claims.
8. Added bounded pending challenges (maximum 1,024), bounded nonce tracking (maximum 8,192), expiry pruning, and fail-closed capacity behavior.
9. Added tests for capability escalation, malformed grants, exact expiry, capacity limits, nonce reuse, and shutdown during asynchronous proof verification.
10. Added a dedicated CI workflow and this evidence/limitations document; PR remains Draft pending same-SHA CI.

## Security behavior

- A challenge must carry explicit allowedCapabilities supplied by the trusted host.
- Only READ_STATUS, SEND_MESSAGE, and REQUEST_RECONNECT are recognized.
- The response capability list must be non-empty, unique, and a subset of the challenge grant.
- Challenge expiry is enforced at now >= expiresAt.
- Pending challenges are capped at 1,024 by default; expired pending entries are pruned on issuance.
- Nonce tracking is capped at 8,192 entries. If capacity is exhausted before entries expire, issuance fails closed.
- A challenge is consumed before proof verification. A failed proof cannot be retried with the same challenge.
- Shutdown during asynchronous proof verification prevents a late authentication result.
- Audit events do not include nonce, proof material, provider credentials, or message bodies.

## Trust boundary and limitations

- The challenge capability grant must be created by a trusted host after applying user consent, room membership, and server-side policy. This module does not independently authorize a room member.
- verifyProof remains an injected trusted-verifier boundary. The default verifier rejects all proofs.
- Tests use deterministic nonce factories and fake proof verifiers; they do not prove real provider identity.
- No ChatGPT, Claude, Gemini, external browser account, OAuth credential, or provider public key was connected or accessed.
- No browser scraping, automated provider login, CAPTCHA/2FA bypass, or cookie extraction is implemented.
- This is protocol hardening, not a deployed provider connector or live GPT-6 connection.
- No paid API, merge, or deployment was activated.

## Validation

node --test web/ai-provider-handshake.test.mjs

The mission CI additionally runs the existing backend, browser, and Android regression suites on the exact final commit.
