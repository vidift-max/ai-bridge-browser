# Foundation Gate

PASS criteria:
- Android project builds in CI.
- Browser shell and tab model are documented.
- Durable identity is stable.
- Locked tabs are protected.
- Lifecycle pause/recovery is explicit.
- No claim of real profile isolation, remote control, DOM automation, or audio.

NO-GO:
- a change weakens tab safety
- a queued action can be silently lost
- remote control is introduced before the foundation gate

BLOCKED:
- physical tablet validation without an authorized installation/test.
