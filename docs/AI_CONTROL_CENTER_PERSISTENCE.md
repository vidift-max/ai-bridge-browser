# AI Control Center Persistence

## Stored locally
The browser stores the AI Control Center registry alongside its existing private app preferences:
- AI panel ID, bound tab ID and logical profile ID;
- response and context states;
- the last two captured response lines;
- pending mission text and report-confirmation flag;
- the GPT-6 coordinator draft.

Text values are Base64-encoded before being placed in SharedPreferences. This is encoding, not encryption; Android application sandbox protection remains the security boundary. No provider credentials or session cookies are copied into this registry.

## Recovery rules
- Completed state and its captured tail can be restored.
- A panel restored as SENDING or RESPONDING is changed to UNKNOWN because the in-memory generation observation sequence cannot survive process death.
- An in-flight panel cannot be treated as complete or report-confirmed after restart.
- The pending mission text is retained for explicit recovery/review; it is not automatically submitted.
- Restore suppresses intermediate writes so a partially rebuilt tab list cannot overwrite the saved panel registry.

## Boundaries
- Persistence is local to this app installation; there is no cloud synchronization or multi-device replication.
- The coordinator text box is a saved draft, not a live connection to GPT-6.
- The profile ID remains a logical identifier and does not prove cookie/account isolation.
- No automatic WebView inspection, message injection, submission, external provider integration, or remote control is enabled by this change.
