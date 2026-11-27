# AI-PHONE DATA SAFE — Crypto and ZIP Core (M323/M324)

## Cryptographic envelope (M323)
- Magic: ASCII `AIPSAFE1`; version 1.
- PBKDF2-HMAC-SHA-256, 310,000 iterations, 256-bit derived key.
- 16-byte random salt, 12-byte random nonce.
- AES-256-GCM with a 128-bit tag; the complete fixed header is authenticated as AAD.
- Password is never serialized. Derived key and temporary salt/nonce buffers are cleared after use.
- Password length: 12–1024 Java characters; encrypted payload maximum 256 MiB.

## ZIP engine (M324)
`DataSafeArchiveEngine.write` accepts an in-memory map of relative paths to bytes, writes ZIP entries and a reserved `checksums.sha256` index, and enforces entry, expanded-size, and output-size limits.
`readAndValidate` opens a ZIP using `ZipFile`, rejects unsafe paths, directories, duplicate names, missing size metadata, oversized entries, expanded-size excess, and compression ratios above 100:1 based on ZIP central-directory metadata. It reads and hashes entries in memory; it never extracts files or uses archive paths for filesystem writes.
The checksum index must describe exactly every payload entry; SHA-256 mismatches are rejected. The reserved checksum path cannot be supplied as user data.

## Defensive limits
- 4,096 ZIP entries, including checksum index.
- 32 MiB per entry.
- 256 MiB total expanded size, including checksum index.
- 256 MiB ZIP file size.
- 100:1 maximum declared compression ratio.
- 1,024 UTF-8 bytes per path.

## Boundaries and remaining work
- ZIP engine is an isolated core, not connected to Android UI, SAF, automatic backup, or restore.
- ZIP content remains in memory; large-file streaming/staging is not implemented.
- Compression ratio uses ZIP metadata and is supplemented by strict actual expanded-byte caps; hostile central-directory metadata still requires adversarial testing.
- Android unit tests were authored but have not yet been executed in CI.
- No Android Keystore key export or credential vault export.
- No changes to installed app or user data.
- Before integration: execute Android unit tests; add duplicate-entry and malformed ZIP corpus tests; verify interruption/rollback behavior; benchmark PBKDF2 and memory use on supported devices.
