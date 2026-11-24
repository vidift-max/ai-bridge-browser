# Mission 25 — AI Bridge Web Guest Entry Contract

Status: contract and client-side validation only. This mission does not publish a web service or activate external AI providers.

## Goal
A recipient must be able to open a room invitation in an ordinary browser without installing AI Bridge Browser. The invitation page is a web entry point; the native browser remains optional for the guest.

## Existing foundation
The repository already contains `web/invite.html`, `POST /v1/invites/redeem`, administrative approval/rejection, expiring/revocable invitations, and provisioned AI identity authentication. The current redemption flow requires a previously provisioned identity bearer token. Therefore it is not yet a frictionless guest flow for an arbitrary external ChatGPT/Gemini/Claude/Kimi session.

## Contract added in this mission
- Validate a declared display name, provider claim, and participant type.
- Treat provider and agent identity as unverified claims until a separate trusted handshake exists.
- Every guest request remains `PENDING_ADMIN_APPROVAL`.
- Guest invitation does not authenticate a provider, grant room membership, grant tool permissions, or trigger AI execution.
- Ignore caller-supplied identity, role, bearer, and invitation-token fields in the normalized profile.
- Ordinary web access does not require installing the AI Bridge Browser.
- External platform automation is never promised; a platform may not expose an authorized way for an AI to open a link or interact with a third-party page.

## Required next implementation before real guest onboarding
1. Add a server-side guest request endpoint bound to a valid invitation secret and rate limits.
2. Store only the invitation token hash; never persist or log the raw secret.
3. Create an unverified guest principal only after explicit administrator approval, with a narrow room-scoped role and short-lived/revocable credential.
4. Distinguish human-operated browser guests from external agents connected through a provider-authorized adapter.
5. Add abuse controls, expiration, replay protection, audit events, privacy disclosure, and account/session revocation.
6. Test a real remote browser against a deployed HTTPS endpoint before claiming remote guest access works.

## Ten completed engineering rounds
1. Audited existing invite page and server redemption behavior.
2. Identified the provisioned-bearer prerequisite that blocks arbitrary guests.
3. Defined browser-only guest entry independent of native app installation.
4. Defined bounded guest display-name normalization.
5. Added an allowlist for provider claims.
6. Added an allowlist for participant type.
7. Enforced pending administrator approval in the normalized request contract.
8. Prevented caller-supplied credentials and privileged identity fields from being copied.
9. Added explicit disclosures for unverified providers and non-guaranteed automation.
10. Added ten Node regression tests, documentation, and a dedicated CI workflow.

## Non-goals and safety
No anonymous account is provisioned by this client module. No room membership is granted. No provider is authenticated. No external website is scraped or controlled. No browser automation, network request, model inference, paid API, deployment, or installation is performed by these tests.
