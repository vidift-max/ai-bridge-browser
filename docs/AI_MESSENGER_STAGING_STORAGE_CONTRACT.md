# Staging Storage Contract

The experimental backend uses SQLite through `MESSENGER_DB_PATH`.

Requirements for a future staging host:
- the configured path must be explicit;
- the parent directory must be writable by the service process;
- the database must not be stored in a secret/configuration value;
- startup must not silently fall back from an explicitly invalid path;
- hosted durability must not be inferred from SQLite alone.

A future production deployment must choose storage semantics appropriate to its persistence and availability requirements. This mission does not provision or migrate a hosted database.
