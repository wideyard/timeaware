#!/usr/bin/env python3
"""Small-batch experiment for single vs multiturn_clean vs multiturn_noisy."""

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import EVAL_MODELS
from llm_client import call_llm

INTERACTION_TYPES = ["single", "multiturn_clean", "multiturn_noisy"]
YESNO_WORD_RE = re.compile(r"\b(yes|no)\b", re.IGNORECASE)
LETTER_RE = re.compile(r"\b([A-D])\b", re.IGNORECASE)


def tokenize(s: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", normalize_text(s))


def token_f1(pred: str, gold: str) -> float:
    pt = tokenize(pred)
    gt = tokenize(gold)
    if not pt or not gt:
        return 0.0
    pcount = defaultdict(int)
    gcount = defaultdict(int)
    for t in pt:
        pcount[t] += 1
    for t in gt:
        gcount[t] += 1
    overlap = 0
    for t in pcount:
        overlap += min(pcount[t], gcount.get(t, 0))
    if overlap == 0:
        return 0.0
    precision = overlap / len(pt)
    recall = overlap / len(gt)
    return (2 * precision * recall) / (precision + recall)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run small-batch interaction comparison")
    parser.add_argument("--input-dir", type=Path, default=Path("dataset_final_v3"))
    parser.add_argument("--samples-per-subtask", type=int, default=20)
    parser.add_argument("--max-subtasks", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--models", type=str, default=",".join(EVAL_MODELS))
    parser.add_argument("--subtasks", type=str, default="")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--output", type=Path, default=Path("output/small_batch_interaction_compare.json"))
    parser.add_argument(
        "--risk-mode",
        type=str,
        choices=["none", "filter", "repair"],
        default="none",
        help="How to handle high-risk single samples: none/filter/repair",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def normalize_text(s: Any) -> str:
    s = "" if s is None else str(s)
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def extract_numbers(s: str) -> List[str]:
    return re.findall(r"-?\d+(?:\.\d+)?", s)


def answers_match(pred: str, gold: str) -> bool:
    p = normalize_text(pred)
    g = normalize_text(gold)
    if not p or not g:
        return False

    if p == g:
        return True

    if p in g or g in p:
        return True

    pn = extract_numbers(p)
    gn = extract_numbers(g)
    if pn and gn and pn == gn:
        return True

    return False


def infer_answer_type(gold: str) -> str:
    g = normalize_text(gold)
    if re.fullmatch(r"[a-d]", g):
        return "mc"
    if re.search(r"\boption\s*[a-d]\b", g):
        return "mc"
    if re.search(r"\b(correct answer is|answer is)\s*[a-d]\b", g):
        return "mc"
    if YESNO_WORD_RE.search(g) and len(tokenize(g)) <= 12:
        return "yesno"
    if len(tokenize(g)) <= 12:
        return "span"
    return "free_form"


def get_gt_key_phrase(sample: Dict[str, Any]) -> str:
    gt = sample.get("ground_truth", {})
    if isinstance(gt, dict):
        for k in ["correct", "answer", "gold_answer", "next_step", "current_state", "result", "duration"]:
            v = gt.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    ans = str(sample.get("answer", "")).strip()
    return ans


def is_high_risk_single(single_sample: Dict[str, Any], clean_sample: Dict[str, Any]) -> bool:
    single_txt = "\n".join(t.get("content", "") for t in single_sample.get("conversation", []))
    clean_txt = "\n".join(t.get("content", "") for t in clean_sample.get("conversation", []))
    if "..." not in single_txt:
        return False

    key = normalize_text(get_gt_key_phrase(single_sample))
    key_tokens = [t for t in tokenize(key) if len(t) >= 4][:6]
    if not key_tokens:
        return False

    s = normalize_text(single_txt)
    c = normalize_text(clean_txt)
    in_single = any(t in s for t in key_tokens)
    in_clean = any(t in c for t in key_tokens)
    return (not in_single) and in_clean


def repair_single_from_clean(single_sample: Dict[str, Any], clean_sample: Dict[str, Any]) -> Dict[str, Any]:
    repaired = dict(single_sample)
    clean_conv = clean_sample.get("conversation", [])
    if not clean_conv:
        return repaired

    user_turns = [t.get("content", "") for t in clean_conv if t.get("role") == "user" and t.get("content")]
    question = user_turns[-1] if user_turns else ""
    context_turns = clean_conv[:-1] if len(clean_conv) > 1 else clean_conv
    context_lines = []
    for t in context_turns:
        role = t.get("role", "user").upper()
        content = str(t.get("content", "")).strip()
        if content:
            context_lines.append(f"{role}: {content}")

    merged = ""
    if context_lines:
        merged += "Context:\n" + "\n".join(context_lines)
    if question:
        if merged:
            merged += "\n\n"
        merged += f"Question: {question}"

    repaired["conversation"] = [{"role": "user", "content": merged.strip()}]
    meta = dict(repaired.get("metadata", {}))
    meta["risk_repaired_single"] = True
    repaired["metadata"] = meta
    return repaired


def extract_mc_letter(text: str) -> str:
    t = normalize_text(text).upper()
    m = LETTER_RE.search(t)
    if m:
        return m.group(1).upper()
    return ""


def extract_gold_mc_letter(gold: str) -> str:
    g = normalize_text(gold).upper()
    if re.fullmatch(r"[A-D]", g):
        return g
    m = re.search(r"OPTION\s*([A-D])", g)
    if m:
        return m.group(1)
    m = re.search(r"(?:ANSWER\s+IS|CORRECT\s+ANSWER\s+IS)\s*([A-D])", g)
    if m:
        return m.group(1)
    return ""


def extract_yesno(text: str) -> str:
    m = YESNO_WORD_RE.search(normalize_text(text))
    if not m:
        return ""
    return m.group(1).lower()


def make_prompt(sample: Dict[str, Any], answer_type: str) -> str:
    conv_text = render_conversation(sample.get("conversation", []))

    if answer_type == "mc":
        answer_rule = "Return exactly one uppercase letter: A, B, C, or D."
    elif answer_type == "yesno":
        answer_rule = "Return exactly one word: yes or no."
    elif answer_type == "span":
        answer_rule = "Return a short extracted answer phrase from the conversation."
    else:
        answer_rule = "Return one concise final answer sentence."

    return (
        "You are answering a temporal reasoning QA sample.\n"
        f"{answer_rule}\n"
        "Do not output explanation.\n\n"
        "Conversation:\n"
        f"{conv_text}\n\n"
        "Return only the answer."
    )


def score_answer(pred: str, gold: str, subtask: str, answer_type: str) -> Tuple[bool, bool, Dict[str, Any]]:
    info: Dict[str, Any] = {"answer_type": answer_type}
    p = pred.strip()
    g = gold.strip()

    if answer_type == "mc":
        pred_letter = extract_mc_letter(p)
        gold_letter = extract_gold_mc_letter(g)
        strict_ok = bool(pred_letter and gold_letter and pred_letter == gold_letter)
        info.update({"pred_letter": pred_letter, "gold_letter": gold_letter})
        return strict_ok, False, info

    if answer_type == "yesno":
        pred_yn = extract_yesno(p)
        gold_yn = extract_yesno(g)
        strict_ok = bool(pred_yn and gold_yn and pred_yn == gold_yn)
        info.update({"pred_yesno": pred_yn, "gold_yesno": gold_yn})
        return strict_ok, False, info

    f1 = token_f1(p, g)
    strict_ok = False
    partial_ok = False

    if answer_type == "span":
        strict_ok = answers_match(p, g) or f1 >= 0.70
        partial_ok = (not strict_ok) and (f1 >= 0.35)
    else:
        strict_ok = answers_match(p, g) or f1 >= 0.65
        partial_ok = (not strict_ok) and (f1 >= 0.40)

        # Status-task partial credit: state captured but next-step detail missing.
        if (not strict_ok) and ("status" in subtask.lower()):
            gnorm = normalize_text(g)
            pnorm = normalize_text(p)
            has_next_step = ("next logical step" in gnorm) or ("next step" in gnorm)
            status_hit = any(k in pnorm for k in ["in progress", "completed", "ongoing", "finished"])
            if has_next_step and status_hit:
                partial_ok = True
                info["partial_reason"] = "status_only_without_next_step"

    info["token_f1"] = f1
    return strict_ok, partial_ok, info


def render_conversation(conv: List[Dict[str, str]]) -> str:
    lines = []
    for turn in conv:
        role = turn.get("role", "user")
        content = str(turn.get("content", "")).strip()
        if not content:
            continue
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)


def discover_subtasks(input_dir: Path) -> List[str]:
    subtasks = set()
    for p in input_dir.glob("T*/*-single.jsonl"):
        stem = p.stem
        if stem.endswith("-single"):
            subtasks.add(stem[: -len("-single")])
    return sorted(subtasks)


def load_triplets_for_subtask(input_dir: Path, subtask: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
    buckets: Dict[str, Dict[str, Dict[str, Any]]] = {itype: {} for itype in INTERACTION_TYPES}
    for itype in INTERACTION_TYPES:
        path = input_dir / subtask.split("-")[0] / f"{subtask}-{itype}.jsonl"
        if not path.exists():
            continue
        rows = read_jsonl(path)
        for row in rows:
            sid = str(row.get("source_id", "")).strip()
            if not sid:
                continue
            buckets[itype][sid] = row
    return buckets


def pick_matched_samples(
    buckets: Dict[str, Dict[str, Dict[str, Any]]], samples_per_subtask: int, rng: random.Random
) -> List[Tuple[str, Dict[str, Dict[str, Any]]]]:
    common_ids = set(buckets["single"].keys())
    common_ids &= set(buckets["multiturn_clean"].keys())
    common_ids &= set(buckets["multiturn_noisy"].keys())
    common_ids = sorted(common_ids)

    if not common_ids:
        return []

    if len(common_ids) > samples_per_subtask:
        chosen = sorted(rng.sample(common_ids, samples_per_subtask))
    else:
        chosen = common_ids

    matched = []
    for sid in chosen:
        matched.append(
            (
                sid,
                {
                    "single": buckets["single"][sid],
                    "multiturn_clean": buckets["multiturn_clean"][sid],
                    "multiturn_noisy": buckets["multiturn_noisy"][sid],
                },
            )
        )
    return matched


def apply_risk_mode_to_pairs(
    pairs: List[Tuple[str, Dict[str, Dict[str, Any]]]],
    risk_mode: str,
) -> Tuple[List[Tuple[str, Dict[str, Dict[str, Any]]]], Dict[str, int]]:
    stats = {"flagged": 0, "filtered": 0, "repaired": 0}
    out: List[Tuple[str, Dict[str, Dict[str, Any]]]] = []

    for sid, trio in pairs:
        single = trio["single"]
        clean = trio["multiturn_clean"]
        risk = is_high_risk_single(single, clean)

        if risk:
            stats["flagged"] += 1
            if risk_mode == "filter":
                stats["filtered"] += 1
                continue
            if risk_mode == "repair":
                trio = dict(trio)
                trio["single"] = repair_single_from_clean(single, clean)
                stats["repaired"] += 1

        out.append((sid, trio))

    return out, stats


def evaluate_samples(
    models: List[str],
    sampled: Dict[str, List[Tuple[str, Dict[str, Dict[str, Any]]]]],
    temperature: float,
) -> Dict[str, Any]:
    records = []
    metrics = defaultdict(
        lambda: defaultdict(
            lambda: {
                "strict_correct": 0,
                "partial_correct": 0,
                "total": 0,
            }
        )
    )

    type_stats = defaultdict(lambda: defaultdict(lambda: {"strict_correct": 0, "partial_correct": 0, "total": 0}))

    for model in models:
        for subtask, pairs in sampled.items():
            for source_id, trio in pairs:
                for itype in INTERACTION_TYPES:
                    sample = trio[itype]
                    gold = str(sample.get("answer", "")).strip()
                    answer_type = infer_answer_type(gold)
                    prompt = make_prompt(sample, answer_type)
                    try:
                        pred = call_llm(prompt, temperature=temperature, model_key=model).strip()
                        strict_ok, partial_ok, info = score_answer(pred, gold, subtask, answer_type)
                        if strict_ok:
                            metrics[model][(subtask, itype)]["strict_correct"] += 1
                            type_stats[model][answer_type]["strict_correct"] += 1
                        elif partial_ok:
                            metrics[model][(subtask, itype)]["partial_correct"] += 1
                            type_stats[model][answer_type]["partial_correct"] += 1

                        metrics[model][(subtask, itype)]["total"] += 1
                        type_stats[model][answer_type]["total"] += 1

                        records.append(
                            {
                                "model": model,
                                "sub_task": subtask,
                                "interaction_type": itype,
                                "source_id": source_id,
                                "answer_type": answer_type,
                                "gold_answer": gold,
                                "prediction": pred,
                                "is_correct_strict": strict_ok,
                                "is_correct_partial": (not strict_ok) and partial_ok,
                                "is_correct_combined": strict_ok or partial_ok,
                                "score_info": info,
                            }
                        )
                    except Exception as e:
                        metrics[model][(subtask, itype)]["total"] += 1
                        records.append(
                            {
                                "model": model,
                                "sub_task": subtask,
                                "interaction_type": itype,
                                "source_id": source_id,
                                "answer_type": answer_type,
                                "gold_answer": gold,
                                "prediction": "",
                                "is_correct_strict": False,
                                "is_correct_partial": False,
                                "is_correct_combined": False,
                                "error": str(e),
                            }
                        )

    summary = {"by_model": {}, "by_model_answer_type": {}, "records": records}

    for model in models:
        by_subtask = {}
        for key, val in metrics[model].items():
            subtask, itype = key
            strict_acc = val["strict_correct"] / val["total"] if val["total"] else 0.0
            partial_acc = val["partial_correct"] / val["total"] if val["total"] else 0.0
            combined_acc = (val["strict_correct"] + val["partial_correct"]) / val["total"] if val["total"] else 0.0
            by_subtask.setdefault(subtask, {})[itype] = {
                "strict_correct": val["strict_correct"],
                "partial_correct": val["partial_correct"],
                "total": val["total"],
                "strict_accuracy": strict_acc,
                "partial_accuracy": partial_acc,
                "combined_accuracy": combined_acc,
            }

        # Add deltas for each subtask.
        for subtask, row in by_subtask.items():
            s = row.get("single", {}).get("combined_accuracy", 0.0)
            c = row.get("multiturn_clean", {}).get("combined_accuracy", 0.0)
            n = row.get("multiturn_noisy", {}).get("combined_accuracy", 0.0)
            row["delta_combined_clean_minus_single"] = c - s
            row["delta_combined_noisy_minus_clean"] = n - c
            row["delta_combined_noisy_minus_single"] = n - s

        summary["by_model"][model] = by_subtask

        by_type = {}
        for atype, val in type_stats[model].items():
            strict_acc = val["strict_correct"] / val["total"] if val["total"] else 0.0
            partial_acc = val["partial_correct"] / val["total"] if val["total"] else 0.0
            combined_acc = (val["strict_correct"] + val["partial_correct"]) / val["total"] if val["total"] else 0.0
            by_type[atype] = {
                "strict_correct": val["strict_correct"],
                "partial_correct": val["partial_correct"],
                "total": val["total"],
                "strict_accuracy": strict_acc,
                "partial_accuracy": partial_acc,
                "combined_accuracy": combined_acc,
            }
        summary["by_model_answer_type"][model] = by_type

    return summary


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models:
        models = list(EVAL_MODELS)

    available_subtasks = discover_subtasks(args.input_dir)
    if args.subtasks.strip():
        wanted = {s.strip() for s in args.subtasks.split(",") if s.strip()}
        selected_subtasks = [s for s in available_subtasks if s in wanted]
    else:
        selected_subtasks = available_subtasks

    selected_subtasks = selected_subtasks[: args.max_subtasks]

    sampled: Dict[str, List[Tuple[str, Dict[str, Dict[str, Any]]]]] = {}
    sampling_stats = {}
    mitigation_stats = {}

    for subtask in selected_subtasks:
        buckets = load_triplets_for_subtask(args.input_dir, subtask)
        pairs = pick_matched_samples(buckets, args.samples_per_subtask, rng)
        pairs, mstats = apply_risk_mode_to_pairs(pairs, args.risk_mode)
        if not pairs:
            continue
        sampled[subtask] = pairs
        sampling_stats[subtask] = {
            "matched_triplets": len(set(buckets["single"]) & set(buckets["multiturn_clean"]) & set(buckets["multiturn_noisy"])),
            "sampled": len(pairs),
        }
        mitigation_stats[subtask] = mstats

    if not sampled:
        raise RuntimeError("No matched triplets found for selected subtasks.")

    result = evaluate_samples(models=models, sampled=sampled, temperature=args.temperature)
    result["meta"] = {
        "timestamp": datetime.now().isoformat(),
        "input_dir": str(args.input_dir),
        "models": models,
        "samples_per_subtask": args.samples_per_subtask,
        "max_subtasks": args.max_subtasks,
        "seed": args.seed,
        "temperature": args.temperature,
        "risk_mode": args.risk_mode,
        "sampling": sampling_stats,
        "mitigation": mitigation_stats,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Console summary.
    print("=" * 72)
    print("Small-Batch Interaction Comparison")
    print("=" * 72)
    print(f"Output: {args.output}")
    print(f"Models: {', '.join(models)}")
    print(f"Subtasks: {', '.join(sorted(sampled.keys()))}")
    print(f"Risk mode: {args.risk_mode}")

    for model in models:
        print("\n" + "-" * 72)
        print(f"Model: {model}")
        rows = result["by_model"].get(model, {})
        for subtask in sorted(rows.keys()):
            r = rows[subtask]
            s = r.get("single", {}).get("combined_accuracy", 0.0)
            c = r.get("multiturn_clean", {}).get("combined_accuracy", 0.0)
            n = r.get("multiturn_noisy", {}).get("combined_accuracy", 0.0)
            print(
                f"{subtask:<20} single={s:.2%} clean={c:.2%} noisy={n:.2%} "
                f"(clean-single={r['delta_combined_clean_minus_single']:+.2%}, "
                f"noisy-clean={r['delta_combined_noisy_minus_clean']:+.2%})"
            )

        type_rows = result["by_model_answer_type"].get(model, {})
        if type_rows:
            print("  Answer-Type Summary (combined accuracy):")
            for at in sorted(type_rows.keys()):
                x = type_rows[at]
                print(
                    f"    {at:<10} combined={x['combined_accuracy']:.2%} "
                    f"(strict={x['strict_accuracy']:.2%}, partial={x['partial_accuracy']:.2%}, n={x['total']})"
                )


if __name__ == "__main__":
    main()
