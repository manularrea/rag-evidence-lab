"""Convert a JSON export of non-streaming LlamaIndex text responses."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__:
    from .langchain_qa import convert_record
else:
    from langchain_qa import convert_record


def convert_node(item: object) -> dict:
    if not isinstance(item, dict) or not isinstance(item.get("node"), dict):
        raise ValueError("each source_nodes entry must contain a node object")
    node = item["node"]
    metadata = node.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("node metadata must be an object")
    return {"page_content": node.get("text"), "metadata": metadata}


def convert_response(record: object, index: int) -> dict:
    if not isinstance(record, dict):
        raise ValueError("each LlamaIndex response must be an object")
    nodes = record.get("source_nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("response needs a non-empty source_nodes array")
    case_id = record.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
        case_id = f"llamaindex-{index + 1}"
    return convert_record(
        {
            "id": case_id,
            "question": record.get("question"),
            "answer": record.get("response"),
            "source_documents": [convert_node(node) for node in nodes],
        },
        index,
    )


def convert(payload: object) -> dict:
    if isinstance(payload, dict) and "records" in payload:
        payload = payload["records"]
        if not isinstance(payload, list):
            raise ValueError("records must be an array")
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("expected a response object, a list, or {records: [...]}")
    return {"cases": [convert_response(record, i) for i, record in enumerate(payload)]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    args = parser.parse_args(argv)
    result = convert(json.loads(args.input.read_text(encoding="utf-8")))
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(text, end="")
    else:
        args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
