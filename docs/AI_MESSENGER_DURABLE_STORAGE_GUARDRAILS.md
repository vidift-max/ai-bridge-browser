# Durable Storage Guardrails

1. The database path is runtime configuration, never a secret committed with credentials.
2. SQLite is suitable for the current experimental single-process path; it is not yet a claim of production-scale concurrency.
3. The storage directory must be writable by the hosting runtime and protected from source-control commits.
4. Database backups, retention, encryption-at-rest policy and disaster recovery are not implemented yet.
5. Authentication remains opaque runtime-token lookup; this is not a real external identity provider.
6. Android must not be pointed at the service until authenticated end-to-end tests pass.
7. A restart-recovery test is mandatory before considering the durable layer complete.
