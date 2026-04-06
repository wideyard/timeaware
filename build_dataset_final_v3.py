#!/usr/bin/env python3
"""Build dataset_final_v3 with full conversion, interaction split, and strict rule checks."""

import argparse
import copy
import hashlib
import importlib
import json
import random
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CASUAL_PATTERNS = [
    r"\bhow are you\b",
    r"\bweather\b",
    r"\blunch\b",
    r"\bdinner\b",
    r"\bbreakfast\b",
    r"\bweekend\b",
    r"\btraffic\b",
    r"\bmovie\b",
    r"\bmusic\b",
    r"\bcoffee\b",
    r"\btea\b",
    r"\bthanks\b",
    r"\bthank you\b",
    r"\bokay\b",
    r"\bgot it\b",
    r"\bno problem\b",
    r"\bby the way\b",
]

ENGLISH_RE = re.compile(r"[A-Za-z]")
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
ALNUM_TOKEN_RE = re.compile(r"[a-z0-9]+")

NOISE_TEMPLATE_PAIRS = [
    (
        "By the way, what are you doing this weekend?",
        "Nothing special, I might just rest at home.",
    ),
    (
        "Have you tried the new cafe near the station?",
        "Not yet, but I heard their coffee is good.",
    ),
    (
        "The weather was unexpectedly cold this morning.",
        "Yes, I had to bring a jacket when I went out.",
    ),
    (
        "I am thinking about what to cook for dinner.",
        "Pasta is easy and usually turns out well.",
    ),
    (
        "Did you watch any good movies recently?",
        "I watched a comedy last night and it was fun.",
    ),
    (
        "I need to clean my room later today.",
        "Same here, I have been postponing it all week.",
    ),
    (
        "My phone battery drains too fast these days.",
        "You might want to check background apps.",
    ),
    (
        "I forgot to buy groceries again.",
        "That happens to me all the time.",
    ),
]

DEFAULT_ACK = "Understood. Please continue."

ACK_TEMPLATES = [
    "Got it. Please continue.",
    "Understood. Please continue.",
    "Thanks, I am following. Go on.",
    "Okay, that makes sense. Please continue.",
    "Noted. I am with you so far.",
    "I understand. Please keep going.",
    "All right, I have that. Continue when ready.",
    "Thanks, I have recorded that step.",
    "Makes sense. What comes next?",
    "I am tracking this. Please continue.",
]

PARALLEL_RESPONSE_TEMPLATES = [
    "Yes, those steps can be done in parallel. Please continue.",
    "Yes, they can run in parallel. Go ahead.",
    "That works in parallel. Please continue.",
    "Yes, those two actions can happen at the same time.",
    "They can be completed in parallel. What is next?",
    "Yes, parallel execution is possible here. Continue.",
]

ELLIPSIS_RESPONSE_TEMPLATES = [
    "I can complete that thought: {base}. Please continue.",
    "To make it explicit: {base}. What comes next?",
    "Let me restate clearly: {base}. Please continue.",
]

ALLOWED_SHORT_ANSWERS = {
    "yes",
    "no",
    "true",
    "false",
    "unknown",
    "cannot be determined",
    "not enough information",
}


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build dataset_final_v3")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("dataset_final_v3_config.json"),
        help="Path to config JSON",
    )
    return parser.parse_args()


def normalize_text(s: Any) -> str:
    if s is None:
        return ""
    return str(s).strip()


def contains_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text or ""))


def looks_english(text: str) -> bool:
    if not text:
        return False
    # English-mode check: reject CJK, allow ASCII/number/symbol text.
    return not contains_cjk(text)


def canonicalize_space(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def extract_tokens(text: str) -> List[str]:
    return ALNUM_TOKEN_RE.findall(canonicalize_space(text))


def normalize_turns(raw_conv: Any) -> List[Dict[str, str]]:
    turns: List[Dict[str, str]] = []
    if not isinstance(raw_conv, list):
        return turns
    for turn in raw_conv:
        if not isinstance(turn, dict):
            continue
        role = normalize_text(turn.get("role", "")).lower()
        content = normalize_text(turn.get("content", ""))
        if not content:
            continue
        if role not in {"user", "assistant"}:
            role = "user" if not turns or turns[-1]["role"] == "assistant" else "assistant"
        turns.append({"role": role, "content": content})
    return turns


def is_casual_noise_turn(content: str) -> bool:
    c = canonicalize_space(content)
    return any(re.search(p, c) for p in CASUAL_PATTERNS)


def detect_existing_noise(conversation: List[Dict[str, str]], query: str) -> bool:
    query_n = canonicalize_space(query)
    for turn in conversation:
        content_n = canonicalize_space(turn["content"])
        if content_n == query_n:
            continue
        if is_casual_noise_turn(content_n):
            return True
    return False


def trim_noise_for_clean(conversation: List[Dict[str, str]], query: str) -> List[Dict[str, str]]:
    query_n = canonicalize_space(query)
    trimmed: List[Dict[str, str]] = []
    for turn in conversation:
        content_n = canonicalize_space(turn["content"])
        if content_n != query_n and is_casual_noise_turn(content_n):
            continue
        trimmed.append(turn)
    return trimmed


def find_best_question(item: Dict[str, Any], conversation: List[Dict[str, str]]) -> str:
    query = normalize_text(item.get("query", ""))
    if query:
        return query
    user_turns = [t["content"] for t in conversation if t["role"] == "user"]
    if user_turns:
        return user_turns[-1]
    return ""


def make_single_turn(context: str, question: str) -> List[Dict[str, str]]:
    merged = ""
    if context:
        merged += f"Context: {context}\n\n"
    merged += f"Question: {question}"
    return [{"role": "user", "content": merged.strip()}]


def ensure_multiturn_min_structure(
    base_conversation: List[Dict[str, str]],
    context: str,
    question: str,
) -> List[Dict[str, str]]:
    if len(base_conversation) >= 3:
        return base_conversation
    return [
        {"role": "user", "content": f"Context: {context}".strip()},
        {"role": "assistant", "content": "I have read the context. What is your question?"},
        {"role": "user", "content": question},
    ]


def pick_template(options: List[str], rng: random.Random) -> str:
    if not options:
        return DEFAULT_ACK
    return rng.choice(options)


def naturalize_assistant_text(content: str, rng: random.Random) -> str:
    text = normalize_text(content)
    if not text:
        return pick_template(ACK_TEMPLATES, rng)

    lower = canonicalize_space(text)
    if lower == "if they can be done in parallel...":
        return pick_template(PARALLEL_RESPONSE_TEMPLATES, rng)

    if text.endswith("..."):
        base = text[:-3].strip()
        if not base:
            return pick_template(ACK_TEMPLATES, rng)
        tmpl = pick_template(ELLIPSIS_RESPONSE_TEMPLATES, rng)
        return tmpl.format(base=base)

    if len(text) < 5:
        return pick_template(ACK_TEMPLATES, rng)

    return text


def enforce_alternating_dialogue(
    conversation: List[Dict[str, str]], question: str, rng: random.Random
) -> List[Dict[str, str]]:
    if not conversation:
        return conversation

    out: List[Dict[str, str]] = []
    for turn in conversation:
        role = turn.get("role", "user")
        content = normalize_text(turn.get("content", ""))
        if not content:
            continue

        if role == "assistant":
            content = naturalize_assistant_text(content, rng)

        current = {"role": role, "content": content}

        if not out:
            if current["role"] != "user":
                out.append({"role": "user", "content": f"Question: {question}" if question else "Question:"})
            out.append(current)
            continue

        prev_role = out[-1]["role"]
        if current["role"] == prev_role:
            if current["role"] == "user":
                out.append({"role": "assistant", "content": pick_template(ACK_TEMPLATES, rng)})
                out.append(current)
            else:
                out[-1]["content"] = naturalize_assistant_text(
                    f"{out[-1]['content']} {current['content']}",
                    rng,
                )
        else:
            out.append(current)

    if question:
        q_norm = canonicalize_space(question)
        if not out or canonicalize_space(out[-1]["content"]) != q_norm:
            if out and out[-1]["role"] == "user":
                out.append({"role": "assistant", "content": pick_template(ACK_TEMPLATES, rng)})
            out.append({"role": "user", "content": question})

    return out


def insert_noise_turns(
    clean_conv: List[Dict[str, str]],
    min_noise_turns: int,
    max_noise_turns: int,
    position: str,
    rng: random.Random,
) -> Tuple[List[Dict[str, str]], int]:
    if not clean_conv:
        return clean_conv, 0

    pair_count = rng.randint(min_noise_turns, max_noise_turns)
    noise_turns: List[Dict[str, str]] = []
    for _ in range(pair_count):
        u, a = rng.choice(NOISE_TEMPLATE_PAIRS)
        noise_turns.append({"role": "user", "content": u})
        noise_turns.append({"role": "assistant", "content": a})

    # Keep the final user question at the end whenever possible.
    if len(clean_conv) >= 1 and clean_conv[-1]["role"] == "user":
        prefix = clean_conv[:-1]
        final_question_turn = [clean_conv[-1]]
    else:
        prefix = clean_conv
        final_question_turn = []

    if position == "front":
        merged = noise_turns + prefix + final_question_turn
    elif position == "tail":
        merged = prefix + noise_turns + final_question_turn
    else:
        if not prefix:
            merged = noise_turns + final_question_turn
        else:
            cut = rng.randint(0, len(prefix))
            merged = prefix[:cut] + noise_turns + prefix[cut:] + final_question_turn

    return merged, len(noise_turns)


def dedup_key(question: str, answer: str) -> str:
    q = canonicalize_space(question)
    a = canonicalize_space(answer)
    return hashlib.md5(f"{q}|{a}".encode("utf-8")).hexdigest()


def sample_id(source_id: str, task: str, sub_task: str, itype: str, idx: int) -> str:
    raw = f"{source_id}|{task}|{sub_task}|{itype}|{idx}"
    h = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
    return f"ta_{task.lower()}_{sub_task.split('-')[-1].lower()}_{itype}_{h}"


def is_answer_extractable(answer: str, conversation: List[Dict[str, str]]) -> bool:
    answer_n = canonicalize_space(answer)
    if not answer_n:
        return False
    if answer_n in ALLOWED_SHORT_ANSWERS:
        return True

    joined = "\n".join(t["content"] for t in conversation)
    joined_n = canonicalize_space(joined)
    if answer_n in joined_n:
        return True

    ans_tokens = [t for t in extract_tokens(answer_n) if len(t) >= 4]
    if not ans_tokens:
        return len(answer_n) >= 2

    match_count = sum(1 for t in set(ans_tokens) if t in joined_n)
    return match_count >= 1


def check_ground_truth_consistency(answer: str, ground_truth: Any) -> bool:
    if not isinstance(ground_truth, dict) or not ground_truth:
        return False

    for key in ["correct_answer", "answer", "gold_answer", "next_step", "current_state"]:
        value = ground_truth.get(key)
        if isinstance(value, str) and value.strip():
            if key == "correct_answer":
                if canonicalize_space(value) != canonicalize_space(answer):
                    return False
    return True


def all_text_fields_english(sample: Dict[str, Any]) -> bool:
    payload = []
    payload.append(normalize_text(sample.get("answer", "")))

    gt = sample.get("ground_truth", {})
    if isinstance(gt, dict):
        for v in gt.values():
            if isinstance(v, str):
                payload.append(v)

    metadata = sample.get("metadata", {})
    if isinstance(metadata, dict):
        for v in metadata.values():
            if isinstance(v, str):
                if contains_cjk(v):
                    return False

    for turn in sample.get("conversation", []):
        payload.append(normalize_text(turn.get("content", "")))

    for text in payload:
        if text and not looks_english(text):
            return False
    return True


def infer_mapping_by_pattern(sub_task: str) -> Optional[Tuple[str, str]]:
    st = canonicalize_space(sub_task).replace("_", "-")

    if st.startswith("t1-"):
        if "timeboundary" in st:
            return ("T1", "TimeBoundary")
        if "duration" in st or "typicaltime" in st:
            return ("T1", "Duration")
        if "ordering" in st or "sequence" in st or "causal" in st:
            return ("T1", "Ordering")
        if any(
            k in st
            for k in [
                "calc",
                "addition",
                "multichoice",
                "multihop",
                "distractor",
                "parallel",
                "histnoise",
                "confusionnoise",
                "numnoise",
                "timenoise",
            ]
        ):
            return ("T1", "Counting")

    if st.startswith("t2-"):
        if "positiontrack" in st:
            return ("T2", "Location")
        if "convo-timeline" in st:
            return ("T2", "Location")
        if any(k in st for k in ["statetrack", "socialstate", "progressive", "tense", "stationarity"]):
            return ("T2", "Status")
        if "state" in st and "timeline" in st:
            return ("T2", "Status")
        if "convo-state" in st:
            return ("T2", "Status")
        if any(
            k in st
            for k in [
                "consequence",
                "evidence",
                "statetransition",
                "location",
                "ordering",
                "sequence",
                "counterfactualstate",
                "branch",
                "rollback",
                "commonsense",
                "physicalstate",
                "causalstate",
            ]
        ):
            return ("T2", "Consequence")

    if st.startswith("t3-"):
        if "resource" in st or "concurrent" in st:
            return ("T3", "ResourceConflict")
        if any(k in st for k in ["conflict", "timeoverlap", "timeconflict", "location", "duration"]):
            return ("T3", "SpaceConflict")

    if st.startswith("t4-"):
        if "cross" in st or "multi-hop" in st or "multihop" in st:
            return ("T4", "MultiHop")
        return ("T4", "NoiseRetrieval")

    if st.startswith("t5-"):
        return ("T5", "RuleReversal")

    return None


def validate_sample(sample: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    if not sample.get("answer"):
        errors.append("empty_answer")

    conversation = sample.get("conversation", [])
    if not isinstance(conversation, list) or not conversation:
        errors.append("empty_conversation")

    if sample.get("interaction_type") == "single":
        if len(conversation) != 1:
            errors.append("single_not_one_turn")
        elif conversation[0].get("role") != "user":
            errors.append("single_turn_role_invalid")

    if sample.get("interaction_type") in {"multiturn_clean", "multiturn_noisy"}:
        if len(conversation) < 3:
            errors.append("multiturn_too_short")
        else:
            for i in range(1, len(conversation)):
                if conversation[i].get("role") == conversation[i - 1].get("role"):
                    errors.append("non_alternating_roles")
                    break

    if not check_ground_truth_consistency(sample.get("answer", ""), sample.get("ground_truth")):
        errors.append("ground_truth_inconsistent")

    if not is_answer_extractable(sample.get("answer", ""), conversation):
        errors.append("answer_not_extractable")

    if not all_text_fields_english(sample):
        errors.append("non_english_content")

    return len(errors) == 0, errors


def choose_primary_mapping(
    sub_task: str,
    mapping_index: Dict[str, Tuple[str, str]],
) -> Optional[Tuple[str, str]]:
    direct = mapping_index.get(sub_task)
    if direct:
        return direct
    return infer_mapping_by_pattern(sub_task)


def build_mapping_index(mapping_file: Path) -> Dict[str, Tuple[str, str]]:
    content = load_json(mapping_file)
    dmap = content.get("dimension_mapping", {})
    index: Dict[str, Tuple[str, str]] = {}
    for task, subdims in dmap.items():
        for subdim, sub_tasks in subdims.items():
            for st in sub_tasks:
                if st not in index:
                    index[st] = (task, subdim)

    try:
        md3 = importlib.import_module("merge_dimensions_v3")
        extra = getattr(md3, "SUBTASK_TO_NEW_DIM", {})
        if isinstance(extra, dict):
            for k, v in extra.items():
                if k not in index and isinstance(v, tuple) and len(v) == 2:
                    index[k] = (v[0], v[1])
    except Exception:
        pass

    return index


def source_allowed(file_stem: str, keywords: List[str]) -> bool:
    s = file_stem.lower()
    return any(k in s for k in keywords)


def iter_jsonl(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def write_jsonl(path: Path, items: List[Dict[str, Any]], ensure_ascii: bool):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=ensure_ascii) + "\n")


def main() -> None:
    args = parse_args()
    config = load_json(args.config)

    input_dir = Path(config["input_dir"])
    output_dir = Path(config["output_dir"])
    mapping_file = Path(config["mapping_file"])
    keywords = [k.lower() for k in config.get("allowed_dataset_keywords", [])]

    noise_cfg = config["noise"]
    min_noise_turns = int(noise_cfg["min_noise_turns"])
    max_noise_turns = int(noise_cfg["max_noise_turns"])
    noise_position = str(noise_cfg["noise_position"])
    noisy_ratio = float(noise_cfg["noisy_ratio_per_subtask"])
    rng = random.Random(int(noise_cfg.get("random_seed", 42)))

    ensure_ascii = bool(config.get("output", {}).get("ensure_ascii", False))

    mapping_index = build_mapping_index(mapping_file)

    if output_dir.exists():
        shutil.rmtree(output_dir)

    grouped: Dict[Tuple[str, str], Dict[str, List[Dict[str, Any]]]] = defaultdict(
        lambda: {
            "single": [],
            "multiturn_clean": [],
            "multiturn_noisy": [],
            "_source_noisy": [],
            "_inject_candidates": [],
        }
    )

    seen_q_a: set = set()
    stats = {
        "total_files": 0,
        "eligible_files": 0,
        "total_samples_read": 0,
        "mapped_samples": 0,
        "dedup_dropped": 0,
        "unmapped_sub_task": defaultdict(int),
        "language_dropped": 0,
        "invalid_dropped": 0,
        "kept": defaultdict(lambda: defaultdict(int)),
    }

    jsonl_files = sorted(input_dir.glob("*.jsonl"))
    stats["total_files"] = len(jsonl_files)

    for file_path in jsonl_files:
        stem = file_path.stem.lower()
        if not source_allowed(stem, keywords):
            continue

        stats["eligible_files"] += 1

        for idx, item in enumerate(iter_jsonl(file_path)):
            stats["total_samples_read"] += 1

            sub_task_src = normalize_text(item.get("sub_task", ""))
            mapped = choose_primary_mapping(sub_task_src, mapping_index)
            if not mapped:
                stats["unmapped_sub_task"][sub_task_src] += 1
                continue

            task, subdim = mapped
            sub_task = f"{task}-{subdim}"

            conversation_raw = normalize_turns(item.get("conversation", []))
            context = normalize_text(item.get("context", ""))
            question = find_best_question(item, conversation_raw)
            answer = normalize_text(item.get("answer", ""))
            ground_truth = item.get("ground_truth", {})
            source_id = normalize_text(item.get("source_id", "")) or f"{file_path.stem}_{idx}"

            if not question or not answer:
                stats["invalid_dropped"] += 1
                continue

            key = dedup_key(question, answer)
            if key in seen_q_a:
                stats["dedup_dropped"] += 1
                continue
            seen_q_a.add(key)
            stats["mapped_samples"] += 1

            # Build clean multiturn.
            convo_for_clean = trim_noise_for_clean(conversation_raw, question)
            if not convo_for_clean:
                convo_for_clean = conversation_raw

            # Ensure the final user turn is the question.
            if not convo_for_clean or canonicalize_space(convo_for_clean[-1]["content"]) != canonicalize_space(question):
                convo_for_clean.append({"role": "user", "content": question})

            convo_for_clean = ensure_multiturn_min_structure(convo_for_clean, context, question)
            convo_for_clean = enforce_alternating_dialogue(convo_for_clean, question, rng)

            single_sample = {
                "id": sample_id(source_id, task, sub_task, "single", idx),
                "task": task,
                "sub_task": sub_task,
                "interaction_type": "single",
                "conversation": make_single_turn(context, question),
                "answer": answer,
                "ground_truth": ground_truth if isinstance(ground_truth, dict) else {},
                "source_id": source_id,
                "source_sub_task": sub_task_src,
                "source_dataset": file_path.stem,
                "metadata": {
                    "language": "en",
                    "has_injected_noise": False,
                    "noise_turns": 0,
                    "noise_source": "none",
                },
            }

            clean_sample = {
                "id": sample_id(source_id, task, sub_task, "multiturn_clean", idx),
                "task": task,
                "sub_task": sub_task,
                "interaction_type": "multiturn_clean",
                "conversation": convo_for_clean,
                "answer": answer,
                "ground_truth": ground_truth if isinstance(ground_truth, dict) else {},
                "source_id": source_id,
                "source_sub_task": sub_task_src,
                "source_dataset": file_path.stem,
                "metadata": {
                    "language": "en",
                    "has_injected_noise": False,
                    "noise_turns": 0,
                    "noise_source": "none",
                },
            }

            existing_noisy = detect_existing_noise(conversation_raw, question)
            noisy_sample = None
            if existing_noisy:
                noisy_sample = {
                    "id": sample_id(source_id, task, sub_task, "multiturn_noisy", idx),
                    "task": task,
                    "sub_task": sub_task,
                    "interaction_type": "multiturn_noisy",
                    "conversation": enforce_alternating_dialogue(
                        ensure_multiturn_min_structure(conversation_raw, context, question),
                        question,
                        rng,
                    ),
                    "answer": answer,
                    "ground_truth": ground_truth if isinstance(ground_truth, dict) else {},
                    "source_id": source_id,
                    "source_sub_task": sub_task_src,
                    "source_dataset": file_path.stem,
                    "metadata": {
                        "language": "en",
                        "has_injected_noise": False,
                        "noise_turns": 0,
                        "noise_source": "from_source",
                    },
                }

            # Validate and retain English-only samples.
            valid_single, _ = validate_sample(single_sample)
            valid_clean, _ = validate_sample(clean_sample)

            if not valid_single or not valid_clean:
                if not all_text_fields_english(single_sample) or not all_text_fields_english(clean_sample):
                    stats["language_dropped"] += 1
                else:
                    stats["invalid_dropped"] += 1
                continue

            grouped[(task, subdim)]["single"].append(single_sample)
            grouped[(task, subdim)]["multiturn_clean"].append(clean_sample)

            if noisy_sample is not None:
                valid_noisy, _ = validate_sample(noisy_sample)
                if valid_noisy:
                    grouped[(task, subdim)]["_source_noisy"].append(noisy_sample)
                else:
                    if not all_text_fields_english(noisy_sample):
                        stats["language_dropped"] += 1
                    else:
                        stats["invalid_dropped"] += 1
            else:
                grouped[(task, subdim)]["_inject_candidates"].append(clean_sample)

    # Build noisy split with configurable ratio.
    for (task, subdim), bucket in grouped.items():
        clean_items = bucket["multiturn_clean"]
        source_noisy_items = bucket["_source_noisy"]
        inject_candidates = bucket["_inject_candidates"]

        target_noisy = int(round(len(clean_items) * noisy_ratio))
        final_noisy: List[Dict[str, Any]] = []
        final_noisy.extend(source_noisy_items)

        need_injected = max(0, target_noisy - len(source_noisy_items))
        rng.shuffle(inject_candidates)
        for clean_sample in inject_candidates[:need_injected]:
            noisy_conv, noise_turn_count = insert_noise_turns(
                clean_sample["conversation"],
                min_noise_turns=min_noise_turns,
                max_noise_turns=max_noise_turns,
                position=noise_position,
                rng=rng,
            )
            noisy_sample = copy.deepcopy(clean_sample)
            noisy_sample["id"] = noisy_sample["id"].replace("multiturn_clean", "multiturn_noisy")
            noisy_sample["interaction_type"] = "multiturn_noisy"
            noisy_sample["conversation"] = enforce_alternating_dialogue(noisy_conv, question, rng)
            noisy_sample["metadata"]["has_injected_noise"] = True
            noisy_sample["metadata"]["noise_turns"] = noise_turn_count
            noisy_sample["metadata"]["noise_source"] = "template_injected"

            valid_noisy, _ = validate_sample(noisy_sample)
            if valid_noisy:
                final_noisy.append(noisy_sample)
            else:
                stats["invalid_dropped"] += 1

        bucket["multiturn_noisy"] = final_noisy

        stats["kept"][f"{task}-{subdim}"]["single"] = len(bucket["single"])
        stats["kept"][f"{task}-{subdim}"]["multiturn_clean"] = len(bucket["multiturn_clean"])
        stats["kept"][f"{task}-{subdim}"]["multiturn_noisy"] = len(bucket["multiturn_noisy"])

    # Write outputs by (subdim x interaction type).
    for (task, subdim), bucket in grouped.items():
        task_dir = output_dir / task
        prefix = f"{task}-{subdim}"
        write_jsonl(task_dir / f"{prefix}-single.jsonl", bucket["single"], ensure_ascii=ensure_ascii)
        write_jsonl(
            task_dir / f"{prefix}-multiturn_clean.jsonl",
            bucket["multiturn_clean"],
            ensure_ascii=ensure_ascii,
        )
        write_jsonl(
            task_dir / f"{prefix}-multiturn_noisy.jsonl",
            bucket["multiturn_noisy"],
            ensure_ascii=ensure_ascii,
        )

    # Save report.
    report = {
        "config": config,
        "summary": {
            "total_files": stats["total_files"],
            "eligible_files": stats["eligible_files"],
            "total_samples_read": stats["total_samples_read"],
            "mapped_samples": stats["mapped_samples"],
            "dedup_dropped_question_answer": stats["dedup_dropped"],
            "language_dropped": stats["language_dropped"],
            "invalid_dropped": stats["invalid_dropped"],
        },
        "kept_by_subtask_and_type": stats["kept"],
        "top_unmapped_sub_task": dict(
            sorted(stats["unmapped_sub_task"].items(), key=lambda x: -x[1])[:100]
        ),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "build_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if config.get("output", {}).get("write_pretty_report", True):
        lines = []
        lines.append("# dataset_final_v3 Build Report")
        lines.append("")
        lines.append("## Summary")
        for k, v in report["summary"].items():
            lines.append(f"- {k}: {v}")
        lines.append("")
        lines.append("## Kept By Subtask And Type")
        for subtask in sorted(report["kept_by_subtask_and_type"]):
            row = report["kept_by_subtask_and_type"][subtask]
            lines.append(
                f"- {subtask}: single={row.get('single', 0)}, "
                f"multiturn_clean={row.get('multiturn_clean', 0)}, "
                f"multiturn_noisy={row.get('multiturn_noisy', 0)}"
            )
        lines.append("")
        lines.append("## Top Unmapped sub_task")
        for k, v in report["top_unmapped_sub_task"].items():
            lines.append(f"- {k}: {v}")

        with open(output_dir / "BUILD_REPORT.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    print("Build completed.")
    print(f"Output directory: {output_dir}")
    print(f"Report: {output_dir / 'build_report.json'}")


if __name__ == "__main__":
    main()
