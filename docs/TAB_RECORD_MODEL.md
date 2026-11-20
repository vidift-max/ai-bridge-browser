# Tab Record Model

`TabRecord` contains durable browser metadata and no Android `WebView`.

The record owns stable `tabId`, logical `profileId`, URL, title, lock state and mission state.

`profileId` remains a logical identifier only. It does not prove cookie, storage, or account isolation.