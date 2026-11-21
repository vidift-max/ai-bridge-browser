# SQLite Backup Policy

Backups are operator-triggered local snapshots. The destination must be new; the backup operation never overwrites an existing file and never deletes older snapshots. The SQLite online backup API is used so a consistent snapshot can be produced while the source connection is open.

A successful backup is accepted only after a separate integrity check. A failed backup must return a stable diagnostic code without exposing SQL, paths, message content, or exception text. Backup files contain the same sensitive message data as the source and must be protected by the operator.

This primitive is not an automated backup schedule, off-site copy, encryption system, retention policy, or proven disaster-recovery process. Restore is deliberately not automatic.
