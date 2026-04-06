#!/usr/bin/env python3
"""Generate markdown diff tables for typed experiment before/after results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

INTERACTIONS = ["single", "multiturn_clean", "multiturn_noisy"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def overall_acc(records: Iterable[Dict[str, Any]], key: str) -> float:
    rows = list(records)
    if not rows:
        return 0.0
    return sum(1 for r in rows if r.get(key)) / len(rows)


def pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def delta_pct(x: float) -> str:
    return f"{x * 100:+.2f}%"


def main() -> None:
    args = parse_args()
    before = load_json(args.before)
    after = load_json(args.after)

    models = sorted(set(before.get("by_model", {}).keys()) & set(after.get("by_model", {}).keys()))

    lines: List[str] = []
    lines.append("# Typed对比实验：修复前 vs 修复后 差异表")
    lines.append("")
    lines.append(f"- before: {args.before.as_posix()}")
    lines.append(f"- after: {args.after.as_posix()}")
    lines.append("")

    for m in models:
        b_model_records = [r for r in before.get("records", []) if r.get("model") == m]
        a_model_records = [r for r in after.get("records", []) if r.get("model") == m]

        b_strict = overall_acc(b_model_records, "is_correct_strict")
        a_strict = overall_acc(a_model_records, "is_correct_strict")
        b_combined = overall_acc(b_model_records, "is_correct_combined")
        a_combined = overall_acc(a_model_records, "is_correct_combined")

        lines.append(f"## {m}")
        lines.append("")
        lines.append("| Overall | Before | After | Delta |")
        lines.append("|---|---:|---:|---:|")
        lines.append(f"| Strict Accuracy | {pct(b_strict)} | {pct(a_strict)} | {delta_pct(a_strict - b_strict)} |")
        lines.append(f"| Combined Accuracy | {pct(b_combined)} | {pct(a_combined)} | {delta_pct(a_combined - b_combined)} |")
        lines.append("")

        subtasks = sorted(
            set(before.get("by_model", {}).get(m, {}).keys())
            & set(after.get("by_model", {}).get(m, {}).keys())
        )

        lines.append("| Subtask | Interaction | Before | After | Delta |")
        lines.append("|---|---|---:|---:|---:|")
        for st in subtasks:
            for it in INTERACTIONS:
                b_val = float(before["by_model"][m].get(st, {}).get(it, {}).get("combined_accuracy", 0.0))
                a_val = float(after["by_model"][m].get(st, {}).get(it, {}).get("combined_accuracy", 0.0))
                lines.append(
                    f"| {st} | {it} | {pct(b_val)} | {pct(a_val)} | {delta_pct(a_val - b_val)} |"
                )
        lines.append("")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
