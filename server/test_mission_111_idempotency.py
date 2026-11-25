import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_first_contact as runner


class Mission111IdempotencyTest(unittest.TestCase):
    def test_same_operation_id_produces_stable_message_and_request_ids(self):
        first = runner._operation_identifiers("first-contact-op-20261125-001")
        second = runner._operation_identifiers("first-contact-op-20261125-001")
        self.assertEqual(first, second)
        self.assertTrue(first[0].startswith("first-contact-"))
        self.assertTrue(first[1].startswith("first-contact-request-"))

    def test_distinct_operation_ids_produce_distinct_identifiers(self):
        first = runner._operation_identifiers("first-contact-op-20261125-001")
        second = runner._operation_identifiers("first-contact-op-20261125-002")
        self.assertNotEqual(first[0], second[0])
        self.assertNotEqual(first[1], second[1])

    def test_operation_id_is_bounded_and_header_safe(self):
        for value in ("", "short", "x" * 129, "invalid\noperation-0001", "bad/id-operation-001"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "invalid_operation_id"):
                runner._operation_identifiers(value)

    def test_invalid_operation_id_is_rejected_before_network(self):
        from unittest.mock import Mock
        request = Mock()
        with self.assertRaisesRegex(ValueError, "invalid_operation_id"):
            runner.run_first_contact(
                "https://stage.example", "room", "token-a", "token-b",
                request=request, operation_id="bad/id-operation-001")
        request.assert_not_called()

    def test_operation_id_never_appears_in_generated_message_identifiers(self):
        operation_id = "sensitive-context-free-operation-0001"
        message_id, request_id = runner._operation_identifiers(operation_id)
        self.assertNotIn(operation_id, message_id)
        self.assertNotIn(operation_id, request_id)
        self.assertLessEqual(len(message_id), 64)
        self.assertLessEqual(len(request_id), 80)


if __name__ == "__main__":
    unittest.main()
