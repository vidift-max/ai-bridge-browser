# Mission 143 — Durable Provider State

## Objective

Strengthen the authenticated provider-to-Messenger path from Mission 142 with
durable request state, durable response/attestation linkage, recovery after
process restart, and an explicit per-AI provider identity binding contract.

## Ten rounds

1. Audited PR #143, current head, merge state, and workflow results.
2. Added SQLite schema v12 with a durable provider_request_records ledger.
3. Added store-level claim, completion, failure, and recovery operations.
4. Added persistence tests proving the ledger survives a SQLite reopen.
5. Added retry semantics for failed requests while preserving payload-digest conflicts.
6. Added authenticated backend access to provider request records and message recovery.
7. Changed the HTTP provider route to claim durable state before provider execution,
   cache completed responses, and reject payload changes for an existing request.
8. Added HTTP integration tests for cached replay, host-instance loss, and conflicts.
9. Added a per-AI provider identity binding contract that stores only credential
   references, never secrets.
10. Added dedicated Mission 143 CI covering the durable ledger, provider host,
    Messenger integration, and provider identity registry tests.

## Evidence boundary

- This mission does not prove live OpenAI/Claude/Gemini inference.
- It does not create or configure API keys, paid calls, provider accounts,
  browser cookies, or private ChatGPT sessions.
- Per-AI provider bindings are a reviewed configuration contract, not proof that
  separate provider accounts are actually connected.
- Durable request state prevents duplicate Messenger messages and permits a
  completed response to be recovered after provider-host process state is lost.
- A provider invocation that crashes after the durable claim but before completion
  may still be retried; exactly-once external provider execution cannot be claimed
  without a provider-side transaction/idempotency contract.
- HMAC attestations are now durably linked to the provider request record and
  message ID. They are still server-generated attestations; peer-side independent
  cryptographic verification is not claimed here.
- No merge, deployment, device activation, or production configuration was done.

## Current security posture

The HTTP route uses the authenticated bearer principal, exact two-member PRIVATE
room authorization, bounded request/response sizes, and the durable request
digest. A second request with the same principal/request ID and identical payload
returns the stored message/attestation without another provider invocation.
A changed payload for the same request ID is rejected with a conflict.

Paid provider calls remain disabled unless explicitly configured by deployment
operators. No such configuration was created during this mission.
