# AI Bridge API — Provider Adapters

The API uses adapters at the provider boundary.

An adapter translates the neutral room protocol into an interface that the provider explicitly permits, such as an official API or an authorized web session.

## Adapter boundary
AI Bridge API <-> Adapter <-> Provider

The adapter may report:
- provider type;
- session availability;
- delivery capability;
- rate-limit state;
- provider request identifier.

The adapter must not expose provider credentials to rooms or other participants.

No provider adapter is enabled by the current browser foundation.