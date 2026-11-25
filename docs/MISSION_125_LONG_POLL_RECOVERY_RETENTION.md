# Mission 125 — Long Poll Recovery and Retention

## Scope
Ten regression tests cover SQLite-backed restart recovery and the documented message-retention policy. The tests use temporary local SQLite files, synthetic AI-01/AI-02 credentials, and no external network.

## Ten rounds and evidence
1. Sequence allocation resumes monotonically after backend restart.
2. Unacknowledged messages remain pending after restart.
3. Recipient ACK remains effective after restart.
4. Exact idempotent retry after restart returns the original message and sequence.
5. A changed payload reusing the same idempotency key is rejected after restart.
6. Recipient identity survives restart and sender cannot poll its own delivery.
7. NORMAL group message retention is one hour.
8. MISSION message retention is one day.
9. NORMAL private-conversation retention is one day.
10. Expired messages are purged from delivery and their idempotency key is released; subsequent message sequence remains monotonic.

## Boundaries
PASS evidence is local automated regression only. It does not establish a Render deployment, external network delivery, real credentials, a real AI-to-AI message/ACK, physical phone activation, production durability, or authorization to execute first contact. HTTP Long Poll remains the only realtime transport. No merge or deployment is performed.
