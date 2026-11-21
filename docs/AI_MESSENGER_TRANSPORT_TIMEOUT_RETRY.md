# AI Messenger — Timeout and Retry Contract

This document defines a bounded contract only. It does not implement a remote provider retry loop.

## Defaults

- request timeout: 10 seconds;
- maximum configured timeout: 120 seconds;
- retry limit: 2;
- maximum configured retries: 5.

## Retry safety

Automatic retries are permitted only for operations that remain idempotent under the existing message/clientRequestId contract. A retry must reuse the same client request identity rather than create a new logical message.

ACK operations must remain idempotent. A timeout is not evidence that a message was not accepted; the client must reconcile using the operation's idempotency identity before creating another logical message.

## Hosted boundary

The current server has bounded configuration values but no claim of a production-grade distributed retry queue, network transport policy, or provider adapter. Those remain future work after hosted authentication and authorized provider integration.
