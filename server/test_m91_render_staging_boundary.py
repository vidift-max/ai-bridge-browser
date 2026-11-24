import unittest
from pathlib import Path


class Mission91RenderBoundaryTest(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_staging_blueprint_isolated_and_persistent(self):
        text = (self.ROOT / "render.staging.yaml").read_text(encoding="utf-8")
        self.assertIn("name: ai-bridge-browser-staging", text)
        self.assertIn("plan: starter", text)
        self.assertIn("value: persistent", text)
        self.assertIn("mountPath: /var/data", text)

    def test_staging_blueprint_does_not_auto_deploy_from_m91_contract(self):
        doc = (self.ROOT / "docs/MISSION_91_RENDER_STAGING_PLAN.md").read_text(encoding="utf-8")
        self.assertIn("Disabled auto-sync", doc)
        self.assertIn("No Render service was created", doc)
        self.assertIn("BLOCKED_PENDING_PAYMENT_INFO", doc)

    def test_no_production_service_reference(self):
        text = (self.ROOT / "render.staging.yaml").read_text(encoding="utf-8").lower()
        self.assertNotIn("production", text)


if __name__ == "__main__":
    unittest.main()
