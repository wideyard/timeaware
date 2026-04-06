#!/usr/bin/env python3
"""Generate figures and example snippets for typed small-batch report."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

INPUT = Path("output/small_batch_interaction_compare_t1_t5_s20_typed.json")
FIG_DIR = Path("output/figures")
EXAMPLE_MD = Path("output/small_batch_interaction_examples.md")


def load():
    with open(INPUT, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dirs():
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def pick_examples(records):
    strict_ok = [r for r in records if r.get("is_correct_strict")]
    partial = [r for r in records if r.get("is_correct_partial")]
    fail = [r for r in records if not r.get("is_correct_combined")]

    # Prefer diverse subtasks.
    def first_by_subtask(rows):
        chosen = []
        seen = set()
        for r in rows:
            st = r.get("sub_task", "")
            if st in seen:
                continue
            seen.add(st)
            chosen.append(r)
            if len(chosen) >= 4:
                break
        return chosen

    return {
        "strict": first_by_subtask(strict_ok),
        "partial": first_by_subtask(partial),
        "fail": first_by_subtask(fail),
    }


def write_examples_md(examples):
    lines = ["## Example Cases", "", "### A. Strictly Correct Cases"]
    for i, r in enumerate(examples["strict"], start=1):
        lines.extend(
            [
                f"{i}. model={r['model']}, sub_task={r['sub_task']}, interaction={r['interaction_type']}",
                f"   - gold: {r['gold_answer']}",
                f"   - prediction: {r['prediction']}",
                "",
            ]
        )

    lines.append("### B. Partial-Correct Cases")
    for i, r in enumerate(examples["partial"], start=1):
        score_info = r.get("score_info", {})
        reason = score_info.get("partial_reason", "token_overlap")
        lines.extend(
            [
                f"{i}. model={r['model']}, sub_task={r['sub_task']}, interaction={r['interaction_type']}",
                f"   - gold: {r['gold_answer']}",
                f"   - prediction: {r['prediction']}",
                f"   - partial_reason: {reason}",
                "",
            ]
        )

    lines.append("### C. Incorrect Cases")
    for i, r in enumerate(examples["fail"], start=1):
        lines.extend(
            [
                f"{i}. model={r['model']}, sub_task={r['sub_task']}, interaction={r['interaction_type']}",
                f"   - gold: {r['gold_answer']}",
                f"   - prediction: {r['prediction']}",
                "",
            ]
        )

    with open(EXAMPLE_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def plot_overall(data):
    models = list(data["by_model"].keys())
    strict = []
    combined = []

    records = data["records"]
    for m in models:
        rows = [r for r in records if r["model"] == m]
        total = len(rows)
        s = sum(1 for r in rows if r.get("is_correct_strict")) / total
        c = sum(1 for r in rows if r.get("is_correct_combined")) / total
        strict.append(s * 100)
        combined.append(c * 100)

    x = np.arange(len(models))
    w = 0.36

    plt.figure(figsize=(8, 5))
    plt.bar(x - w / 2, strict, width=w, label="Strict")
    plt.bar(x + w / 2, combined, width=w, label="Combined")
    plt.ylabel("Accuracy (%)")
    plt.title("Overall Accuracy by Model")
    plt.xticks(x, models, rotation=15)
    plt.ylim(0, 100)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "overall_accuracy_by_model.png", dpi=180)
    plt.close()


def plot_interaction(data):
    models = list(data["by_model"].keys())
    interactions = ["single", "multiturn_clean", "multiturn_noisy"]

    mat = np.zeros((len(models), len(interactions)))
    for i, m in enumerate(models):
        submap = data["by_model"][m]
        counts = {k: [] for k in interactions}
        for _, row in submap.items():
            for k in interactions:
                counts[k].append(row.get(k, {}).get("combined_accuracy", 0.0) * 100)
        for j, k in enumerate(interactions):
            mat[i, j] = np.mean(counts[k]) if counts[k] else 0.0

    x = np.arange(len(models))
    w = 0.24

    plt.figure(figsize=(9, 5))
    for j, k in enumerate(interactions):
        plt.bar(x + (j - 1) * w, mat[:, j], width=w, label=k)
    plt.ylabel("Combined Accuracy (%)")
    plt.title("Interaction Style Effect by Model (Mean Across Subtasks)")
    plt.xticks(x, models, rotation=15)
    plt.ylim(0, 100)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "interaction_effect_by_model.png", dpi=180)
    plt.close()


def plot_subtask_heatmap(data):
    models = list(data["by_model"].keys())
    subtasks = sorted({k for m in models for k in data["by_model"][m].keys()})

    mat = np.zeros((len(models), len(subtasks)))
    for i, m in enumerate(models):
        for j, st in enumerate(subtasks):
            row = data["by_model"][m].get(st, {})
            s = row.get("single", {}).get("combined_accuracy", 0.0)
            c = row.get("multiturn_clean", {}).get("combined_accuracy", 0.0)
            n = row.get("multiturn_noisy", {}).get("combined_accuracy", 0.0)
            mat[i, j] = (s + c + n) / 3.0 * 100

    plt.figure(figsize=(11, 4.8))
    im = plt.imshow(mat, aspect="auto", cmap="YlOrRd", vmin=0, vmax=100)
    plt.colorbar(im, label="Mean Combined Accuracy (%)")
    plt.yticks(np.arange(len(models)), models)
    plt.xticks(np.arange(len(subtasks)), subtasks, rotation=30, ha="right")
    plt.title("Subtask Difficulty Heatmap (Mean Over Interaction Styles)")

    for i in range(len(models)):
        for j in range(len(subtasks)):
            plt.text(j, i, f"{mat[i, j]:.1f}", ha="center", va="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(FIG_DIR / "subtask_heatmap.png", dpi=180)
    plt.close()


def plot_answer_type(data):
    models = list(data["by_model_answer_type"].keys())
    atypes = sorted({k for m in models for k in data["by_model_answer_type"][m].keys()})

    x = np.arange(len(atypes))
    w = 0.24

    plt.figure(figsize=(10, 5))
    for i, m in enumerate(models):
        vals = []
        for a in atypes:
            vals.append(data["by_model_answer_type"][m].get(a, {}).get("combined_accuracy", 0.0) * 100)
        plt.bar(x + (i - 1) * w, vals, width=w, label=m)

    plt.ylabel("Combined Accuracy (%)")
    plt.title("Performance by Answer Type")
    plt.xticks(x, atypes)
    plt.ylim(0, 100)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "answer_type_comparison.png", dpi=180)
    plt.close()


def main():
    ensure_dirs()
    data = load()
    write_examples_md(pick_examples(data["records"]))
    plot_overall(data)
    plot_interaction(data)
    plot_subtask_heatmap(data)
    plot_answer_type(data)
    print("Generated figures and examples.")


if __name__ == "__main__":
    main()
