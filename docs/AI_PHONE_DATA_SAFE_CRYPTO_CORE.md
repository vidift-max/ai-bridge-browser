# AI-PHONE DATA SAFE — Crypto Core (M323)

Status: isolated cryptographic core implemented on branch `feat/data-safe-crypto-core-m323`.
This is not a complete backup/export/restore feature and is not wired into the Android UI.

## Envelope v1
- Magic: ASCII `AIPSAFE1`
- Version: 1
- KDF iterations: PBKDF2-HMAC-SHA-256, 310,000
- Salt: 16 random bytes
- Nonce: 12 random bytes
- Cipher: AES-256-GCM with a 128-bit authentication tag
- The complete fixed header is authenticated as GCM AAD.
- Password is never serialized. Derived key and temporary salt/nonce buffers are cleared after use.
- Password length: 12–1024 Java characters.
- Payload limit: 256 MiB.

## Archive path policy
Future archive readers must call `DataSafePathPolicy.validate` before creating any file.
Absolute paths, Windows separators/drive prefixes, empty/dot/dot-dot segments, NUL/control characters, and overlong paths are rejected.

## Defensive limits
- 4,096 entries
- 32 MiB per entry
- 256 MiB total expanded size
- 100:1 maximum compression ratio
- 1,024 UTF-8 bytes per path

These are policy constants only; no ZIP reader/writer exists yet, so enforcement across an archive is not yet implemented.

## Explicit non-goals
- No Android Keystore key export.
- No credential vault export.
- No automatic backup or restore.
- No SAF picker, staging directory, attachment copier, manifest/checksum implementation, or rollback yet.
- No changes to installed app or user data.

## Validation required before integration
Run Android unit tests on the project toolchain; add malformed-header/KDF-boundary, oversized payload, archive duplicate-entry, zip-bomb, checksum, interruption, staging, and rollback tests. Review KDF performance on supported devices before shipping.
