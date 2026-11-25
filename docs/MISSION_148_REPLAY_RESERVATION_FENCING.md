# Mission 148 — Replay Reservation Fencing

## Ten-round scope

1. Revalidated M147 PR #148 and its final CI result.
2. Created an isolated M148 branch from the verified M147 HEAD.
3. Audited replay reservation expiry while a provider call remains in flight.
4. Identified a race: an expired first attempt could later fail and unconditionally delete a newer attempt's reservation for the same principal/request ID.
5. Replaced timestamp-only replay entries with timestamp plus unique reservation-owner token.
6. Made expiry cleanup read the timestamp from the reservation record.
7. Made provider-failure cleanup conditional on ownership of the current reservation token.
8. Added a deterministic threaded regression test that expires the first attempt, admits a second, then releases the first to fail.
9. Added dedicated CI and this evidence-boundary document.
10. Opened a Draft PR without merge, deployment, paid provider calls, or device activity.

## Correctness invariant

A provider attempt may release only the replay reservation it created. An expired attempt that finishes late must not remove a newer reservation that now occupies the same replay key.

The test uses events and a controlled clock to force the interleaving; it does not rely on arbitrary sleeps.

## Evidence boundary

Automated tests use fake providers. This change does not prove live provider inference, deployed service behavior, or physical AI-to-AI communication. No API key, paid call, deployment, device activation, private browser session access, or merge was performed.
