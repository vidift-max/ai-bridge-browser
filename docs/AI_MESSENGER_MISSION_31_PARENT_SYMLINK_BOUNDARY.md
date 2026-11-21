# Mission 31 — Restore Candidate Parent Symlink Boundary

## Objective
Close the narrow gap left by Mission 30: a candidate leaf may be a regular file while one of its lexical parent components is a symbolic link.

## Implementation
`validate_restore_candidate` now checks the candidate path and each `Path.parents` component with `is_symlink()` before checking the regular-file condition or opening SQLite. Any detected symbolic link returns the existing generic `RESTORE_CANDIDATE_INTEGRITY_FAILED` result.

## Regression coverage
- Existing regular candidate path remains accepted.
- Symlink at the candidate leaf is rejected before SQLite is opened.
- Dangling symlink at the candidate leaf is rejected before SQLite is opened.
- Symlink at the immediate parent directory is rejected before SQLite is opened.
- Symlink at an intermediate parent directory is rejected before SQLite is opened.

Symlink-creation tests skip with an explicit reason on platforms/environments that do not permit creating the required link. The backend CI result must therefore be inspected for skip counts before PASS.

## Security boundary
This is lexical path-component screening, not an atomic file-handle identity check. It does not prove resistance to:
- replacement of a path component after the check;
- hard-link aliasing;
- Windows junction/reparse-point behavior across all supported versions;
- mount-point or other filesystem aliasing;
- external filesystem tampering.

Keep candidate directories operator-controlled and quiescent. A successful validation is not provenance proof, production recovery certification, or authorization to promote a candidate.

## Exclusions
No candidate is modified, deleted, promoted, or restored over a live database. No deployment or physical-device test is included.

## Verification gate
Require Messenger Backend Test and Android Build to complete with SUCCESS on the exact same final branch HEAD. Inspect backend test totals and skips, not just the workflow conclusion.
