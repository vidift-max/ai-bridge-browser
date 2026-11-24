# Mission 101 — First-contact verification runner

## Ten-round execution record

1. Revalidated the M100 baseline and CI run #38 (`45496978093`): SUCCESS, all four jobs successful.
2. Inspected the existing identity endpoint and confirmed the server reports the authenticated `aiId` without accepting a caller-supplied sender identity.
3. Inspected the actual HTTP Long Poll route: `GET /v1/conversations/{conversationId}/messages/wait`.
4. Inspected the actual send and ACK routes: `POST /v1/messages` and `POST /v1/messages/{messageId}/ack`.
5. Added `scripts/verify_first_contact.py` to verify two distinct bearer credentials resolve independently to AI-01 and AI-02.
6. Implemented a concurrent recipient Long Poll followed by sender submission, checking the exact message ID, conversation, authenticated sender and body.
7. Added recipient-only ACK verification and a post-ACK pending check; the runner returns PASS only when the message is no longer pending.
8. Added credential-redaction behavior: tokens are read only from environment variables and are never emitted; HTTP error response bodies are not echoed.
9. Added seven focused unit tests for credential separation, identity mismatch, successful end-to-end protocol, wrong recipient, message mismatch, missing ACK removal, and malformed response handling.
10. Wired the tests and Python compilation into the existing CI workflow and added this mission's branch to push/PR triggers.

## Local invocation (only after staging is explicitly authorized)

Set `MESSENGER_TOKEN_AI_A` and `MESSENGER_TOKEN_AI_B` as private environment variables, then run:

```sh
python scripts/verify_first_contact.py https://<staging-host> <conversation-id>
```

The command does not create credentials, create conversations, deploy services, or activate devices. The conversation must already exist and include AI-01 and AI-02. Never pass tokens as command-line arguments.

## Safety and evidence boundaries

- Staging activation/deployment remains NOT AUTHORIZED and NOT PERFORMED.
- No Render service, secrets, paid resources, persistent disk, or payment information was created or used.
- No merge; PR remains Draft with `maintainer_can_modify:false`.
- No real AI sessions, physical devices, or actual AI-01 ↔ AI-02 contact were exercised by this code-only mission.
- The runner's tests use a controlled fake HTTP transport; they prove the verifier's logic, not a deployed service.
- The M100 Free staging profile remains ephemeral and suitable only for a short controlled test, not production durability.