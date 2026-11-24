# Mission 84 — Read-only production readiness configuration check

## Purpose
Provide an operator-safe check that validates the production Firebase configuration without contacting Firebase, creating resources, sending messages, or attempting an acknowledgement.

## Command
Set the six required environment variables used by the first-contact runner, then execute:

`python tools/firebase_first_contact_smoke.py --config-check`

The command validates required values, distinct AI identities, safe identity/conversation identifiers, and a production Firebase HTTPS database URL. Production URLs may not contain credentials, query strings, fragments, nested paths, or non-standard ports.

## Output semantics
A successful result reports:
- `CONFIGURATION_VALID`: local values passed syntax and presence checks only.
- `PRESENT_NOT_VERIFIED`: ID token strings exist; token validity and expiry were not checked.
- `network_check=NOT_RUN`: no Firebase request was made.
- `identity_provisioning=NOT_VERIFIED` and `conversation_membership=NOT_VERIFIED`: remote state is unknown.
- `message_send=NOT_RUN` and `acknowledgement=NOT_RUN`: no message or ACK was created.

The report never contains token values. A successful config check is not a production readiness approval and is not proof of live AI-01 ↔ AI-02 communication.

## Safety
- `--config-check` cannot be combined with `--send` or `--allow-production-send`.
- Production sends still require `--send`, `--allow-production-send`, and `MESSENGER_FIREBASE_ALLOW_PRODUCTION_SEND=true`.
- Emulator round-trip coverage remains isolated to the loopback Firebase Emulator.
- No production credentials, production Firebase network requests, rules publication, physical devices, or deployment are used by this mission.

## Validation
Unit tests cover report redaction, explicit NOT_RUN states, no-network behavior, and rejection of custom production ports/nested paths. CI also reruns the Firebase Auth/RTDB Emulator round-trip and existing rules/HTTP regression suites.
