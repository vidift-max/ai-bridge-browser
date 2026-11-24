# Mission 29 — Guest Room Web Messenger

## Scope
The browser guest portal now turns the authenticated, short-lived guest session into a minimal room messenger. It reuses the server's existing authenticated conversation, identity-directory, message-submit, pending-message, and acknowledgement endpoints.

## Authorization boundaries
- The client accepts exactly one room from the authenticated conversation listing and fails closed for zero or multiple rooms.
- The server remains authoritative: every directory read, message read, message submission, and acknowledgement is authenticated and checked against conversation membership.
- The sender identity comes from the bearer credential on the server; the browser-supplied sender field is only a consistency claim.
- Outbound messages target only the other members returned for the authorized room.
- The interface renders message bodies and participant labels with textContent, never HTML interpolation.
- Session bearer remains in JavaScript memory only; no persistent browser storage or URL token.

## Behavior
- Displays the room identity and participant directory.
- Polls pending messages every four seconds and acknowledges each received message.
- Sends bounded text messages with idempotency identifiers.
- Stops polling and requests session revocation on logout or page teardown.

## Limitations
- Polling is not WebSocket or push delivery.
- No attachments, voice calls, typing indicators, delivery receipts, or multiple-room switching are included.
- Guest identity/provider claim is not verified by ChatGPT, Gemini, Claude, Kimi, or any external provider.
- A green CI run is not a deployment or a real external AI conversation. HTTPS and a same-origin deployment are required for real-world use.
