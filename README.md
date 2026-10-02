<p align="center"><img src="docs/assets/hero.svg" alt="RAG Evidence Lab: inspect the answer, follow the evidence" width="100%"></p>

# RAG Evidence Lab

**Catch broken citations and suspicious numbers before shipping your RAG answers.**

Your assistant says the refund window is **90 days**. The retrieved policy says **30**. The answer looks convincing—and even cites the right document. RAG Evidence Lab makes that mismatch visible.

[![Tests](https://github.com/manularrea/rag-evidence-lab/actions/workflows/tests.yml/badge.svg)](https://github.com/manularrea/rag-evidence-lab/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)
[![License: MIT](https://img.shields.io/badge/License-MIT-86d7cc.svg)](LICENSE)

**Runs locally · No API keys · No runtime dependencies · JSON + portable HTML**

[Quick start](#try-it-in-30-seconds) · [Input format](#bring-your-own-rag-run) · [How it works](#what-the-signals-mean) · [Español](docs/README.es.md) · [Contribute](CONTRIBUTING.md)

## Try it in 30 seconds

You only need Python 3.10+ and Git. No installation or model download required:

```bash
git clone https://github.com/manularrea/rag-evidence-lab.git
cd rag-evidence-lab
python -m rag_evidence_lab examples/demo.json --html report.html --json report.json
```

Open `report.html` in your browser. On Windows, use `py` instead of `python` if needed.

```text
4 cases · 4 claims · 3 flagged for review
  refund-drift: unmatched_number — Refunds are available within 90 days of purchase
  invented-reference: unknown_citation, low_lexical_overlap, unmatched_number — Support is available 24 hours per day
  missing-citation-es: missing_citation — La garantía dura 12 meses
Heuristic triage only: lexical overlap is not entailment or factuality.
```

<img src="docs/assets/demo.svg" alt="A grounded 30-day refund answer has no flags. A 90-day answer citing the same 30-day policy is flagged for an unmatched number." width="100%">

The demo is synthetic. The figures above come from the included fixture, not a benchmark of a real model.

## Why use it?

- **RAG engineers:** inspect exported answers without coupling evaluation to a model provider.
- **Reviewers:** open one HTML file, read each claim, and expand its retrieved sources.
- **Teams changing prompts or retrieval:** compare runs using stable case IDs and fail a CI check when heuristic flags increase.
- **Educators:** demonstrate why fluent answers and plausible citations do not guarantee factual support.

Use this as a lightweight first pass alongside human review or a semantic evaluator. It deliberately avoids an LLM judge, so every signal is repeatable and inspectable.

## Bring your own RAG run

Export a JSON object with a non-empty `cases` array:

```json
{
  "cases": [
    {
      "id": "refund-policy",
      "question": "How long do I have to request a refund?",
      "answer": "Refunds are available within 90 days of purchase [policy].",
      "sources": [
        {"id": "policy", "text": "Refunds are available within 30 days of purchase."}
      ]
    }
  ]
}
```

Use `[source-id]` citations inline, **before the sentence-ending punctuation**. Source IDs accept letters, digits, underscores and hyphens. Case IDs must be unique. `question` is optional; `id`, `answer`, and `sources` are required. Sources may be empty when retrieval returned nothing.

```bash
python -m rag_evidence_lab my-run.json --threshold 0.45 --html review.html
```

Already inside Python?

```python
from rag_evidence_lab.core import inspect

report = inspect({"cases": your_exported_cases}, threshold=0.45)
print(report["summary"])
```

Optional local installation exposes the `rag-evidence` command:

```bash
python -m pip install -e .
rag-evidence examples/demo.json --html report.html
```

The package is not published on PyPI. Editable installation may download the setuptools build tooling; the clone-and-run path uses only Python's standard library.

## What the signals mean

| Signal | What is checked | What it does **not** establish |
|---|---|---|
| `missing_citation` | No `[source-id]` in the claim | Whether the claim is false |
| `unknown_citation` | A citation ID is absent from retrieved sources | Whether another document supports it |
| `unmatched_number` | A normalized numeric value is absent from the eligible evidence | Whether the number is wrong, derived, or uses the same textual unit |
| `low_lexical_overlap` | Few claim tokens occur in the best matching source | Whether a paraphrase is unsupported |

Claims are split at newlines and simple sentence boundaries. Tokens are lowercased with a small English/Spanish stopword list. Lexical overlap is the fraction of distinct claim tokens found in a source. With citations, only cited known sources are eligible; without citations, all retrieved sources are considered, while the missing-citation flag remains.

Numeric comparison normalizes a conservative set of common English/Spanish presentations. Three-digit groups separated by comma, period, ordinary space, non-breaking space, or narrow non-breaking space are treated as thousands groups. When both comma and period occur, the rightmost separator is treated as the decimal mark only when the other separator forms valid three-digit groups. A single comma or period followed by exactly three digits is treated as a thousands separator only when the leading group has one to three digits and is not zero; leading-zero forms such as `0.125` and `0,125` remain fractional. Ambiguous non-zero forms keep the grouping rule, so `1.234` is treated as `1234`, while `1.2340` remains decimal. Under these assumptions, `1,000`, `1.000`, `1 000`, and `1000` compare equal, while `1,5` compares with `1.5` and not with `15`. A percent sign remains part of the normalized value, so `30%` does not match `30`.

This is deliberately not a full locale or unit parser. Textual units and currencies, scientific notation, malformed grouping, and conventions outside the assumptions above can still produce noisy numeric results.

**A report with zero flags is not proof of truth.** Negation, conflicting evidence, time scope, units, calculations, and semantically wrong but lexically similar statements can pass these checks. The test suite includes an explicit negation false negative. Abbreviations, lists, citation placement, multilingual paraphrases, and number formatting can produce noisy results. No accuracy claim is made for production datasets.

## Put a review gate in CI

Absolute budget (exit 1 when flagged claims exceed the allowed count):

```bash
python -m rag_evidence_lab my-run.json --max-flagged 0
```

Compare a candidate run with an earlier report:

```bash
python -m rag_evidence_lab baseline-run.json --json baseline.json
python -m rag_evidence_lab candidate-run.json --baseline baseline.json --json candidate.json
```

Both runs must use the same case IDs and overlap threshold. A case regresses when its **number of flagged claims increases**. This is a count-based signal: changed claims or failure types may go undetected when counts stay equal. Keep questions, sources and claim structure comparable when interpreting the result. It is not a quality score.

| Exit code | Meaning |
|---|---|
| `0` | Inspection completed and configured gates passed |
| `1` | Flag budget exceeded or a baseline regression was found |
| `2` | Invalid arguments/input/baseline, or file access error |

Without a gate, flagged claims do not cause a non-zero exit code.

## Privacy and portability

The inspector makes no network requests. Generated HTML contains no external scripts, fonts, or remote assets. **Reports include the full source text and answers**: review them before sharing or attaching them to an issue. The repository README's badge images are external; the generated reports are self-contained.

## Development

```bash
python -m unittest discover -s tests -v
```

The CI workflow tests Python 3.10 and 3.12, the example output, the console installation, and the regression gate. See [architecture and design choices](docs/design.md) and [the changelog](CHANGELOG.md).

## Help shape the next version

Small contributions are welcome: better claim splitting, numeric normalization, stronger multilingual fixtures, and exporter recipes. Start with [open issues](https://github.com/manularrea/rag-evidence-lab/issues), or read [CONTRIBUTING.md](CONTRIBUTING.md). Please include a minimal synthetic example; keep real customer data and API keys out of reports.

If this saves you a debugging session, **give the repository a star** so you can find it again—and share the use case that helped you. Useful examples and honest failure reports are especially welcome.

MIT licensed. Built for transparent inspection of AI outputs, not automatic certification of correctness.
