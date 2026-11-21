import unittest
from server.operational_runtime import OperationalRuntime


class OperationalEventPolicyTests(unittest.TestCase):
    def test_event_buffer_is_bounded(self):
        runtime = OperationalRuntime(max_events=2)
        runtime.record("ONE")
        runtime.record("TWO")
        runtime.record("THREE")
        self.assertEqual([e.event_type for e in runtime.snapshot()], ["TWO", "THREE"])

    def test_metadata_is_truncated(self):
        runtime = OperationalRuntime()
        event = runtime.record("REQUEST", metadata={"route": "x" * 300})
        self.assertEqual(len(event.metadata["route"]), 256)

    def test_no_payload_field_is_part_of_event_contract(self):
        runtime = OperationalRuntime()
        event = runtime.record("MESSAGE_SUBMITTED", metadata={"count": "1"})
        self.assertFalse(hasattr(event, "body"))
        self.assertFalse(hasattr(event, "payload"))


if __name__ == "__main__":
    unittest.main()
