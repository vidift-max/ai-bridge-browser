# Mission 123 — HTTP Long Poll Protocol Hardening

## Objective

Harden the HTTP Long Poll contract at the actual HTTP handler boundary. Prove strict
query validation, authentication, immediate and bounded delivery, cursor ordering,
and concurrent waiter behavior using only synthetic identities on loopback HTTP.

## Ten rounds

1. Re-verify M122's final pull-request CI: all four jobs passed on its final SHA.
2. Trace the existing Long Poll parser and handler, confirming the accepted fields
   are exactly after, limit, and timeout.
3. Create an isolated M123 branch from M122 without modifying the prior mission.
4. Add a temporary-SQLite HTTP fixture bound only to 127.0.0.1 with synthetic
   AI-01, AI-02, and non-member AI-03 credentials.
5. Verify missing, duplicate, and unknown query parameters fail closed with HTTP 400.
6. Verify signed, non-decimal, non-ASCII, oversized cursor, invalid batch limits,
   and excessive timeout values fail closed with HTTP 400.
7. Verify authentication is mandatory and a zero-second poll returns an empty
   successful response without waiting.
8. Verify a message already queued is returned immediately, and batch size plus
   sequence ordering are honored.
9. Verify the after cursor excludes earlier messages, concurrent waiters are
   notified and see the same unacknowledged item, and ACK removes it from later polls.
10. Register the suite in CI, document limits, open a Draft PR, and await every job.

## Coverage

server/test_mission_123_long_poll_protocol.py adds ten HTTP integration tests.
They use only synthetic bearer tokens, a temporary SQLite file, an ephemeral
listener on 127.0.0.1, and no external network.

## Safety and evidence boundaries

- HTTP Long Poll remains the only realtime transport; no WebSocket or SSE is added.
- No Render service/deploy, external network contact, real credentials, real
  message/ACK, paid resource, physical device activation, or merge is performed.
- Multiple concurrent polls are allowed to observe the same unacknowledged message;
  this is an at-least-once delivery contract, not exclusive queue consumption.
- A passing CI run proves the automated local contract only, not a real AI-01 to
  AI-02 exchange or activation of AI-PHONE-02.
