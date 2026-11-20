# Browser Shell

The shell owns the Android Activity, top controls, tab strip, active WebView surface, status area, and lifecycle.

The shell must not own provider-specific logic. Remote control and external AI adapters belong to later layers.

Initial device target: Android tablet. Layout must remain usable on smaller screens and landscape/portrait changes.
