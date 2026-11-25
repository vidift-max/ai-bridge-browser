# M136 — Android Browser APK Readiness

Status: IN PROGRESS until Android Build workflow completes successfully on this branch.

Base: `f2ab4695b26a46ecffde05dc980ec11aae270fb2` (M135 approved head).
Branch: `feat/mission-136-android-browser-apk-readiness`

## Goal

Make the existing Android application build workflow produce a downloadable, installable **debug APK** for the AI Bridge Browser Android shell. The source ZIP is not an installer. This mission does not create hosting, configure production secrets, sign a public release, or enable paid provider calls.

## Ten rounds

1. Revalidated M135 PR #136 head and its five successful CI workflows.
2. Audited Android project structure, manifest, Gradle configuration, and launcher activities.
3. Confirmed the Android module contains the browser WebView activity and collective-room entry point.
4. Audited the Android Build workflow and identified that the active M135/M136 branches were not included in push/PR triggers.
5. Created an isolated M136 branch from the exact approved M135 head.
6. Added the M136 branch to Android Build push triggers so a branch commit produces an APK workflow run.
7. Added M135 and M136 target branches to pull-request triggers for Android validation.
8. Documented the exact GitHub Actions artifact name, APK filename, and distinction between source ZIP, debug APK, and unsigned/release-preparation output.
9. Added this mission record with explicit limitations and acceptance criteria.
10. Validate the resulting workflow run, confirm artifact availability, and record the final SHA/CI result. This round remains pending until GitHub Actions reports success and the artifact is present.

## Acceptance criteria

- Android Build runs on this M136 branch.
- `:app:testDebugUnitTest` and `:app:assembleDebug` succeed.
- GitHub Actions uploads `ai-phone-debug-apk` containing `app-debug.apk`.
- No signing secrets, production service, domain, deployment, paid API, or real participant contact is configured.
- APK build success is not treated as proof of installation on the user's tablet or proof of live collective-room connectivity.

## Tablet installation path after CI

Open the successful Android Build workflow run in GitHub Actions, download artifact `ai-phone-debug-apk`, extract the artifact ZIP, then tap `app-debug.apk` on Android and approve installation from that source if Android asks. The first launch opens the Android app; use **Ferramentas → Abrir navegador e Central de Controle** to open the browser. Actual collective-room use still requires a reachable HTTPS rooms server and authorized login/configuration.

## Current limitations

The debug APK is a test build. It is not a Play Store release and is not signed with a project release key. The Android shell's default launcher remains the AI-PHONE home screen, with the browser available through its browser button. A successful CI build does not prove a physical tablet install or server/API activation.
