import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from rag_evidence_lab.cli import main as cli_main
from rag_evidence_lab.core import inspect


def _load_recipe():
    path = Path(__file__).resolve().parents[1] / "examples" / "recipes" / "langchain_qa.py"
    spec = importlib.util.spec_from_file_location("langchain_qa_recipe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


recipe = _load_recipe()
convert = recipe.convert
recipe_main = recipe.main


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "examples" / "recipes" / "langchain_qa_input.json"
FIXTURE = ROOT / "examples" / "recipes" / "langchain_qa_cases.json"


class LangChainRecipeTests(unittest.TestCase):
    def test_convert_preserves_ids_and_does_not_invent_citations(self):
        payload = json.loads(INPUT.read_text(encoding="utf-8"))
        cases = convert(payload)["cases"]
        self.assertEqual([c["id"] for c in cases], ["policy-grounded", "policy-drift", "hours-uncited"])
        self.assertEqual(cases[0]["sources"][0]["id"], "policy-md")
        self.assertIn("[policy-md]", cases[0]["answer"])
        self.assertNotIn("[", cases[2]["answer"])

    def test_checked_in_fixture_matches_converter_and_expected_flags(self):
        payload = json.loads(INPUT.read_text(encoding="utf-8"))
        generated = convert(payload)
        checked = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(generated, checked)
        report = inspect(checked)
        flags = {c["id"]: c["claims"][0]["flags"] for c in report["cases"]}
        self.assertEqual(flags["policy-grounded"], [])
        self.assertEqual(flags["policy-drift"], ["unmatched_number"])
        self.assertEqual(flags["hours-uncited"], ["missing_citation", "low_lexical_overlap"])
        self.assertEqual(report["summary"]["flagged_claims"], 2)

    def test_cli_accepts_fixture_under_documented_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            self.assertEqual(recipe_main([str(INPUT), str(out)]), 0)
            self.assertEqual(json.loads(out.read_text()), json.loads(FIXTURE.read_text()))
        self.assertEqual(cli_main([str(FIXTURE), "--max-flagged", "3"]), 0)
        self.assertEqual(cli_main([str(FIXTURE), "--max-flagged", "1"]), 1)

    def test_preserves_valid_explicit_id_with_leading_underscore(self):
        payload = {
            "id": "underscore-id",
            "query": "What is the policy?",
            "result": "See [_policy] for the rule.",
            "source_documents": [
                {"page_content": "The rule is stated in the policy.", "metadata": {"id": "_policy"}}
            ],
        }
        case = convert(payload)["cases"][0]
        self.assertEqual(case["sources"][0]["id"], "_policy")
        from rag_evidence_lab.core import validate, inspect
        validate({"cases": [case]})
        flags = inspect({"cases": [case]})["cases"][0]["claims"][0]["flags"]
        self.assertNotIn("unknown_citation", flags)

    def test_duplicate_explicit_ids_raise_instead_of_rewriting(self):
        payload = {
            "query": "q",
            "result": "answer [a]",
            "source_documents": [
                {"page_content": "first", "metadata": {"id": "a"}},
                {"page_content": "second", "metadata": {"id": "a-3"}},
                {"page_content": "third", "metadata": {"id": "a"}},
            ],
        }
        with self.assertRaises(ValueError) as ctx:
            convert(payload)
        self.assertIn("duplicate source ID", str(ctx.exception))

    def test_sanitization_collision_raises(self):
        payload = {
            "query": "q",
            "result": "answer",
            "source_documents": [
                {"page_content": "first", "metadata": {"filename": "notes.md"}},
                {"page_content": "second", "metadata": {"filename": "notes.md"}},
            ],
        }
        with self.assertRaises(ValueError) as ctx:
            convert(payload)
        self.assertIn("duplicate source ID", str(ctx.exception))

    def test_recipe_does_not_import_langchain(self):
        import sys
        self.assertNotIn("langchain", sys.modules)
