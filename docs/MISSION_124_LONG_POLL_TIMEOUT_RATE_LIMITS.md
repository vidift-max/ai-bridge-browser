# Mission 124 — Long Poll Timeout and Rate-Limit Verification

## Objective
Verify bounded wait behavior, prompt wake-up on message arrival, sequence cursor
paging, at-least-once redelivery, ACK removal, and per-principal rate limiting
through the actual HTTP handler.

## Ten rounds
1. Confirm M123 push and pull_request workflows each completed with 4/4 SUCCESS.
2. Inspect the Long Poll wait loop, cursor semantics, ACK path, and sliding-window limiter.
3. Create an isolated M124 branch from the final M123 commit.
4. Build a loopback-only HTTP fixture with temporary SQLite and synthetic AI credentials.
5. Verify an empty Long Poll waits for its configured duration within a bounded tolerance.
6. Verify a message arriving during a wait wakes the request before its deadline.
7. Verify future cursors, maximum batch size, and single-item cursor paging.
8. Verify unacknowledged delivery is stable across polls and ACK prevents later redelivery.
9. Verify rate-limit exhaustion returns HTTP 429 and budgets are isolated per AI principal.
10. Verify concurrent requests cannot exceed a one-event budget, register tests in CI,
    document evidence boundaries, open a Draft PR, and await CI.

## Coverage
The test module server/test_mission_124_long_poll_timeout_rate_limits.py adds ten local
HTTP integration tests. All requests target an ephemeral 127.0.0.1 listener. The
database is a temporary SQLite file and all bearer credentials are synthetic.

## Safety boundaries
- HTTP Long Poll remains the only realtime transport.
- No WebSocket/SSE, external network, Render service/deploy, real secrets, real
  AI message/ACK, paid resource, physical activation, or merge is performed.
- Tests verify application behavior in local CI only; they do not prove a real
  AI-01/AI-02 device exchange.
