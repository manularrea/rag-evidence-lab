"""Convert a documented LangChain RetrievalQA-style export into cases JSON.

This recipe is tested against a synthetic LangChain-shaped fixture that matches
the RetrievalQA / create_retrieval_chain source-document shape used by
LangChain 0.2 / 0.3 (page_content + metadata). The tests do not import
LangChain and do not exercise an installed LangChain version.

The recipe never invents bracketed citations: only IDs already present in the
answer, or IDs taken from document metadata, are preserved.

Usage:
    python examples/recipes/langchain_qa.py examples/recipes/langchain_qa_input.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


VALID_ID = re.compile(r"[\w-]+")


def _sanitize_filename(value: str) -> str:
    name = Path(value.strip()).name
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in name)
    cleaned = cleaned.strip("-_")
    return cleaned


def source_id(doc: dict, index: int) -> str:
    """Return a case-schema source ID for one LangChain-shaped document.

    An already-valid explicit ``metadata.id`` / ``source`` / ``filename`` is
    kept verbatim so citations such as ``[_policy]`` keep matching. Path-like
    or otherwise invalid values are sanitized to the allowed character set.
    """
    meta = doc.get("metadata") or {}
    for key in ("id", "source", "filename"):
        value = meta.get(key)
        if isinstance(value, str) and value.strip():
            raw = value.strip()
            if VALID_ID.fullmatch(raw):
                return raw
            cleaned = _sanitize_filename(raw)
            if cleaned:
                return cleaned
    return f"doc-{index + 1}"


def document_text(doc: dict) -> str:
    if isinstance(doc.get("page_content"), str) and doc["page_content"].strip():
        return doc["page_content"]
    if isinstance(doc.get("page_content"), dict):
        text = doc["page_content"].get("text") or doc["page_content"].get("page_content")
        if isinstance(text, str) and text.strip():
            return text
    raise ValueError("each source document needs non-empty page_content text")


def _add_source(doc: dict, index: int, seen: set, sources: list) -> None:
    if not isinstance(doc, dict):
        raise ValueError("source document must be an object")
    sid = source_id(doc, index)
    if sid in seen:
        raise ValueError(
            f"duplicate source ID {sid!r} after sanitization; "
            "refusing to rewrite an existing citation target"
        )
    seen.add(sid)
    sources.append({"id": sid, "text": document_text(doc)})


def convert_record(record: dict, index: int) -> dict:
    if not isinstance(record, dict):
        raise ValueError("each LangChain record must be an object")
    question = record.get("query") or record.get("question") or ""
    answer = record.get("result") or record.get("answer") or record.get("output_text")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("record is missing a non-empty answer/result")
    raw_docs = record.get("source_documents") or record.get("context") or []
    if not isinstance(raw_docs, list) or not raw_docs:
        raise ValueError("record is missing source_documents")
    sources = []
    seen = set()
    for i, doc in enumerate(raw_docs):
        _add_source(doc, i, seen, sources)
    case_id = record.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
        case_id = f"langchain-{index + 1}"
    return {
        "id": case_id,
        "question": question if isinstance(question, str) else "",
        "answer": answer,
        "sources": sources,
    }


def convert(payload) -> dict:
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict) and isinstance(payload.get("records"), list):
        records = payload["records"]
    elif isinstance(payload, dict):
        records = [payload]
    else:
        raise ValueError("expected a LangChain record, a list of records, or {records: [...]}")
    return {"cases": [convert_record(record, i) for i, record in enumerate(records)]}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: python examples/recipes/langchain_qa.py INPUT.json [OUTPUT.json]", file=sys.stderr)
        return 2
    src = Path(args[0])
    dest = Path(args[1]) if len(args) > 1 else None
    data = json.loads(src.read_text(encoding="utf-8"))
    cases = convert(data)
    text = json.dumps(cases, ensure_ascii=False, indent=2) + "\n"
    if dest:
        dest.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
