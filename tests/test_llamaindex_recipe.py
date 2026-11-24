import json
import tempfile
import unittest
from pathlib import Path

from examples.recipes import llamaindex_qa as recipe
from rag_evidence_lab.cli import main as cli_main
from rag_evidence_lab.core import inspect


RECIPES = Path(__file__).resolve().parents[1] / "examples" / "recipes"
INPUT = RECIPES / "llamaindex_qa_input.json"
CASES = RECIPES / "llamaindex_qa_cases.json"


class LlamaIndexRecipeTests(unittest.TestCase):
    def test_fixture_preserves_answers_and_matches_expected_flags(self):
        payload = json.loads(INPUT.read_text(encoding="utf-8"))
        generated = recipe.convert(payload)
        self.assertEqual(generated, json.loads(CASES.read_text(encoding="utf-8")))
        self.assertEqual(
            [c["answer"] for c in generated["cases"]],
            [r["response"] for r in payload["records"]],
        )
        self.assertEqual(generated["cases"][0]["sources"][0]["id"], "_loans")
        report = inspect(generated)
        flags = {c["id"]: c["claims"][0]["flags"] for c in report["cases"]}
        self.assertEqual(flags, {
            "loan-grounded": [],
            "loan-drift": ["unmatched_number"],
            "loan-uncited": ["missing_citation"],
        })

    def test_cli_export_and_flag_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "cases.json"
            self.assertEqual(recipe.main([str(INPUT), str(output)]), 0)
            self.assertEqual(output.read_bytes(), CASES.read_bytes())
            self.assertEqual(cli_main([str(output), "--max-flagged", "2"]), 0)
            self.assertEqual(cli_main([str(output), "--max-flagged", "1"]), 1)

    def test_sanitization_collision_preserves_citation_identity(self):
        record = {
            "response": "Books may be borrowed for 21 days [loans-md].",
            "source_nodes": [
                {"node": {"text": "First", "metadata": {"id": "loans-md"}}},
                {"node": {"text": "Second", "metadata": {"source": "handbook/loans.md"}}},
            ],
        }
        with self.assertRaisesRegex(ValueError, "duplicate source ID"):
            recipe.convert(record)

    def test_missing_source_node_text_is_rejected(self):
        record = {"response": "A response.", "source_nodes": [{"node": {"metadata": {}}}]}
        with self.assertRaisesRegex(ValueError, "non-empty"):
            recipe.convert(record)
