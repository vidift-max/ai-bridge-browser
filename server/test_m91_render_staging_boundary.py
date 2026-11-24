import unittest
from pathlib import Path


class Mission91RenderBoundaryTest(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_staging_blueprint_isolated_and_ephemeral(self):
        text = (self.ROOT / "render.staging.yaml").read_text(encoding="utf-8")
        self.assertIn("name: ai-bridge-browser-staging", text)
        self.assertIn("plan: free", text)
        self.assertIn("value: ephemeral", text)
        self.assertIn("value: ':memory:'", text)
        self.assertNotIn("mountPath: /var/data", text)

    def test_staging_blueprint_does_not_auto_deploy_from_m91_contract(self):
        doc = (self.ROOT / "docs/MISSION_91_RENDER_STAGING_PLAN.md").read_text(encoding="utf-8")
        self.assertIn("Auto-sync: disabled", doc)
        self.assertIn("No physical AI-PHONE is activated", doc)
        self.assertIn("Render plan: **Free**", doc)

    def test_no_production_service_reference(self):
        text = (self.ROOT / "render.staging.yaml").read_text(encoding="utf-8").lower()
        self.assertNotIn("production", text)


if __name__ == "__main__":
    unittest.main()
