#!/usr/bin/env python3
"""Validate dataset_final_v3 outputs with strict rule checks."""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from build_dataset_final_v3 import validate_sample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate dataset_final_v3")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("dataset_final_v3"),
        help="Path to dataset_final_v3 directory",
    )
    return parser.parse_args()


def iter_jsonl(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield i, json.loads(line)
            except json.JSONDecodeError:
                yield i, None


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir

    split_files = []
    split_files.extend(input_dir.glob("**/*-single.jsonl"))
    split_files.extend(input_dir.glob("**/*-multiturn_clean.jsonl"))
    split_files.extend(input_dir.glob("**/*-multiturn_noisy.jsonl"))
    files = sorted(set(split_files))
    summary = {
        "total_files": len(files),
        "total_samples": 0,
        "valid_samples": 0,
    }
    by_file: Dict[str, Dict[str, Any]] = {}
    error_buckets = defaultdict(int)

    for file_path in files:
        total = 0
        valid = 0
        sample_errors: List[str] = []

        for line_no, item in iter_jsonl(file_path):
            total += 1
            summary["total_samples"] += 1

            if item is None:
                error_buckets["json_decode_error"] += 1
                if len(sample_errors) < 5:
                    sample_errors.append(f"line {line_no}: json_decode_error")
                continue

            ok, errors = validate_sample(item)
            if ok:
                valid += 1
                summary["valid_samples"] += 1
            else:
                for e in errors:
                    error_buckets[e] += 1
                if len(sample_errors) < 5:
                    sample_errors.append(f"line {line_no}: {','.join(errors)}")

        rate = (100.0 * valid / total) if total else 0.0
        by_file[str(file_path)] = {
            "total": total,
            "valid": valid,
            "rate": rate,
            "sample_errors": sample_errors,
        }

    overall_rate = (100.0 * summary["valid_samples"] / summary["total_samples"]) if summary["total_samples"] else 0.0

    report = {
        "summary": {
            **summary,
            "overall_rate": overall_rate,
        },
        "error_counts": dict(sorted(error_buckets.items(), key=lambda x: -x[1])),
        "by_file": by_file,
    }

    out_path = input_dir / "validation_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Validated files: {summary['total_files']}")
    print(f"Valid samples: {summary['valid_samples']}/{summary['total_samples']} ({overall_rate:.2f}%)")
    print(f"Report saved to: {out_path}")


if __name__ == "__main__":
    main()
