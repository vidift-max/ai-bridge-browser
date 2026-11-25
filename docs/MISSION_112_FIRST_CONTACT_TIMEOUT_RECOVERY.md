# Mission 112 — First-contact timeout recovery

## Ten-round execution record

1. Verified M111 run 45542087345 completed with SUCCESS across backend, Android, browser and activation-boundary jobs.
2. Re-read the first-contact runner and confirmed M111 created stable message/request IDs but deliberately stopped after an ambiguous POST result.
3. Defined the recovery boundary: only message submission may be replayed; identity, Long Poll receive, ACK and pending checks are never automatically retried by this helper.
4. Added a bounded submit helper that treats transport failure (status 0) and HTTP 5xx as ambiguous outcomes.
5. Limited recovery to exactly one replay; both attempts reuse the same payload object, messageId and clientRequestId.
6. Kept HTTP 4xx responses terminal and non-retryable, avoiding retries for authorization, validation or other client errors.
7. Added a terminal `message_submit_outcome_ambiguous` result when the second attempt is also transport-failed or 5xx; the helper never performs a third POST.
8. Added five tests for timeout recovery, 5xx recovery, stable payload reuse, bounded stop, 4xx no-retry and success no-retry.
9. Registered the new test module and M112 branch in the backend CI workflow; preserved Free/ephemeral/manual staging and HTTP Long Poll only.
10. Documented that the helper's safety relies on the backend idempotency contract validated in M111; no live service, real credentials or physical device was used.

## Recovery behavior

- First POST returns success: continue normally.
- First POST returns status 0 or HTTP 5xx: replay once with the exact same messageId/clientRequestId/payload.
- Replay returns success: continue normal receive/ACK/pending verification.
- Replay returns status 0 or HTTP 5xx: stop with `message_submit_outcome_ambiguous`; operator must inspect using the same operation ID. Do not generate a new operation ID.
- HTTP 4xx: stop without retry.
- No automatic retry is added to identity, receive, ACK or pending-check calls.

## Evidence boundary

The tests exercise deterministic fake transports and source-level backend idempotency. They do not prove network fault behavior against a deployed Render service or a real AI-01/AI-02 session. No deploy, secret creation, real message, paid resource, physical activation or merge occurred. HTTP Long Poll remains the only realtime transport.
