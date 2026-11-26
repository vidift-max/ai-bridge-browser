from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github/workflows/android-build.yml").read_text(encoding="utf-8")
GRADLE = (ROOT / "app/build.gradle.kts").read_text(encoding="utf-8")
MANIFEST = (ROOT / "scripts/create_android_update_manifest.py").read_text(encoding="utf-8")
UPDATER = (ROOT / "app/src/main/java/com/vidiftmax/aibridgebrowser/UpdateCenterActivity.java").read_text(encoding="utf-8")
RELEASE_POLICY = (ROOT / "app/src/main/java/com/vidiftmax/aibridgebrowser/UpdateReleasePolicy.java").read_text(encoding="utf-8")


class OfficialReleasePublicationContractTest(unittest.TestCase):
    def test_release_job_is_manual_and_scoped_for_publishing(self):
        self.assertIn("github.event_name == 'workflow_dispatch'", WORKFLOW)
        self.assertIn("github.ref == 'refs/heads/v2-saas-alpha'", WORKFLOW)
        self.assertIn("contents: write", WORKFLOW)
        self.assertIn("GH_TOKEN: ${{ github.token }}", WORKFLOW)
        self.assertIn("gh release create", WORKFLOW)

    def test_push_branch_filters_do_not_contain_duplicate_entries(self):
        push_section = WORKFLOW.split("  pull_request:", 1)[0]
        branch_entries = re.findall(r'^      - "([^"]+)"$', push_section, re.MULTILINE)
        self.assertEqual(len(branch_entries), len(set(branch_entries)))

    def test_release_tag_and_latest_endpoint_match_updater_contract(self):
        expected_tag = 'TAG="v${VERSION_NAME}-${VERSION_CODE}"'
        self.assertIn(expected_tag, WORKFLOW)
        self.assertIn("/releases/latest", UPDATER)
        self.assertIn('"tag_name"', UPDATER)
        self.assertIn("/vidift-max/ai-bridge-browser/releases/download/", (ROOT / "app/src/main/java/com/vidiftmax/aibridgebrowser/UpdateUrlPolicy.java").read_text(encoding="utf-8"))
        self.assertIn("ai-bridge-update.json", WORKFLOW)
        self.assertIn("app-release.apk", WORKFLOW)

    def test_signed_release_gate_requires_all_existing_signing_secrets(self):
        for secret in (
            "AI_PHONE_RELEASE_KEYSTORE_B64",
            "AI_PHONE_RELEASE_STORE_PASSWORD",
            "AI_PHONE_RELEASE_KEY_ALIAS",
            "AI_PHONE_RELEASE_KEY_PASSWORD",
        ):
            self.assertIn(secret, WORKFLOW)

    def test_release_uploads_the_manifest_and_verification_evidence(self):
        self.assertIn("app/build/outputs/apk/release/app-release.apk", WORKFLOW)
        self.assertIn("ai-bridge-update.json", WORKFLOW)
        self.assertIn("app-release.apk.sha256", WORKFLOW)
        self.assertIn("app-release-signature.txt", WORKFLOW)
        self.assertIn('EXPECTED_APK_ASSET = "app-release.apk"', MANIFEST)

    def test_android_version_is_incremented_for_existing_installations(self):
        self.assertIn("versionCode = 2", GRADLE)
        self.assertIn('versionName = "0.2.0"', GRADLE)


if __name__ == "__main__":
    unittest.main()
