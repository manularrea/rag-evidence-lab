# Exporter recipes

Small, dependency-free converters that turn a documented RAG export into the
`{"cases": [...]}` schema used by `rag-evidence`.

## LangChain RetrievalQA (0.2 / 0.3 document shape)

Checked with a **synthetic, LangChain-shaped fixture** that mirrors the
`source_documents` object used by RetrievalQA / create_retrieval_chain
(page_content + optional metadata `id` / `source` / `filename`). The tests
do **not** import LangChain and were not run against an installed LangChain
version. The recipe does not call a model.

### Citation formatting

- Source IDs come from `metadata.id`, then `metadata.source`, then
  `metadata.filename`, then `doc-N`. Path prefixes are dropped.
- An explicit ID that is already valid (`letters`, `numbers`, `_`, `-`,
  including a leading underscore such as `_policy`) is kept verbatim.
- Filenames such as `policy.md` become `policy-md` because case source IDs
  allow only letters, numbers, underscore and hyphen.
- If two documents sanitize or collide onto the same ID, conversion raises
  instead of suffixing an ID that an existing citation already refers to.
- Bracketed citations already present in the answer (for example `[policy-md]`)
  are left unchanged so they can match those IDs.
- The recipe **does not invent** `[source]` markers when the model answer
  omitted them. Those cases are expected to receive `missing_citation`.

### Convert and inspect

```bash
python examples/recipes/langchain_qa.py \
  examples/recipes/langchain_qa_input.json \
  examples/recipes/langchain_qa_cases.json

python -m rag_evidence_lab examples/recipes/langchain_qa_cases.json --max-flagged 3
```

Expected CLI flags on the checked-in fixture:

| case            | expected flags                          |
|-----------------|-----------------------------------------|
| policy-grounded | none                                    |
| policy-drift    | `unmatched_number`                      |
| hours-uncited   | `missing_citation`, `low_lexical_overlap` |

`--max-flagged 3` is the budget for this fixture (two flagged claims). Raise
it only if you add cases.

No credentials or remote model execution are required.
