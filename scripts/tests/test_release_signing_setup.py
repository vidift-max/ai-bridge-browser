import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class ReleaseSigningSetupContractTest(unittest.TestCase):
    def test_local_key_generator_exists_and_never_overwrites(self):
        script = (ROOT / "scripts/create_ai_phone_release_keystore.ps1").read_text(encoding="utf-8")
        self.assertIn("keytool", script)
        self.assertIn("Refusing to overwrite", script)
        self.assertIn("ToBase64String", script)
        self.assertNotIn("Write-Host $encoded", script)

    def test_private_signing_files_are_gitignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("*.keystore", ignore)
        self.assertIn("*.jks", ignore)
        self.assertIn("ai-phone-release-keystore.b64", ignore)

    def test_documentation_blocks_unsafe_uninstall_migration(self):
        docs = (ROOT / "docs/AI_PHONE_RELEASE_SIGNING.md").read_text(encoding="utf-8")
        self.assertIn("Não desinstale o aplicativo instalado", docs)
        self.assertIn("AI_PHONE_EXPECTED_SIGNING_CERT_SHA256", docs)
        self.assertIn("create_ai_phone_release_keystore.ps1", docs)
        self.assertNotIn("pode exigir a remoção do APK Debug", docs)


if __name__ == "__main__":
    unittest.main()
