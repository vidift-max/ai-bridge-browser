# AI Messenger Android remote transport — Mission 38

## Implemented in this change set

- `MessengerRemoteConfig` validates HTTPS base URLs, provisioned AI_ID syntax, and a unique participant list with a maximum of 20 members.
- `MessengerHttpClient` provides authenticated HTTPS calls for:
  - `POST /v1/conversations` (PRIVATE or GROUP)
  - `POST /v1/messages`
  - `GET /v1/conversations/{conversationId}/messages?after={sequence}&limit={limit}`
  - `POST /v1/messages/{messageId}/ack`
- Request and response bodies are bounded; connect/read timeouts are set; bearer credentials are never placed in URLs.
- Android Messenger now has a setup screen that stores the bearer token through the existing Android Keystore-backed credential vault. Server URL and AI_ID are stored separately as non-secret configuration.
- Android unit tests cover HTTPS-only URLs, rejection of URL user-info, AI_ID validation, duplicate normalization, empty member rejection, and participant limits.

## API semantics

The current server only accepts identities already provisioned in its configured token map. Creating a conversation does not invite or provision a new AI. A private conversation must have exactly two members; a group may have 2–20. The authenticated creator must be included.

A successful message POST means **accepted by the server**, not confirmed delivered or read. A recipient obtains messages by polling the pending endpoint and then acknowledges each message. This client is synchronous and must only be called from a worker thread.

## Explicit remaining work / limits

- The current Android screen still has its original local-only conversation/message workflow. The secure remote connection form is present, but the complete remote create/send/poll/ack flow is not yet wired into the visible conversation controls.
- No live endpoint was configured or contacted during this mission.
- No backend deployment, external AI provisioning, push notifications, WebSocket, background polling, voice calls, WebRTC, or PSTN integration is claimed.
- Android CI is the next verification gate. Physical-device and cross-network tests remain required after a reachable staging endpoint and authorized credentials exist.

## Safety

Do not paste production credentials into source code, issue comments, or mission reports. Use HTTPS only. Do not infer AI identity from a display name or a local contact card.
