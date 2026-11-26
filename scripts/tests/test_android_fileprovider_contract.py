import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
FILE_PATHS = ROOT / "app/src/main/res/xml/file_paths.xml"


class FileProviderScopeContractTests(unittest.TestCase):
    def test_manifest_declares_one_non_exported_grant_only_file_provider(self):
        root = ET.parse(MANIFEST).getroot()
        providers = [
            node for node in root.findall("./application/provider")
            if node.get(ANDROID_NS + "name") == "androidx.core.content.FileProvider"
        ]
        self.assertEqual(1, len(providers), "expected_exactly_one_androidx_fileprovider")
        provider = providers[0]
        self.assertEqual("${applicationId}.fileprovider",
                         provider.get(ANDROID_NS + "authorities"))
        self.assertEqual("false", provider.get(ANDROID_NS + "exported"))
        self.assertEqual("true", provider.get(ANDROID_NS + "grantUriPermissions"))
        metadata = provider.findall("meta-data")
        self.assertEqual(1, len(metadata))
        self.assertEqual("android.support.FILE_PROVIDER_PATHS",
                         metadata[0].get(ANDROID_NS + "name"))
        self.assertEqual("@xml/file_paths", metadata[0].get(ANDROID_NS + "resource"))

    def test_provider_paths_are_exactly_the_update_folder_and_documents_cache(self):
        root = ET.parse(FILE_PATHS).getroot()
        entries = list(root)
        self.assertEqual(2, len(entries), "unexpected_fileprovider_path_count")
        by_tag_and_name = {
            (node.tag, node.get("name")): node.get("path")
            for node in entries
        }
        self.assertEqual(
            "Download/updates/",
            by_tag_and_name.get(("external-files-path", "app_update_apk")),
        )
        self.assertEqual(
            "official_documents/",
            by_tag_and_name.get(("cache-path", "official_documents")),
        )
        for node in entries:
            self.assertNotIn("..", node.get("path", ""))
            self.assertNotIn("*", node.get("path", ""))

    def test_no_root_or_broad_external_storage_mapping_is_allowed(self):
        root = ET.parse(FILE_PATHS).getroot()
        forbidden = {"root-path", "external-path", "files-path"}
        for node in root:
            self.assertNotIn(node.tag, forbidden, "broad_fileprovider_mapping_forbidden")

    def test_update_path_contract_matches_private_download_construction(self):
        source = (ROOT / "app/src/main/java/com/vidiftmax/aibridgebrowser/UpdateCenterActivity.java").read_text(encoding="utf-8")
        self.assertIn('getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)', source)
        self.assertIn('new File(downloads, "updates")', source)
        xml = ET.parse(FILE_PATHS).getroot()
        update_mapping = [
            node for node in xml
            if node.tag == "external-files-path" and node.get("name") == "app_update_apk"
        ]
        self.assertEqual(1, len(update_mapping))
        self.assertEqual("Download/updates/", update_mapping[0].get("path"))


if __name__ == "__main__":
    unittest.main()
