# Backup Verification Contract

A backup is valid only when:
1. The source exists as a regular file.
2. The destination differs from the source and does not already exist.
3. SQLite's online backup operation completes.
4. The destination passes PRAGMA integrity_check.

The operation returns only a boolean and a stable diagnostic code. It does not return database rows or raw exception messages. A backup is a copy of sensitive application data; access control and secure storage remain the operator's responsibility.
