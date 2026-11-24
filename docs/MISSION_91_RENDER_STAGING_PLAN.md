# Mission 91 — Render Staging Plan Boundary

## 10-round execution record

1. Revalidated PR #90 as Draft and confirmed its staging Blueprint was based on M89.
2. Created the M91 branch from the M90 HEAD without merge, reset, or force-push.
3. Registered a separate Render Blueprint named **AI Bridge Browser Staging M91** in the existing Render workspace.
4. Configured the Blueprint to read `render.staging.yaml` from the M91 branch with auto-sync disabled.
5. Requested an initial Render infrastructure plan.
6. The initial plan exposed a paid boundary because the first Blueprint revision requested a Starter web service and persistent disk.
7. Removed the paid Starter plan and persistent disk from `render.staging.yaml`.
8. Switched staging to Render **Free** with ephemeral SQLite in `:memory:` and removed unnecessary OpenAI variables from this invitation-only staging plan.
9. Replanned successfully: Free web service, Oregon, no persistent disk, and only AI-01/AI-02 messenger tokens as manual secrets.
10. Updated the activation tests and reran CI; the final M91 CI set passed.

## Current staging contract

- Render plan: **Free**.
- Storage: **ephemeral**; `MESSENGER_DB_PATH=:memory:`.
- Persistent disk: **none**.
- Auto-sync: disabled in the isolated Blueprint.
- Manual secrets: `MESSENGER_TOKEN_AI_A` and `MESSENGER_TOKEN_AI_B` only.
- AI identities: AI-01 and AI-02.
- No production resources are referenced.
- No physical AI-PHONE is activated by this mission.

## Activation boundary

M91 prepared the infrastructure plan but did **not** approve the Blueprint, create a public service, or deploy it. A later mission may apply this reviewed Free plan only after explicit user authorization. Real runtime credentials must never be invented or committed.

## Safety

The Free plan does not provide durable SQLite persistence across instance replacement/redeploy. It is suitable only for the controlled staging browser/invite test while the instance remains available; it is not a production persistence strategy.
