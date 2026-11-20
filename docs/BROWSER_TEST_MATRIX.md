# Browser Foundation Test Matrix

## Automated / CI checks

- Compile Android debug APK with AndroidX WebKit dependency.
- Run JVM unit tests for browser state, tab identity, control-center state and persistence.
- Review Android lint output, especially WebView lifecycle callbacks.
- Confirm the six-tab cap is enforced in the UI path.
- Confirm profile assignment is performed before settings, clients, JavaScript evaluation or navigation.

## Manual browser checks

- Create one through six tabs; seventh creation is rejected.
- Switch between tabs without changing their URL/title identity.
- Navigate by address, go back, go forward and reload.
- Lock/unlock; locked tab cannot close; unlocked tab requires confirmation.
- Confirm tab order and active tab after close.
- Recreate Activity and restart process; verify the persisted metadata and URLs.
- Verify PAUSE prevents queued work from advancing and RESUME waits for page readiness.
- Trigger or simulate a WebView renderer exit; app must handle the callback and remove the crashed renderer without crashing the Activity.
- Verify invalid TLS, unsupported URL schemes, URL userinfo, mixed content, file/content access, popups and camera/microphone requests remain blocked.

## Session-isolation checks — physical device required

- Read actual `WebViewFeature.MULTI_PROFILE` support from the installed Android System WebView.
- Confirm each tab receives its own stable profile name before first WebView use.
- If unsupported, confirm the tab is visibly marked shared and no account-isolation claim is made.
- With two test accounts, confirm cookies, local storage, login/logout and session persistence are independent.
- Repeat with up to six profiles and record RAM, load latency, crashes and WebView version.

## Device readiness gate

Physical Galaxy Tab A7 testing remains pending until the user authorizes installation. CI success is not a substitute for this gate. Do not declare six independent accounts ready until the two-account isolation test passes on the target device and six-profile stability has been measured.

## Out of scope for browser completion

Remote control, automatic message injection/submission, mission distribution, external provider integrations, group-chat API and audio bridging are later phases.
