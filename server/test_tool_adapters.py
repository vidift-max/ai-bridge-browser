import unittest
import xml.etree.ElementTree as ET

from server.tool_adapters import (
    ToolInputError, duration_timer, recipe_scaler, quiz_engine, svg_chart, link_card
)


class CleanRoomToolAdapterTests(unittest.TestCase):
    def test_duration_timer_format_and_seconds(self):
        self.assertEqual(duration_timer({"duration": "1h 30m"})["seconds"], 5400)
        self.assertEqual(duration_timer({"duration": "1h 30m"})["formatted"], "1h 30m")
        self.assertEqual(duration_timer({"duration": 90, "operation": "seconds"}), {"seconds": 90})

    def test_duration_timer_rejects_long_and_malformed_inputs(self):
        for value in ("1" * 10000 + "x", "١٢m", "1h xx", "999999999d", ""):
            with self.subTest(value=str(value)[:20]), self.assertRaises(ToolInputError):
                duration_timer({"duration": value})

    def test_recipe_scaler_bounds_and_scales_without_cross_unit_guessing(self):
        result = recipe_scaler({"originalServings": 2, "targetServings": 4,
                                "ingredients": [{"name": "Flour", "amount": 250, "unit": "g"}]})
        self.assertEqual(result["ingredients"][0]["amount"], 500)
        with self.assertRaisesRegex(ToolInputError, "UNKNOWN_UNIT"):
            recipe_scaler({"originalServings": 2, "targetServings": 4,
                           "ingredients": [{"name": "x", "amount": 1, "unit": "__proto__"}]})
        with self.assertRaises(ToolInputError):
            recipe_scaler({"originalServings": 1, "targetServings": 1,
                           "ingredients": [{"name": "x", "amount": 1, "unit": "g"}] * 101})

    def test_quiz_engine_build_and_score(self):
        quiz = {"questions": [{"id": "q1", "prompt": "2+2?", "options": [
            {"id": "a", "text": "3"}, {"id": "b", "text": "4"}],
            "correctOptionId": "b", "explanation": "Arithmetic"}]}
        self.assertEqual(quiz_engine(quiz)["questionCount"], 1)
        scored = quiz_engine({**quiz, "answers": {"q1": "b"}})
        self.assertEqual(scored["scorePercent"], 100)
        with self.assertRaises(ToolInputError):
            quiz_engine({**quiz, "answers": {"q1": {"bad": "shape"}}})

    def test_svg_chart_escapes_text_and_produces_well_formed_xml(self):
        output = svg_chart({"title": "<script>alert(1)</script>", "labels": ["A&B", "B"],
                            "series": [{"name": "safe", "values": [2, 4]}]})
        root = ET.fromstring(output["svg"])
        self.assertTrue(root.tag.endswith("svg"))
        self.assertNotIn("<script>", output["svg"])
        self.assertIn("&lt;script&gt;", output["svg"])

    def test_svg_chart_rejects_mismatched_series_and_bad_dimensions(self):
        with self.assertRaisesRegex(ToolInputError, "LENGTH_MISMATCH"):
            svg_chart({"labels": ["a", "b"], "series": [{"name": "x", "values": [1]}]})
        with self.assertRaisesRegex(ToolInputError, "INVALID_SIZE"):
            svg_chart({"labels": ["a"], "series": [{"name": "x", "values": [1]}], "width": 100})

    def test_link_card_rejects_dangerous_schemes_credentials_and_private_addresses(self):
        for url in ("javascript:alert(1)", "https://user:pass@example.com", "http://127.0.0.1",
                    "http://169.254.169.254/latest", "http://127.1", "https://localhost"):
            with self.subTest(url=url), self.assertRaises(ToolInputError):
                link_card({"url": url})

    def test_link_card_canonicalizes_safe_https_and_never_fetches(self):
        result = link_card({"url": "HTTPS://Example.COM:443/path", "title": "Example"})
        self.assertEqual(result["url"], "https://example.com/path")
        self.assertEqual(result["rel"], "noopener noreferrer nofollow")
        self.assertEqual(result["target"], "_blank")


if __name__ == "__main__":
    unittest.main()
