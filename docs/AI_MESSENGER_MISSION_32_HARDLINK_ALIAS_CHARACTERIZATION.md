# Mission 32 — Hard-link Alias Characterization

## Scope
Characterize whether read-only restore-candidate validation distinguishes a hard-link alias from an ordinary regular file. No production restore, promotion, deletion, or filesystem policy change is included.

## Work performed
1. Inspected the current candidate path screening and SQLite read-only open sequence.
2. Distinguished symbolic links from hard links: `Path.is_symlink()` does not identify a hard-link alias.
3. Added a platform-dependent regression test that creates a hard link to a valid candidate.
4. The test verifies both paths identify the same file, validation currently accepts the alias, and bytes visible through both names remain unchanged.
5. Updated the operator runbook to state the observed behavior and operational boundary.

## Result
This mission characterizes existing behavior; it does not implement hard-link rejection. A hard link is another directory entry for the same underlying file, so successful validation does not establish unique artifact identity or provenance.

## Limitations
- Multi-link files are not rejected.
- The validator does not establish provenance or independent storage.
- No protection against concurrent replacement, filesystem tampering, or hard-link creation is claimed.
- Hard-link tests may be skipped on filesystems or runners that disallow link creation.
- A passing CI workflow proves only the repository tests/build on the recorded commit, not production recovery readiness.

## Verification gate
PASS requires Messenger Backend Test and Android Build to complete successfully on the same final HEAD.
