# SQLite Backup Operator Runbook

1. Stop and identify the exact local database path used by the experimental backend.
2. Choose a new destination path in a protected location with sufficient free space.
3. Invoke the backup primitive explicitly; do not reuse an existing destination.
4. Require the result BACKUP_CREATED.
5. Independently verify the destination with the storage recovery check.
6. Record the backup location in the operator's private inventory, not in public logs or GitHub.
7. Keep the original database unchanged. Do not restore over it using this tool.

The current implementation has no scheduler, retention cleanup, off-site copy, encryption, or automatic restore. Treat the backup as sensitive because it contains message data.
