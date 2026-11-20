# Tab Lock and Persistence

## Safety rule

Every tab starts locked (🔒). A locked tab cannot be closed by an accidental tap.

To close a tab:
1. Unlock the tab explicitly.
2. Confirm the close action.
3. Only then destroy the WebView and remove its persisted tab record.

Lock state is persisted and restored with the tab.

## Restore rule

The browser must persist, at minimum:
- stable tab ID;
- profile/session ID;
- URL;
- active tab;
- lock state;
- mission ID and mission state;
- queued messages;
- last known title;
- pause state.

On application restart:
1. Load persisted tab records.
2. Recreate the corresponding tab/profile containers.
3. Restore URLs and active tab.
4. Wait for each page to reach the ready state.
5. Revalidate the session/profile state.
6. Resume only actions that were previously authorized.

Closing the app is treated as a pause, not as permission to discard work.

## Evidence boundary

The current implementation only restores URLs and active-tab state through Android instance state. Durable persistence across process death, persistent message queues, and truly isolated WebView profiles still require implementation and reproducible testing on Android 12.

🔒 is a UI safety requirement already specified, not evidence that persistence or account isolation is complete.