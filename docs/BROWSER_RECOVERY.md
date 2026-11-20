# Browser Recovery

Recovery restores durable browser structure first.

Order:
1. restore persisted tab records
2. recreate WebViews
3. load persisted URLs
4. wait for readiness
5. restore visible UI state
6. remain paused if lifecycle recovery requires explicit RESUME

No remote action is replayed merely because a tab was restored.
