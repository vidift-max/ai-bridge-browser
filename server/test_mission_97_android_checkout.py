import unittest
from pathlib import Path


class AndroidWorkflowCheckoutTest(unittest.TestCase):
    def test_android_regression_checks_out_repository_before_gradle(self):
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "mission-90-staging-invite-activation.yml"
        ).read_text(encoding="utf-8")
        android_job = workflow.split("  android-regression:", 1)[1].split(
            "  activation-boundary:", 1
        )[0]
        checkout = android_job.index("- uses: actions/checkout@v4")
        setup_java = android_job.index("- uses: actions/setup-java@v4")
        setup_gradle = android_job.index("- uses: gradle/actions/setup-gradle@v4")
        test_task = android_job.index("gradle :app:testDebugUnitTest")
        self.assertLess(checkout, setup_java)
        self.assertLess(setup_java, setup_gradle)
        self.assertLess(setup_gradle, test_task)


if __name__ == "__main__":
    unittest.main()
