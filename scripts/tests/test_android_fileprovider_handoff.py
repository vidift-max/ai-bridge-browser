import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
FILE_PATHS = ROOT / "app/src/main/res/xml/file_paths.xml"
ACTIVITY = ROOT / "app/src/main/java/com/vidiftmax/aibridgebrowser/UpdateCenterActivity.java"
POLICY = ROOT / "app/src/main/java/com/vidiftmax/aibridgebrowser/InstallerIntentPolicy.java"
PACKAGE = "com.vidiftmax.aibridgebrowser"

class FileProviderHandoffWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = ET.parse(MANIFEST).getroot()
        cls.paths = ET.parse(FILE_PATHS).getroot()
        cls.activity = ACTIVITY.read_text(encoding="utf-8")
        cls.policy = POLICY.read_text(encoding="utf-8")

    def test_application_id_and_provider_authority_are_bound(self):
        app = self.manifest.find("application")
        self.assertEqual(1, len(app.findall("provider")))
        provider = app.findall("provider")[0]
        self.assertEqual("androidx.core.content.FileProvider", provider.get(ANDROID_NS + "name"))
        self.assertEqual("${applicationId}.fileprovider", provider.get(ANDROID_NS + "authorities"))
        self.assertIn('getPackageName() + ".fileprovider"', self.activity)

    def test_physical_update_folder_maps_to_expected_logical_uri_prefix(self):
        matches = [n for n in self.paths if n.tag == "external-files-path" and n.get("name") == "app_update_apk"]
        self.assertEqual(1, len(matches))
        self.assertEqual("Download/updates/", matches[0].get("path"))
        self.assertIn('new File(downloads, "updates")', self.activity)
        self.assertIn('new File(canonicalFolder, APK_ASSET)', self.activity)
        self.assertIn('private static final String APK_ASSET = "app-release.apk"', self.activity)
        self.assertIn('private static final String APK_PATH = "/app_update_apk/app-release.apk"', self.policy)

    def test_installer_uri_is_created_by_androidx_fileprovider(self):
        self.assertIn('FileProvider.getUriForFile(this, getPackageName() + ".fileprovider", apk)', self.activity)
        self.assertNotIn("Uri.fromFile(", self.activity)
        self.assertNotIn("file://", self.activity)

    def test_installer_action_and_mime_are_exact(self):
        self.assertIn("new Intent(Intent.ACTION_VIEW)", self.activity)
        self.assertIn('install.setDataAndType(uri, "application/vnd.android.package-archive")', self.activity)
        self.assertIn('private static final String APK_MIME = "application/vnd.android.package-archive"', self.policy)

    def test_only_read_grant_and_new_task_are_added(self):
        self.assertIn("Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK", self.activity)
        self.assertNotIn("FLAG_GRANT_WRITE_URI_PERMISSION", self.activity)
        self.assertIn("Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK", self.policy)

    def test_policy_gate_occurs_after_uri_creation_and_before_activity_launch(self):
        created = self.activity.index("FileProvider.getUriForFile(")
        gate = self.activity.index("InstallerIntentPolicy.isSafeHandoff(")
        launch = self.activity.index("startActivity(install)", gate)
        self.assertLess(created, gate)
        self.assertLess(gate, launch)
        self.assertIn("throw new SecurityException(", self.activity[gate:launch])

    def test_locked_verified_apk_gate_precedes_uri_creation(self):
        locked = self.activity.index("UpdateInstallPolicy.isLockedInstallerHandoff(")
        created = self.activity.index("FileProvider.getUriForFile(")
        self.assertLess(locked, created)
        self.assertIn("expected.sha256.equals(sha256(apk))", self.activity)

    def test_policy_rejects_noncanonical_provider_paths(self):
        self.assertIn('"/app_update_apk/app-release.apk"', self.policy)
        self.assertIn("parsed.getRawPath()", self.policy)
        self.assertIn("parsed.getRawQuery() == null", self.policy)
        self.assertIn("parsed.getRawFragment() == null", self.policy)

    def test_fileprovider_contract_has_no_broad_root_mapping(self):
        forbidden = {"root-path", "external-path", "files-path"}
        self.assertFalse(any(n.tag in forbidden for n in self.paths))

if __name__ == "__main__":
    unittest.main()
