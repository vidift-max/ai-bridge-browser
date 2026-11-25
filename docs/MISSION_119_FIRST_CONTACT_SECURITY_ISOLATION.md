# Mission 119 — First Contact Security & Isolation Audit

## Scope and result
Ten-round security audit of the AI-01 → AI-02 first-contact path. This mission verifies distinct bearer identities, sender attribution, conversation membership, recipient-only delivery, recipient-only ACK, idempotency, credential redaction, and the realtime transport boundary.

## Ten rounds
1. Revalidated the M118 Draft PR and successful CI runs before changing the source branch.
2. Inspected credential hashing, registry lookup, generation checks, and authentication error handling.
3. Traced HTTP sender attribution: the bearer principal is authoritative; a conflicting claimed sender is rejected.
4. Traced conversation membership checks for pending reads, history, and transport capability reads.
5. Traced recipient scoping in pending/Long Poll and confirmed a room member who is not a recipient does not receive the message.
6. Traced ACK authorization and confirmed only an authenticated listed recipient can ACK.
7. Audited idempotent replay and found a payload-equivalence gap: message kind was omitted from the replay comparison.
8. Fixed the idempotency comparison so a replay with changed message kind returns `idempotency_conflict`; added regression coverage for body/recipient/kind changes.
9. Added HTTP/backend security regression tests and registered them in the staging activation CI workflow.
10. Documented the security boundaries and verified CI on the final commit.

## Verified boundaries
- AI-01, AI-02, and AI-03 synthetic credentials map to distinct principals.
- Sender identity is derived from the bearer token; a conflicting `senderAiId` claim is rejected.
- Conversation membership is required for pending, history, and transport capability access.
- Pending delivery is scoped to explicit recipients, not every room member.
- ACK requires recipient membership in the message recipient list; repeated ACK is idempotent.
- Idempotency now compares message ID, conversation, body, recipients, and message kind.
- HTTP Long Poll remains enabled; WebSocket and server push remain disabled.
- Authentication error responses do not echo bearer credentials.

## Validation
Run `python -m unittest server.test_mission_119_security_isolation -v` and the full workflow backend/browser/Android/activation-boundary jobs.

## Safety boundary
Tests use synthetic credentials and local loopback only. This mission does not create or deploy a Render service, configure real secrets, contact an external endpoint, send a real AI message, activate a physical device, purchase a paid resource, or merge a pull request. The PR remains Draft pending review. A passing CI run is not proof of a real AI-01/AI-02 network exchange.
