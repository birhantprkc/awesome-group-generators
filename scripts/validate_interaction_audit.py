#!/usr/bin/env python3
"""Check interaction feature coverage and evidence against the public catalog."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "tools.json"
EVIDENCE = ROOT / "data" / "review-evidence" / "interaction-features-2026-09-23.json"
FEATURES = (
    "Progressive group reveal",
    "Interactive assignment process",
    "Manual post-generation editing",
)
VALUES = {"yes", "partial", "no"}
BASES = {"live", "official-docs", "existing-review", "no-visible-support"}


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    audit = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    tools = catalog["tools"]
    rows = audit["tools"]
    assert audit["fields"] == list(FEATURES)
    assert len(tools) == catalog["metadata"]["toolCount"] == len(rows)
    assert len({row["id"] for row in rows}) == len(rows)

    evidence_by_id = {row["id"]: row for row in rows}
    counts = {feature: Counter() for feature in FEATURES}
    for tool in tools:
        row = evidence_by_id[tool["id"]]
        assert row["rank"] == tool["rank"], tool["id"]
        assert set(row["features"]) == set(FEATURES), tool["id"]
        assert set(row["evidence"]) == set(FEATURES), tool["id"]
        assert row["confidence"] in {"high", "medium", "low"}, tool["id"]
        for feature in FEATURES:
            value = row["features"][feature]
            source = row["evidence"][feature]
            assert value in VALUES, (tool["id"], feature, value)
            assert tool["features"][feature] == value, (tool["id"], feature)
            assert source["basis"] in BASES, (tool["id"], feature)
            assert isinstance(source["note"], str) and source["note"].strip(), (tool["id"], feature)
            assert isinstance(source["url"], str), (tool["id"], feature)
            if source["basis"] in {"live", "official-docs"}:
                assert source["url"].startswith("http"), (tool["id"], feature)
            if value != "no":
                assert source["basis"] != "no-visible-support", (tool["id"], feature)
            counts[feature][value] += 1

    for feature in FEATURES:
        print(f"{feature}: {dict(counts[feature])}")
    confidence = Counter(row["confidence"] for row in rows)
    print(f"Review confidence: {dict(confidence)}")
    print(f"Validated {len(rows)} tool reviews and {len(rows) * len(FEATURES)} feature decisions")


if __name__ == "__main__":
    main()
