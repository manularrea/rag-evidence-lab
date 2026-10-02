"""Explainable surface checks for exported RAG runs."""
import re

STOP = set("a an the is are was were be to of in on for and or with as by it this that from can will must not all de del la el los las un una en para por y o con es son se que al como su sus no".split())


def tokens(text):
    return {t for t in re.findall(r"[^\W_]+", text.lower()) if t not in STOP and len(t) > 1}


NUMBER_LITERAL_RE = re.compile(
    r"(?<!\w)(?:\d{1,3}(?:[ \u00A0\u202F]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)*)(?:\s*%)?(?!\w)"
)


def _canonical_number(integer, fraction=None, percent=False):
    integer = integer.lstrip("0") or "0"
    if fraction is not None:
        fraction = fraction.rstrip("0")
    value = integer if not fraction else f"{integer}.{fraction}"
    return value + ("%" if percent else "")


def normalize_number_literal(raw):
    compact = raw.strip().replace("\u00A0", " ").replace("\u202F", " ")
    compact = re.sub(r"\s+", "", compact)
    percent = compact.endswith("%")
    if percent:
        compact = compact[:-1]

    if "," in compact and "." in compact:
        decimal_separator = "," if compact.rfind(",") > compact.rfind(".") else "."
        grouping_separator = "." if decimal_separator == "," else ","
        integer, fraction = compact.rsplit(decimal_separator, 1)
        groups = integer.split(grouping_separator)
        valid_grouping = (
            groups[0].isdigit()
            and 1 <= len(groups[0]) <= 3
            and all(group.isdigit() and len(group) == 3 for group in groups[1:])
            and fraction.isdigit()
        )
        if valid_grouping:
            return _canonical_number("".join(groups), fraction, percent)
        return raw.strip().replace(" ", "")

    separator = "," if "," in compact else "." if "." in compact else None
    if separator is not None:
        parts = compact.split(separator)
        if all(part.isdigit() for part in parts):
            if len(parts) > 2:
                if 1 <= len(parts[0]) <= 3 and all(len(part) == 3 for part in parts[1:]):
                    return _canonical_number("".join(parts), percent=percent)
                return raw.strip().replace(" ", "")
            integer, fraction = parts
            if integer != "0" and 1 <= len(integer) <= 3 and len(fraction) == 3:
                return _canonical_number(integer + fraction, percent=percent)
            return _canonical_number(integer, fraction, percent)

    if compact.isdigit():
        return _canonical_number(compact, percent=percent)
    return raw.strip().replace(" ", "")


def number_literals(text):
    return [
        (match.group(0).strip(), normalize_number_literal(match.group(0)))
        for match in NUMBER_LITERAL_RE.finditer(text)
    ]


def numbers(text):
    return {normalized for _, normalized in number_literals(text)}


def validate(data):
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list) or not data["cases"]:
        raise ValueError("Expected a non-empty 'cases' array")
    ids = set()
    for c in data["cases"]:
        if not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c["id"] or c["id"] in ids:
            raise ValueError("Case IDs must be non-empty unique strings")
        ids.add(c["id"])
        if not isinstance(c.get("answer"), str) or not c["answer"].strip():
            raise ValueError(f"{c['id']}: answer must be non-empty text")
        if not isinstance(c.get("sources"), list):
            raise ValueError(f"{c['id']}: sources must be an array")
        source_ids = set()
        for s in c["sources"]:
            if not isinstance(s, dict) or not isinstance(s.get("id"), str) or not re.fullmatch(r"[\w-]+", s["id"]):
                raise ValueError(f"{c['id']}: source IDs use letters, numbers, underscore or hyphen")
            if s["id"] in source_ids or not isinstance(s.get("text"), str) or not s["text"].strip():
                raise ValueError(f"{c['id']}: duplicate source ID or empty source text")
            source_ids.add(s["id"])
    return data


def inspect_case(case, threshold=0.45):
    sources = {s["id"]: s["text"] for s in case["sources"]}
    # Periods inside numeric values do not split a claim. Bullet/newline boundaries do.
    parts = re.split(r"(?<!\d)[.!?]+\s+|\n+", case["answer"].strip())
    claims = []
    for part in parts:
        if not part.strip():
            continue
        refs = re.findall(r"\[([\w-]+)\]", part)
        text = re.sub(r"\[[\w-]+\]", "", part).strip(" .!?-•")
        if not text:
            continue
        words = tokens(text)
        candidates = [r for r in refs if r in sources] if refs else list(sources)
        matches = []
        for sid in candidates:
            overlap = len(words & tokens(sources[sid])) / len(words) if words else 0.0
            matches.append((overlap, sid))
        best = max(matches, default=(0.0, None))
        evidence = " ".join(sources[r] for r in candidates)
        flags = []
        if not refs:
            flags.append("missing_citation")
        if any(r not in sources for r in refs):
            flags.append("unknown_citation")
        if best[0] < threshold:
            flags.append("low_lexical_overlap")
        evidence_numbers = numbers(evidence)
        absent = sorted({
            raw for raw, normalized in number_literals(text)
            if normalized not in evidence_numbers
        })
        if absent:
            flags.append("unmatched_number")
        claims.append({"text": text, "citations": refs, "best_source": best[1],
                       "lexical_overlap": round(best[0], 4), "unmatched_numbers": absent, "flags": flags})
    return {"id": case["id"], "question": case.get("question", ""), "claims": claims,
            "flagged_claims": sum(bool(c["flags"]) for c in claims), "claim_count": len(claims),
            "sources": case["sources"]}


def inspect(data, threshold=0.45):
    validate(data)
    cases = [inspect_case(c, threshold) for c in data["cases"]]
    return {"schema_version": 1, "threshold": threshold,
            "notice": "Heuristic triage only: lexical overlap is not entailment or factuality.",
            "summary": {"cases": len(cases), "claims": sum(c["claim_count"] for c in cases),
                        "flagged_claims": sum(c["flagged_claims"] for c in cases)}, "cases": cases}
