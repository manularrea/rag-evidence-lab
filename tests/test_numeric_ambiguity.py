"""Regression coverage for the maintainer's no-silent-value-collapse contract."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from rag_evidence_lab.cli import main
from rag_evidence_lab.core import inspect, numbers


def case(answer_number, source_number):
    return {"cases": [{"id": "numeric", "answer": f"The value is {answer_number} units [p].",
                      "sources": [{"id": "p", "text": f"The value is {source_number} units."}]}]}


class NumericAmbiguityTests(unittest.TestCase):
    def test_ambiguous_forms_never_guess_thousands_or_decimals(self):
        for ambiguous, alternative in [
            ("1.234", "1234"), ("1,234", "1234"),
            ("1.234", "1.2340"), ("1,234", "1.2340"),
            ("1,000", "1000"), ("1.000", "1000"),
            ("12.345", "12345"), ("12,345", "12.3450"),
            ("1.234%", "1234%"), ("1,234%", "1.2340%"),
        ]:
            for answer, source in [(ambiguous, alternative), (alternative, ambiguous)]:
                with self.subTest(answer=answer, source=source):
                    self.assertNotEqual(numbers(answer), numbers(source))
                    claim = inspect(case(answer, source))["cases"][0]["claims"][0]
                    self.assertIn("unmatched_number", claim["flags"])
                    self.assertEqual(claim["unmatched_numbers"], [answer])

    def test_exact_ambiguous_spelling_can_match_itself(self):
        for value in ["1.234", "1,234", "1,000", "1.234%"]:
            with self.subTest(value=value):
                claim = inspect(case(value, value))["cases"][0]["claims"][0]
                self.assertNotIn("unmatched_number", claim["flags"])
        self.assertEqual(numbers("1.234 %"), numbers("1.234%"))
        self.assertNotEqual(numbers("1.234%"), numbers("1.234"))

    def test_zero_integer_groups_remain_fractional(self):
        for value in ["0.125", "0,125", "00.125", "000,125"]:
            with self.subTest(value=value):
                self.assertEqual(numbers(value), numbers("0.1250"))
                self.assertNotEqual(numbers(value), numbers("125"))
                self.assertEqual(inspect(case(value, "125"))["cases"][0]["claims"][0]["unmatched_numbers"], [value])

    def test_unambiguous_grouping_and_percent_semantics_remain(self):
        for left, right in [
            ("1 000", "1000"), ("1\u00a0000", "1000"), ("1\u202f000", "1000"),
            ("1,000.50", "1000.5"), ("1.000,50", "1000,50"),
            ("1,234,567", "1234567"), ("1.234.567", "1234567"),
            ("1,5", "1.5"), ("30 %", "30%"),
        ]:
            with self.subTest(left=left, right=right):
                self.assertEqual(numbers(left), numbers(right))
        self.assertNotEqual(numbers("30%"), numbers("30"))
        self.assertNotEqual(numbers("1,5"), numbers("15"))

    def test_cli_gate_catches_ambiguous_mismatch_and_preserves_spelling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, report = root / "input.json", root / "report.json"
            source.write_text(json.dumps(case("1.234", "1234")), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main([str(source), "--json", str(report), "--max-flagged", "0"])
            self.assertEqual(exit_code, 1)
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["cases"][0]["claims"][0]["unmatched_numbers"], ["1.234"])
