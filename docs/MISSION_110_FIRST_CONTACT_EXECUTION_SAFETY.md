# Mission 110 — First-contact execution safety

## Ten-round execution record

1. Rechecked the M109 CI failure and isolated the issue to control-character test fixtures and the credential CR/LF predicate; retained the corrective commits on the M109 branch.
2. Verified that invalid conversation IDs and malformed credentials are rejected before the runner performs identity requests.
3. Created the M110 work branch from the corrected M109 head without merging or changing the prior PR.
4. Audited the command-line entry point and found that valid environment credentials alone could start a real first-contact sequence.
5. Added a mandatory `--execute` CLI argument; invocations without it stop before calling the runner.
6. Added a second explicit gate requiring `MESSENGER_FIRST_CONTACT_EXECUTE=true`; absent or false values stop before any request.
7. Audited urllib redirect behavior for bearer-token handling and replaced automatic redirect following with a handler that refuses redirects.
8. Added tests proving both execution gates are independently required and that execution starts only when both are present.
9. Added a local HTTP redirect regression test proving the destination is never contacted and the redirect response body is not echoed; registered M110 tests and branch filters in CI.
10. Documented the invocation boundary and preserved the operational stop: no live credentials, staging deployment, real message, physical device activation or merge.

## Controlled invocation

The runner now requires both:
- CLI: `python scripts/verify_first_contact.py --execute https://staging.example CONVERSATION_ID`
- Environment: `MESSENGER_FIRST_CONTACT_EXECUTE=true`

The two AI bearer tokens remain environment-only and are never written to Git or printed by the runner. Redirects are rejected. The command is still a real-send operation when explicitly enabled; do not run it until staging, identities, conversation membership and credentials have been independently authorized.

## Evidence boundary

M110 adds local execution safeguards and automated tests. It does not prove live staging, actual AI sessions, message delivery, ACK, or physical AI-PHONE-02 activation. HTTP Long Poll remains the only realtime transport. Staging remains Free, ephemeral and manual-deploy only.
