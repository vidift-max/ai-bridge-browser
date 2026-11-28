# Clean-room implementation record — AI Tool Hub

Date: 2026-11-28  
Archived source package SHA-256: `f5415aabd795da2f30fcbbaca1cfb40cfb0f68a8235e5e4f36d2806f09253cee`.

## Separation decision
The archived package remains unchanged and is not imported, copied, adapted, bundled, or executed. Its source-license and authorship status remain unresolved. This branch implements only the same broad user-facing capabilities using newly authored code in `server/tool_adapters.py`, based on generic functional requirements and safety constraints in the audit report. This is not a claim of source equivalence, exact parity, or license clearance for the original ZIP.

## New implementation inventory
- `duration_timer`: bounded, linear duration parser and formatter.
- `recipe_scaler`: bounded quantity scaling; declared units are preserved, not automatically converted.
- `quiz_engine`: bounded quiz construction and scoring; output remains data, not HTML.
- `svg_chart`: SVG generation with escaped text and a fixed set of SVG elements/attributes.
- `link_card`: strict HTTP(S) URL normalization and metadata output; no network fetch.

Per-tool JSON schemas live under `registry/tool-hub/schemas/`. Runtime input checks are performed by each adapter; the catalog loader verifies that each READY schema reference resolves to a schema file inside the registry.

## Security boundary
- No network, filesystem, shell, browser DOM, or subprocess access in adapters.
- Tool calls require authenticated principal identity and an explicit durable per-tool `TOOL_USE` grant.
- No identity field is accepted in the invocation body.
- Body limit 10,000 bytes; output limit 32 KiB; per-principal/per-tool sliding-window limiter 60/minute.
- `link_card` does not retrieve titles or follow redirects; private/local IP destinations are rejected.
- `svg_chart` returns SVG text only. Any Android/UI consumer must parse/sanitize it and must not inject arbitrary HTML.
- Tool grants remain deny-by-default. No AI-01/AI-02 grant has been silently inserted.

## Verification status
Unit and HTTP tests are authored. Their execution status is determined only by CI on the exact PR head; this record must be updated after CI returns. No deployment or real-agent invocation is claimed.
