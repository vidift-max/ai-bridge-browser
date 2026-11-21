# Readiness and Recovery Boundary

The operational runtime composes the existing SQLite integrity check with bounded operational events. It does not repair a corrupt database, restore backups, or guarantee data recovery. It reports whether SQLite integrity validation succeeds at the time of the check.

A missing database is reported as STORAGE_UNAVAILABLE. An unreadable or integrity-failing database is reported as STORAGE_INTEGRITY. Callers must not expose raw exception text or database contents. A failed check blocks readiness; it does not delete, recreate, or overwrite the database.
