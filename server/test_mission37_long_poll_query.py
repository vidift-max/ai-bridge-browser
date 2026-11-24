import unittest

from server.http_server import parse_long_poll_query


class StrictLongPollQueryTest(unittest.TestCase):
    def test_accepts_default_negotiated_profile(self):
        self.assertEqual(
            parse_long_poll_query("after=0&limit=100&timeout=20"),
            (0, 100, 20),
        )

    def test_accepts_tighter_negotiated_profile(self):
        self.assertEqual(
            parse_long_poll_query("after=17&limit=25&timeout=7"),
            (17, 25, 7),
        )

    def test_accepts_zero_wait_and_maximum_safe_cursor(self):
        self.assertEqual(
            parse_long_poll_query(
                "after=9007199254740991&limit=1&timeout=0"
            ),
            (9007199254740991, 1, 0),
        )

    def test_rejects_missing_or_unknown_parameters(self):
        invalid = (
            "after=0&limit=10",
            "after=0&limit=10&timeout=1&extra=x",
            "after=0&limit=10&timeout=1&",
        )
        for query in invalid:
            with self.subTest(query=query):
                with self.assertRaisesRegex(ValueError, "invalid_long_poll_query"):
                    parse_long_poll_query(query)

    def test_rejects_duplicate_parameters(self):
        for query in (
            "after=0&after=1&limit=10&timeout=1",
            "after=0&limit=10&timeout=1&timeout=2",
        ):
            with self.subTest(query=query):
                with self.assertRaisesRegex(ValueError, "invalid_long_poll_query"):
                    parse_long_poll_query(query)

    def test_rejects_empty_values_and_empty_query(self):
        for query in (
            "",
            "after=&limit=10&timeout=1",
            "after=0&limit=&timeout=1",
            "after=0&limit=10&timeout=",
        ):
            with self.subTest(query=query):
                with self.assertRaisesRegex(ValueError, "invalid_long_poll_query"):
                    parse_long_poll_query(query)

    def test_rejects_non_decimal_and_non_ascii_numbers(self):
        for query in (
            "after=-1&limit=10&timeout=1",
            "after=1.5&limit=10&timeout=1",
            "after=%EF%BC%91&limit=10&timeout=1",
            "after=1&limit=10&timeout=1.0",
            "after=1&limit=+10&timeout=1",
        ):
            with self.subTest(query=query):
                with self.assertRaisesRegex(ValueError, "invalid_long_poll_query"):
                    parse_long_poll_query(query)

    def test_rejects_cursor_above_safe_integer(self):
        with self.assertRaisesRegex(ValueError, "invalid_long_poll_query"):
            parse_long_poll_query(
                "after=9007199254740992&limit=10&timeout=1"
            )

    def test_rejects_batch_size_outside_contract(self):
        for limit in (0, 101):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(ValueError, "invalid_long_poll_query"):
                    parse_long_poll_query(
                        f"after=0&limit={limit}&timeout=1"
                    )

    def test_rejects_timeout_above_server_capability(self):
        with self.assertRaisesRegex(ValueError, "invalid_long_poll_query"):
            parse_long_poll_query("after=0&limit=10&timeout=26")

    def test_rejects_more_than_three_fields(self):
        with self.assertRaisesRegex(ValueError, "invalid_long_poll_query"):
            parse_long_poll_query(
                "after=0&limit=10&timeout=1&other=2"
            )


if __name__ == "__main__":
    unittest.main()
