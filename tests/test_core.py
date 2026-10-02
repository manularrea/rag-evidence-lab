import unittest
from rag_evidence_lab.core import inspect, validate


def fixture(answer, text="Refunds are available within 30 days of purchase."):
    return {"cases": [{"id": "case", "answer": answer, "sources": [{"id": "p", "text": text}]}]}


class EvidenceTests(unittest.TestCase):
    def test_grounded(self):
        self.assertEqual(inspect(fixture("Refunds are available within 30 days of purchase [p]."))["summary"]["flagged_claims"], 0)

    def test_number_drift_even_with_high_overlap(self):
        claim = inspect(fixture("Refunds are available within 90 days of purchase [p]."))["cases"][0]["claims"][0]
        self.assertIn("unmatched_number", claim["flags"])
        self.assertGreater(claim["lexical_overlap"], .45)

    def test_numeric_formatting_normalization(self):
        cases = [
            ("Count is 1,000 [p].", "Count is 1000.", []),
            ("Count is 1 000 [p].", "Count is 1000.", []),
            ("Amount is 1,000.50 [p].", "Amount is 1000.5.", []),
            ("Cantidad: 1.000 [p].", "Cantidad: 1000.", []),
            ("Importe: 1.000,50 [p].", "Importe: 1000,50.", []),
            ("Tasa: 1,5 [p].", "Tasa: 1.5.", []),
            ("Tasa: 1,5 [p].", "Tasa: 15.", ["1,5"]),
            ("Rate is 30% [p].", "Rate is 30.", ["30%"]),
            ("Rate is 30 % [p].", "Rate is 30%.", []),
            ("Count is 1,000 [p].", "Count is 1.0.", ["1,000"]),
            ("Value is 0.125 [p].", "Value is 125.", ["0.125"]),
            ("Value is 0,125 [p].", "Value is 125.", ["0,125"]),
            ("Value is 1.234 [p].", "Value is 1.2340.", ["1.234"]),
        ]
        for answer, source, expected in cases:
            with self.subTest(answer=answer, source=source):
                claim = inspect(fixture(answer, source))["cases"][0]["claims"][0]
                self.assertEqual(claim["unmatched_numbers"], expected)

    def test_unknown_citation(self):
        self.assertIn("unknown_citation", inspect(fixture("Refunds [wrong]."))["cases"][0]["claims"][0]["flags"])

    def test_missing_citation(self):
        self.assertIn("missing_citation", inspect(fixture("Refunds within 30 days."))["cases"][0]["claims"][0]["flags"])

    def test_does_not_use_uncited_source_for_numbers(self):
        data = fixture("Refunds within 90 days [p].")
        data["cases"][0]["sources"].append({"id": "other", "text": "90 days"})
        self.assertIn("unmatched_number", inspect(data)["cases"][0]["claims"][0]["flags"])

    def test_decimal_not_split(self):
        self.assertEqual(inspect(fixture("Rate is 3.5 percent [p].", "Rate is 3.5 percent."))["summary"]["claims"], 1)

    def test_duplicate_ids_rejected(self):
        data = fixture("Test")
        data["cases"].append(data["cases"][0])
        with self.assertRaises(ValueError):
            validate(data)

    def test_negation_is_not_understood(self):
        # This intentionally documents the false negative: overlap cannot establish entailment.
        self.assertEqual(inspect(fixture("Refunds are not available within 30 days of purchase [p]."))["summary"]["flagged_claims"], 0)


if __name__ == "__main__":
    unittest.main()
