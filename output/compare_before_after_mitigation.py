#!/usr/bin/env python3
"""Compare before/after mitigation experiment outputs and produce diff report."""

import argparse
import json
from pathlib import Path
from typing import Dict, Any


INTERACTIONS = ["single", "multiturn_clean", "multiturn_noisy"]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    p.add_argument("--output-json", type=Path, default=Path("output/mitigation_diff.json"))
    p.add_argument("--output-md", type=Path, default=Path("output/mitigation_diff_report.md"))
    return p.parse_args()


def load(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def acc(rows):
    t = rows.get("total", 0)
    if t == 0:
        return 0.0
    return rows.get("strict_correct", 0) / t, rows.get("combined_accuracy", rows.get("strict_accuracy", 0.0))


def main():
    args = parse_args()
    b = load(args.before)
    a = load(args.after)

    out = {
        "before": str(args.before),
        "after": str(args.after),
        "models": {},
    }

    md = [
        "# Before/After Mitigation Difference Report",
        "",
        f"- before: {args.before}",
        f"- after: {args.after}",
        "",
    ]

    models = sorted(set(b.get("by_model", {}).keys()) & set(a.get("by_model", {}).keys()))

    for m in models:
        out["models"][m] = {"by_subtask": {}, "overall": {}}

        # overall from records
        b_rows = [r for r in b.get("records", []) if r.get("model") == m]
        a_rows = [r for r in a.get("records", []) if r.get("model") == m]

        def overall(rows):
            t = len(rows)
            if t == 0:
                return {"strict": 0.0, "combined": 0.0, "total": 0}
            strict = sum(1 for r in rows if r.get("is_correct_strict")) / t
            combined = sum(1 for r in rows if r.get("is_correct_combined")) / t
            return {"strict": strict, "combined": combined, "total": t}

        bo = overall(b_rows)
        ao = overall(a_rows)
        out["models"][m]["overall"] = {
            "before": bo,
            "after": ao,
            "delta_strict": ao["strict"] - bo["strict"],
            "delta_combined": ao["combined"] - bo["combined"],
        }

        md.append(f"## Model: {m}")
        md.append(
            f"- overall strict: {bo['strict']*100:.2f}% -> {ao['strict']*100:.2f}% (delta {((ao['strict']-bo['strict'])*100):+.2f}%)"
        )
        md.append(
            f"- overall combined: {bo['combined']*100:.2f}% -> {ao['combined']*100:.2f}% (delta {((ao['combined']-bo['combined'])*100):+.2f}%)"
        )
        md.append("")

        subtasks = sorted(set(b["by_model"].get(m, {}).keys()) & set(a["by_model"].get(m, {}).keys()))
        md.append("### Subtask Delta (combined)")
        for st in subtasks:
            out["models"][m]["by_subtask"][st] = {}
            b_row = b["by_model"][m][st]
            a_row = a["by_model"][m][st]
            line = [f"- {st}"]
            for it in INTERACTIONS:
                bc = b_row.get(it, {}).get("combined_accuracy", 0.0)
                ac = a_row.get(it, {}).get("combined_accuracy", 0.0)
                d = ac - bc
                out["models"][m]["by_subtask"][st][it] = {
                    "before_combined": bc,
                    "after_combined": ac,
                    "delta_combined": d,
                }
                line.append(f"{it}: {bc*100:.2f}% -> {ac*100:.2f}% ({d*100:+.2f}%)")
            md.append("; ".join(line))
        md.append("")

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open(args.output_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"Saved: {args.output_json}")
    print(f"Saved: {args.output_md}")


if __name__ == "__main__":
    main()
