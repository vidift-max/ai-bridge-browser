import unittest

from server.local_inference import (
    LocalInferenceController,
    LocalInferenceError,
    LocalInferencePolicy,
)


class FakeLocalEngine:
    engine_id = "fake-local-test-engine"
    runtime_scope = "server_host"
    local_only = True
    network_access = "NONE"
    downloads_allowed = False

    def __init__(self):
        self.calls = []

    def generate(self, prompt, *, max_output_tokens):
        self.calls.append((prompt, max_output_tokens))
        return "local response"


class LocalInferenceContractTest(unittest.TestCase):
    def test_default_policy_is_disabled_and_engine_is_not_discovered(self):
        controller = LocalInferenceController()
        self.assertFalse(controller.status()["inferenceAvailable"])
        with self.assertRaisesRegex(LocalInferenceError, "LOCAL_INFERENCE_DISABLED_BY_POLICY"):
            controller.execute("hello", user_opt_in=True)

    def test_requires_explicit_user_opt_in(self):
        controller = LocalInferenceController(
            FakeLocalEngine(), LocalInferencePolicy(enabled=True)
        )
        with self.assertRaisesRegex(LocalInferenceError, "EXPLICIT_OPT_IN_REQUIRED"):
            controller.execute("hello")
        self.assertEqual(controller._engine.calls, [])

    def test_truthy_string_is_not_explicit_user_opt_in(self):
        controller = LocalInferenceController(
            FakeLocalEngine(), LocalInferencePolicy(enabled=True)
        )
        with self.assertRaisesRegex(LocalInferenceError, "EXPLICIT_OPT_IN_REQUIRED"):
            controller.execute("hello", user_opt_in="yes")

    def test_accepts_only_declared_server_local_engine(self):
        engine = FakeLocalEngine()
        controller = LocalInferenceController(engine, LocalInferencePolicy(enabled=True))
        self.assertEqual(controller.status()["state"], "READY_FOR_EXPLICIT_OPT_IN")
        self.assertEqual(controller.execute("hello", user_opt_in=True), "local response")
        self.assertEqual(engine.calls, [("hello", 256)])

    def test_rejects_nonlocal_or_network_enabled_engine(self):
        engine = FakeLocalEngine()
        engine.network_access = "HTTP"
        controller = LocalInferenceController(engine, LocalInferencePolicy(enabled=True))
        self.assertFalse(controller.status()["inferenceAvailable"])
        with self.assertRaisesRegex(LocalInferenceError, "LOCAL_ENGINE_NOT_CONFIGURED"):
            controller.execute("hello", user_opt_in=True)

    def test_rejects_policy_that_allows_network_or_downloads(self):
        engine = FakeLocalEngine()
        network_policy = LocalInferencePolicy(enabled=True, allow_network=True)
        self.assertFalse(LocalInferenceController(engine, network_policy).status()["inferenceAvailable"])
        download_policy = LocalInferencePolicy(enabled=True, allow_model_downloads=True)
        self.assertFalse(LocalInferenceController(engine, download_policy).status()["inferenceAvailable"])

    def test_rejects_download_enabled_engine(self):
        engine = FakeLocalEngine()
        engine.downloads_allowed = True
        controller = LocalInferenceController(engine, LocalInferencePolicy(enabled=True))
        self.assertFalse(controller.status()["inferenceAvailable"])

    def test_prompt_and_output_limits_fail_closed(self):
        policy = LocalInferencePolicy(enabled=True, max_prompt_chars=4, max_output_tokens=8)
        controller = LocalInferenceController(FakeLocalEngine(), policy)
        with self.assertRaisesRegex(LocalInferenceError, "PROMPT_TOO_LARGE"):
            controller.execute("12345", user_opt_in=True)
        with self.assertRaisesRegex(LocalInferenceError, "OUTPUT_LIMIT_INVALID"):
            controller.execute("ok", user_opt_in=True, max_output_tokens=9)

    def test_rejects_empty_prompt_and_non_string_result(self):
        controller = LocalInferenceController(FakeLocalEngine(), LocalInferencePolicy(enabled=True))
        with self.assertRaisesRegex(LocalInferenceError, "PROMPT_REQUIRED"):
            controller.execute("  ", user_opt_in=True)
        engine = FakeLocalEngine()
        engine.generate = lambda *args, **kwargs: {"unexpected": "object"}
        controller = LocalInferenceController(engine, LocalInferencePolicy(enabled=True))
        with self.assertRaisesRegex(LocalInferenceError, "LOCAL_ENGINE_INVALID_RESULT"):
            controller.execute("hello", user_opt_in=True)

    def test_rejects_oversized_engine_output(self):
        engine = FakeLocalEngine()
        engine.generate = lambda *args, **kwargs: "x" * 10
        controller = LocalInferenceController(
            engine, LocalInferencePolicy(enabled=True, max_output_chars=5)
        )
        with self.assertRaisesRegex(LocalInferenceError, "LOCAL_ENGINE_OUTPUT_TOO_LARGE"):
            controller.execute("hello", user_opt_in=True)

    def test_does_not_leak_engine_exception_details(self):
        engine = FakeLocalEngine()
        engine.generate = lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("private token must not escape")
        )
        controller = LocalInferenceController(engine, LocalInferencePolicy(enabled=True))
        with self.assertRaisesRegex(LocalInferenceError, "LOCAL_ENGINE_EXECUTION_FAILED") as caught:
            controller.execute("hello", user_opt_in=True)
        self.assertNotIn("private token", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
