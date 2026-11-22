# Mission 42 — Messenger hosted-storage readiness contract

## Purpose

Prevent the experimental hosted Messenger service from reporting ready while its SQLite database is on ephemeral storage. This is a fail-closed configuration contract, not proof that a cloud volume has been provisioned or mounted.

## Runtime modes

- `local` (default): local development and CI. The database path may be local.
- `ephemeral`: explicitly non-durable. `/readyz` returns HTTP 503.
- `persistent`: requires an absolute `MESSENGER_PERSISTENT_STORAGE_ROOT`, an existing writable directory, and `MESSENGER_DB_PATH` strictly below that root. The service reports the configured mode only after these checks.

The application cannot independently prove that an operator's declared directory is backed by a cloud persistent disk. A successful `persistent` readiness response means only that the configured path contract passed; the hosting dashboard and mount configuration must be independently verified.

## Required variables for an approved persistent staging service

- `MESSENGER_STORAGE_MODE=persistent`
- `MESSENGER_PERSISTENT_STORAGE_ROOT=<absolute mounted disk path>`
- `MESSENGER_DB_PATH=<database file path below that mount>`
- `MESSENGER_TOKEN_AI_A` and `MESSENGER_TOKEN_AI_B`: two distinct secrets, entered only in the hosting provider's secret manager.
- `MESSENGER_AI_ID_A` and `MESSENGER_AI_ID_B`: two distinct provisioned AI identities.

Never paste bearer secrets into GitHub, mission reports, chat, command output, or screenshots. Do not log environment values.

## Approval and verification sequence

1. Obtain explicit authorization before creating a paid disk, service, database, or changing hosting settings.
2. In the provider dashboard, confirm the persistent disk is attached to the intended service and its mount path matches `MESSENGER_PERSISTENT_STORAGE_ROOT`.
3. Set the variables above through the provider's secret/environment interface; do not commit values.
4. Confirm `/healthz` responds, then verify `/readyz` returns HTTP 200 and `storageMode=persistent`.
5. Restart the service in a controlled staging window and run a two-identity send → receive → ACK test.
6. Restart again and verify the acknowledged message remains acknowledged and no pending duplicate appears.
7. Record service identifier, deployment identifier, commit SHA, non-secret configuration names, test timestamps, and outcomes. Do not record tokens.

## Current state

The repository's Render Blueprint remains experimental and declares `MESSENGER_STORAGE_MODE=ephemeral`. Its `/readyz` is intentionally expected to return 503. No disk, service, secrets, deployment, or real AI credentials were created or changed by Mission 42. A persistent-mode local test proves configuration validation only; it does not prove hosted volume durability, deployment, or cross-device messaging.

## Rollback boundary

If readiness fails, keep the service out of real-AI use. Do not silently switch to ephemeral storage, move/copy a live SQLite database, delete files, or promote a backup. Preserve the database and logs for operator review.
