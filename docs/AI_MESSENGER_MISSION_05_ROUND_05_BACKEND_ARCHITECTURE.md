# Mission 05 — Round 05 — Backend Architecture Foundation

Free-first backend direction:

Android Messenger
  -> authenticated transport
  -> Messenger service
  -> durable message store / queue
  -> recipient session

Initial backend responsibilities:
1. authenticate the session;
2. derive sender AI identity from authentication;
3. authorize conversation membership;
4. validate message envelope;
5. enforce idempotency;
6. assign server ordering metadata;
7. queue pending delivery;
8. record delivery/acknowledgement events.

The Android app must not connect directly to a database.

The first backend implementation should remain a small service with a replaceable transport mechanism. HTTP polling is acceptable for the first real integration if it keeps the system simple; WebSocket can follow after authenticated delivery is proven.

No backend service is deployed by this round.
