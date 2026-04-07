#!/usr/bin/env python3
"""Generate a per-subtask casebook with original conversations.

For each subtask, select at least:
- one correct case
- one incorrect case

Cases are pulled from the typed post-fix result file and enriched with the
original conversation from dataset_final_v3.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

INTERACTION_ORDER = {"single": 0, "multiturn_clean": 1, "multiturn_noisy": 2}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--result",
        type=Path,
        default=Path("output/small_batch_interaction_compare_t1_t5_s20_typed_post_hellaswag_fix.json"),
    )
    p.add_argument("--dataset-dir", type=Path, default=Path("dataset_final_v3"))
    p.add_argument("--model", type=str, default="gpt-4o-mini")
    p.add_argument(
        "--output",
        type=Path,
        default=Path("output/subtask_casebook_with_conversations.md"),
    )
    return p.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def find_sample(dataset_dir: Path, subtask: str, interaction: str, source_id: str) -> Optional[Dict[str, Any]]:
    task_prefix = subtask.split("-")[0]
    p = dataset_dir / task_prefix / f"{subtask}-{interaction}.jsonl"
    if not p.exists():
        return None
    for row in read_jsonl(p):
        if str(row.get("source_id", "")).strip() == source_id:
            return row
    return None


def rank_key(rec: Dict[str, Any]) -> Tuple[int, int]:
    # Prefer single, then clean, then noisy; then shorter prediction text.
    it = rec.get("interaction_type", "single")
    pred_len = len(str(rec.get("prediction", "")))
    return (INTERACTION_ORDER.get(it, 99), pred_len)


def pick_case(records: List[Dict[str, Any]], want_correct: bool) -> Optional[Dict[str, Any]]:
    if want_correct:
        strict_cands = [r for r in records if bool(r.get("is_correct_strict"))]
        if strict_cands:
            strict_cands.sort(key=rank_key)
            return strict_cands[0]

        # Fallback: combined-correct if no strict-correct exists.
        comb_cands = [r for r in records if bool(r.get("is_correct_combined"))]
        if comb_cands:
            comb_cands.sort(key=rank_key)
            return comb_cands[0]
        return None

    cands = [r for r in records if not bool(r.get("is_correct_combined"))]
    if not cands:
        return None
    cands.sort(key=rank_key)
    return cands[0]


def render_conversation(conv: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for turn in conv:
        role = str(turn.get("role", "user")).upper()
        content = str(turn.get("content", "")).strip()
        if not content:
            continue
        lines.append(f"[{role}] {content}")
    return "\n\n".join(lines)


def analyze_case(gold: str, pred: str, ok: bool) -> str:
    g = (gold or "").strip()
    p = (pred or "").strip()
    if ok:
        if len(g) == 1 and g in "ABCD":
            return "模型正确锁定了选项字母，说明其在候选约束下能完成定位与选择。"
        return "模型答案与标准答案语义一致或满足类型化判分规则，推理链路与输出格式匹配。"

    if len(g) == 1 and g in "ABCD":
        return f"这是典型的选项混淆：标准答案为 {g}，但模型输出为 {p or '空输出'}。"

    if g.lower() in ("yes", "no") or "overlap" in g.lower():
        return "这是极性判断错误（yes/no 方向反转），通常来自时间线整合失败。"

    return "模型输出与目标片段不一致，表现为关键信息遗漏或改写方向偏移。"


def main() -> None:
    args = parse_args()
    data = load_json(args.result)

    records = [r for r in data.get("records", []) if r.get("model") == args.model]
    by_subtask: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        st = str(r.get("sub_task", "")).strip()
        if not st:
            continue
        by_subtask.setdefault(st, []).append(r)

    subtasks = sorted(by_subtask.keys())

    lines: List[str] = []
    lines.append("# 子任务案例文档（含原始 Conversations）")
    lines.append("")
    lines.append(f"- 结果文件: {args.result.as_posix()}")
    lines.append(f"- 数据目录: {args.dataset_dir.as_posix()}")
    lines.append(f"- 模型: {args.model}")
    lines.append("- 说明: 每个子任务至少给出 1 个正确案例和 1 个错误案例。")
    lines.append("")

    for st in subtasks:
        lines.append(f"## {st}")
        rows = by_subtask.get(st, [])

        correct = pick_case(rows, True)
        wrong = pick_case(rows, False)

        if correct is None:
            lines.append("### 正确案例")
            lines.append("- 未找到正确样本。")
            lines.append("")
        else:
            sid = str(correct.get("source_id", ""))
            it = str(correct.get("interaction_type", ""))
            sample = find_sample(args.dataset_dir, st, it, sid)
            lines.append("### 正确案例")
            lines.append(f"- source_id: {sid}")
            lines.append(f"- interaction_type: {it}")
            lines.append(f"- gold: {correct.get('gold_answer', '')}")
            lines.append(f"- prediction: {correct.get('prediction', '')}")
            lines.append(f"- is_correct_strict: {bool(correct.get('is_correct_strict'))}")
            lines.append(f"- is_correct_partial: {bool(correct.get('is_correct_partial'))}")
            lines.append(f"- is_correct_combined: {bool(correct.get('is_correct_combined'))}")
            lines.append(f"- 分析: {analyze_case(str(correct.get('gold_answer', '')), str(correct.get('prediction', '')), True)}")
            lines.append("- 原始 conversation:")
            lines.append("")
            lines.append("```text")
            if sample and isinstance(sample.get("conversation"), list):
                lines.append(render_conversation(sample.get("conversation", [])))
            else:
                lines.append("(conversation not found)")
            lines.append("```")
            lines.append("")

        if wrong is None:
            lines.append("### 错误案例")
            lines.append("- 未找到错误样本。")
            lines.append("")
        else:
            sid = str(wrong.get("source_id", ""))
            it = str(wrong.get("interaction_type", ""))
            sample = find_sample(args.dataset_dir, st, it, sid)
            lines.append("### 错误案例")
            lines.append(f"- source_id: {sid}")
            lines.append(f"- interaction_type: {it}")
            lines.append(f"- gold: {wrong.get('gold_answer', '')}")
            lines.append(f"- prediction: {wrong.get('prediction', '')}")
            lines.append(f"- is_correct_strict: {bool(wrong.get('is_correct_strict'))}")
            lines.append(f"- is_correct_partial: {bool(wrong.get('is_correct_partial'))}")
            lines.append(f"- is_correct_combined: {bool(wrong.get('is_correct_combined'))}")
            lines.append(f"- 分析: {analyze_case(str(wrong.get('gold_answer', '')), str(wrong.get('prediction', '')), False)}")
            lines.append("- 原始 conversation:")
            lines.append("")
            lines.append("```text")
            if sample and isinstance(sample.get("conversation"), list):
                lines.append(render_conversation(sample.get("conversation", [])))
            else:
                lines.append("(conversation not found)")
            lines.append("```")
            lines.append("")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
