#!/usr/bin/env python3
"""
MCTACO Dataset Conversion Script for Time-Aware Benchmark

Converts MCTACO dataset to conversational format following the analysis in MCTACO.md.

Task Mapping:
- T1 (Time Calculation): Uses Duration + Typical Time categories
- T2 (State Update): Uses Stationarity + Event Ordering categories
- T3 (Conflict Detection): Uses Duration + Typical Time for overlapping events
- T4 (Long-term Memory): Uses all categories with buried time anchors
- T5 (Counterfactual): Uses Duration/Stationarity with reversed rules
"""

import json
import os
import random
import hashlib
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Temporal categories in MCTACO
CATEGORIES = {
    "Event Duration": "duration",
    "Event Ordering": "ordering",
    "Frequency": "frequency",
    "Stationarity": "stationarity",
    "Typical Time": "typical_time"
}

# Duration patterns for time calculation
DURATION_PATTERNS = {
    "Event Duration": {
        "patterns": ["How long", "How much time", "duration", "lasted"],
        "type": "duration"
    }
}

# Stationarity patterns for state tracking
STATIONARITY_PATTERNS = {
    "still": "continuing",
    "still the": "continuing",
    "ever": "persistence",
    "Will": "future_persistence"
}

def load_mctaco_data(filepath: str) -> List[Dict]:
    """Load MCTACO TSV data."""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 5:
                sentence, question, answer, label, category = parts[:5]
                data.append({
                    "sentence": sentence,
                    "question": question,
                    "answer": answer,
                    "label": label,
                    "category": category
                })
    return data

def group_by_sentence(data: List[Dict]) -> Dict[str, List[Dict]]:
    """Group Q&A pairs by sentence."""
    grouped = defaultdict(list)
    for item in data:
        grouped[item["sentence"]].append(item)
    return grouped

def generate_id(sentence: str, question: str, task: str, sub_task: str) -> str:
    """Generate unique ID for each converted item."""
    hash_input = f"{sentence}_{question}_{task}_{sub_task}"
    hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:12]
    return f"mctaco_{task.lower()}_{hash_val}"

# ============== T1: Time Calculation ==============
def convert_t1_duration(item: Dict, sentence: str) -> Optional[Dict]:
    """Convert Duration questions to T1 time calculation task."""
    if item["category"] != "Event Duration":
        return None
    
    # Only use yes-labeled answers
    if item["label"] != "yes":
        return None
    
    answer = item["answer"]
    question = item["question"]
    
    # Extract time expression from answer
    time_expr = extract_time_expression(answer)
    
    # Create conversational context
    conversation = [
        {"role": "user", "content": sentence},
        {"role": "assistant", "content": "I understand, please continue."},
        {"role": "user", "content": f"{question} (请根据常识推理)"}
    ]
    
    return {
        "task": "T1",
        "sub_task": "T1-Duration",
        "context": sentence,
        "conversation": conversation,
        "query": question,
        "answer": answer,
        "state_info": {
            "type": "duration_calculation",
            "duration": time_expr,
            "category": "Event Duration"
        },
        "ground_truth": {
            "answer": answer,
            "label": item["label"],
            "category": item["category"]
        },
        "difficulty": "medium",
        "source_id": generate_id(sentence, question, "T1", "Duration")
    }

def convert_t1_time_calc(item: Dict, sentence: str) -> Optional[Dict]:
    """Convert to T1 time calculation with start/end time inference."""
    if item["category"] not in ["Event Duration", "Typical Time"]:
        return None
    
    if item["label"] != "yes":
        return None
    
    question = item["question"]
    answer = item["answer"]
    
    # Generate time calculation question
    if "How long" in question or "duration" in question.lower():
        # Duration-based calculation
        conversation = [
            {"role": "user", "content": f"假设现在我们开始这个事件：{sentence}"},
            {"role": "assistant", "content": "好的，我记下了这个事件。"},
            {"role": "user", "content": f"根据常识，{question}"}
        ]
        query = question
        sub_task = "T1-TimeCalc"
    elif "What time" in question or "When" in question:
        # Typical time question
        conversation = [
            {"role": "user", "content": sentence},
            {"role": "assistant", "content": "我了解这个情境。"},
            {"role": "user", "content": f"{question}"}
        ]
        query = question
        sub_task = "T1-TypicalTime"
    else:
        return None
    
    return {
        "task": "T1",
        "sub_task": sub_task,
        "context": sentence,
        "conversation": conversation,
        "query": query,
        "answer": answer,
        "state_info": {
            "type": "time_calculation",
            "category": item["category"],
            "answer_type": "duration" if "long" in question.lower() else "time_point"
        },
        "ground_truth": {
            "answer": answer,
            "label": item["label"],
            "category": item["category"]
        },
        "difficulty": "medium",
        "source_id": generate_id(sentence, question, "T1", sub_task.replace("T1-", ""))
    }

def extract_time_expression(answer: str) -> str:
    """Extract time expression from answer."""
    # Common time expressions
    time_patterns = [
        "hours", "hour", "minutes", "minute", "seconds", "second",
        "days", "day", "weeks", "week", "months", "month", "years", "year",
        "centuries", "century", "morning", "evening", "afternoon", "night"
    ]
    for pattern in time_patterns:
        if pattern in answer.lower():
            return answer
    return answer

# ============== T2: State Update ==============
def convert_t2_stationarity(item: Dict, sentence: str) -> Optional[Dict]:
    """Convert Stationarity questions to T2 state update task."""
    if item["category"] != "Stationarity":
        return None
    
    if item["label"] != "yes":
        return None
    
    question = item["question"]
    answer = item["answer"]
    
    # Determine if state persists
    is_persistent = answer.lower() in ["yes", "still", "continues"]
    
    conversation = [
        {"role": "user", "content": sentence},
        {"role": "assistant", "content": "我了解这个背景。"},
        {"role": "user", "content": "根据上文，"},
        {"role": "user", "content": f"时间已经过去很久了。{question}"}
    ]
    
    return {
        "task": "T2",
        "sub_task": "T2-Stationarity",
        "context": sentence,
        "conversation": conversation,
        "query": f"经过时间流逝后，{question}",
        "answer": "状态持续" if is_persistent else "状态改变",
        "state_info": {
            "type": "state_persistence",
            "is_persistent": is_persistent,
            "original_question": question
        },
        "ground_truth": {
            "answer": answer,
            "label": item["label"],
            "category": item["category"]
        },
        "difficulty": "medium",
        "source_id": generate_id(sentence, question, "T2", "Stationarity")
    }

def convert_t2_ordering(item: Dict, sentence: str, all_items: List[Dict]) -> Optional[Dict]:
    """Convert Event Ordering questions to T2 state update task."""
    if item["category"] != "Event Ordering":
        return None
    
    if item["label"] != "yes":
        return None
    
    question = item["question"]
    answer = item["answer"]
    
    # Determine temporal order
    if "before" in question.lower():
        order_type = "before"
    elif "after" in question.lower() or "next" in question.lower():
        order_type = "after"
    else:
        order_type = "ordering"
    
    conversation = [
        {"role": "user", "content": f"让我描述一个事件序列：{sentence}"},
        {"role": "assistant", "content": "好的，请注意事件的时间顺序。"},
        {"role": "user", "content": f"{question}"}
    ]
    
    return {
        "task": "T2",
        "sub_task": "T2-Ordering",
        "context": sentence,
        "conversation": conversation,
        "query": question,
        "answer": answer,
        "state_info": {
            "type": "event_ordering",
            "order_type": order_type
        },
        "ground_truth": {
            "answer": answer,
            "label": item["label"],
            "category": item["category"]
        },
        "difficulty": "medium",
        "source_id": generate_id(sentence, question, "T2", "Ordering")
    }

# ============== T3: Conflict Detection ==============
def convert_t3_conflict(items: List[Dict], sentence: str) -> Optional[Dict]:
    """Create T3 conflict detection from Duration + Typical Time combinations."""
    duration_items = [i for i in items if i["category"] == "Event Duration" and i["label"] == "yes"]
    time_items = [i for i in items if i["category"] == "Typical Time" and i["label"] == "yes"]
    
    if not duration_items or not time_items:
        return None
    
    # Pick first valid pair
    duration_item = duration_items[0]
    time_item = time_items[0]
    
    duration_answer = duration_item["answer"]
    time_answer = time_item["answer"]
    
    # Create conflict scenario
    conversation = [
        {"role": "user", "content": f"场景：{sentence}"},
        {"role": "assistant", "content": "我已了解场景。"},
        {"role": "user", "content": f"根据常识，这个事件通常持续{duration_answer}。"},
        {"role": "user", "content": f"假设这个事件发生在{time_answer}。"},
        {"role": "user", "content": "我同时计划在这个时间做另一件事。这会冲突吗？"}
    ]
    
    return {
        "task": "T3",
        "sub_task": "T3-Duration-Conflict",
        "context": sentence,
        "conversation": conversation,
        "query": "这两个在时间上会有冲突吗？",
        "answer": f"可能会有冲突，因为事件持续{duration_answer}，而同时还有其他计划。",
        "state_info": {
            "type": "conflict_detection",
            "duration": duration_answer,
            "typical_time": time_answer
        },
        "ground_truth": {
            "duration_answer": duration_answer,
            "time_answer": time_answer,
            "category": "Conflict"
        },
        "difficulty": "hard",
        "source_id": generate_id(sentence, duration_item["question"], "T3", "Conflict")
    }

# ============== T4: Long-term Memory ==============
def convert_t4_buried(item: Dict, sentence: str) -> Optional[Dict]:
    """Create T4 long-term memory task with buried time anchor."""
    if item["label"] != "yes":
        return None
    
    question = item["question"]
    answer = item["answer"]
    category = item["category"]
    
    # Create conversation with buried information
    time_anchor = f"上周{random.choice(['一', '二', '三', '四', '五'])}"
    
    conversation = [
        {"role": "user", "content": f"对了，{time_anchor}发生了一件事。"},
        {"role": "user", "content": sentence},
        {"role": "user", "content": question},
        {"role": "assistant", "content": "我来分析一下..."},
        {"role": "user", "content": "顺便说一句，我明天要去看电影。"}, # Noise
        {"role": "assistant", "content": "好的，你刚才提到什么时间发生的事？"},
        {"role": "user", "content": f"回想一下，我开头说的{time_anchor}发生了什么？"}
    ]
    
    return {
        "task": "T4",
        "sub_task": "T4-Buried-Time",
        "context": sentence,
        "conversation": conversation,
        "query": f"我开头提到的{time_anchor}发生了什么？",
        "answer": sentence[:50] + "...",  # Partial recall
        "state_info": {
            "type": "buried_time",
            "time_anchor": time_anchor,
            "category": category,
            "narrative_length": len(conversation) // 2
        },
        "ground_truth": {
            "answer": answer,
            "label": item["label"],
            "category": category,
            "time_anchor": time_anchor
        },
        "difficulty": "hard",
        "source_id": generate_id(sentence, question, "T4", "Buried")
    }

def convert_t4_noisy(item: Dict, sentence: str) -> Optional[Dict]:
    """Create T4 with noisy retrieval task."""
    if item["label"] != "yes":
        return None
    
    question = item["question"]
    answer = item["answer"]
    category = item["category"]
    
    # Add noise sentences
    noise_sentences = [
        "今天天气不错。",
        "我最近在学习做饭。",
        "周末我打算去爬山。"
    ]
    
    conversation = [
        {"role": "user", "content": sentence},
        {"role": "user", "content": random.choice(noise_sentences)},
        {"role": "assistant", "content": "请继续。"},
        {"role": "user", "content": random.choice(noise_sentences)},
        {"role": "user", "content": question}
    ]
    
    return {
        "task": "T4",
        "sub_task": "T4-Noisy-Retrieval",
        "context": sentence,
        "conversation": conversation,
        "query": question,
        "answer": answer,
        "state_info": {
            "type": "noisy_retrieval",
            "category": category,
            "noise_count": len([s for s in conversation if "天气" in s.get("content", "") or "做饭" in s.get("content", "") or "爬山" in s.get("content", "")])
        },
        "ground_truth": {
            "answer": answer,
            "label": item["label"],
            "category": category
        },
        "difficulty": "hard",
        "source_id": generate_id(sentence, question, "T4", "Noisy")
    }

# ============== T5: Counterfactual ==============
def convert_t5_counterfactual_duration(item: Dict, sentence: str) -> Optional[Dict]:
    """Create T5 counterfactual task from Duration."""
    if item["category"] != "Event Duration":
        return None
    
    if item["label"] != "yes":
        return None
    
    question = item["question"]
    original_duration = item["answer"]
    
    # Add noise sentences
    noise_sentences = [
        "今天天气不错。",
        "我最近在学习做饭。",
        "周末我打算去爬山。"
    ]
    
    conversation = [
        {"role": "user", "content": f"假设一个不同的世界：{sentence}"},
        {"role": "user", "content": f"但在这个世界里，常识被颠覆了。"},
        {"role": "user", "content": f"通常{question}是{original_duration}，但在这个世界里，是相反的。"},
        {"role": "assistant", "content": "我明白了，这是一个反事实世界。"},
        {"role": "user", "content": f"{question}（在这个反事实世界中）"}
    ]
    
    # Generate counterfactual answer
    counterfactual_answer = generate_counterfactual_duration(original_duration)
    
    return {
        "task": "T5",
        "sub_task": "T5-Duration-Reverse",
        "context": sentence,
        "conversation": conversation,
        "query": f"在这个反事实世界中，{question}",
        "answer": counterfactual_answer,
        "state_info": {
            "type": "counterfactual_duration",
            "original_duration": original_duration,
            "category": item["category"]
        },
        "ground_truth": {
            "answer": counterfactual_answer,
            "original_answer": original_duration,
            "label": item["label"],
            "category": item["category"],
            "is_counterfactual": True
        },
        "difficulty": "very_hard",
        "source_id": generate_id(sentence, question, "T5", "Counterfactual")
    }

def convert_t5_counterfactual_stationarity(item: Dict, sentence: str) -> Optional[Dict]:
    """Create T5 counterfactual task from Stationarity."""
    if item["category"] != "Stationarity":
        return None
    
    if item["label"] != "yes":
        return None
    
    question = item["question"]
    original_answer = item["answer"]
    
    conversation = [
        {"role": "user", "content": f"场景：{sentence}"},
        {"role": "assistant", "content": "我了解这个场景。"},
        {"role": "user", "content": "但在一个假设的世界中，状态持续性与现实相反。"},
        {"role": "user", "content": "在现实中，如果某事曾经如此，通常会继续如此。"},
        {"role": "user", "content": "但在反事实世界里，状态会频繁改变。"},
        {"role": "assistant", "content": "明白了，状态改变规则被反转。"},
        {"role": "user", "content": f"{question}（在反事实世界中）"}
    ]
    
    # Inverse the answer
    counterfactual_answer = "不确定，状态可能已改变" if "yes" in original_answer.lower() else "很可能是，状态会持续"
    
    return {
        "task": "T5",
        "sub_task": "T5-Stationarity-Reverse",
        "context": sentence,
        "conversation": conversation,
        "query": f"在反事实世界中，{question}",
        "answer": counterfactual_answer,
        "state_info": {
            "type": "counterfactual_stationarity",
            "original_answer": original_answer,
            "category": item["category"]
        },
        "ground_truth": {
            "answer": counterfactual_answer,
            "original_answer": original_answer,
            "label": item["label"],
            "category": item["category"],
            "is_counterfactual": True
        },
        "difficulty": "very_hard",
        "source_id": generate_id(sentence, question, "T5", "Stationarity-CF")
    }

def generate_counterfactual_duration(original: str) -> str:
    """Generate counterfactual duration (opposite magnitude)."""
    # Simple heuristic: if original is short, make long; if long, make short
    short_patterns = ["second", "minute", "hour", "short", "brief"]
    long_patterns = ["year", "century", "decade", "long", "extended"]
    
    original_lower = original.lower()
    
    for pattern in short_patterns:
        if pattern in original_lower:
            return "很长一段时间（反事实）"
    
    for pattern in long_patterns:
        if pattern in original_lower:
            return "很短的一瞬间（反事实）"
    
    return "与常识相反的时长（反事实）"

def convert_mctaco_to_conversational(input_file: str, output_file: str, split: str):
    """Main conversion function."""
    print(f"Loading {input_file}...")
    data = load_mctaco_data(input_file)
    print(f"Loaded {len(data)} Q&A pairs")
    
    # Group by sentence
    grouped = group_by_sentence(data)
    print(f"Grouped into {len(grouped)} unique sentences")
    
    converted_data = []
    stats = defaultdict(int)
    
    for sentence, items in grouped.items():
        # T1: Time Calculation
        for item in items:
            # Duration questions
            if item["category"] == "Event Duration":
                result = convert_t1_time_calc(item, sentence)
                if result:
                    converted_data.append(result)
                    stats["T1-TimeCalc"] += 1
            
            # Typical Time questions
            if item["category"] == "Typical Time":
                result = convert_t1_time_calc(item, sentence)
                if result:
                    converted_data.append(result)
                    stats["T1-TypicalTime"] += 1
            
            # T2: State Update
            if item["category"] == "Stationarity":
                result = convert_t2_stationarity(item, sentence)
                if result:
                    converted_data.append(result)
                    stats["T2-Stationarity"] += 1
            
            if item["category"] == "Event Ordering":
                result = convert_t2_ordering(item, sentence, items)
                if result:
                    converted_data.append(result)
                    stats["T2-Ordering"] += 1
            
            # T4: Long-term Memory
            if item["label"] == "yes":
                if random.random() < 0.3:  # Sample 30%for T4
                    result = convert_t4_buried(item, sentence)
                    if result:
                        converted_data.append(result)
                        stats["T4-Buried"] += 1
                
                if random.random() < 0.3:  # Sample 30% for noisy retrieval
                    result = convert_t4_noisy(item, sentence)
                    if result:
                        converted_data.append(result)
                        stats["T4-Noisy"] += 1
            
            # T5: Counterfactual
            if item["category"] == "Event Duration" and item["label"] == "yes":
                if random.random() < 0.2:  # Sample 20% for T5
                    result = convert_t5_counterfactual_duration(item, sentence)
                    if result:
                        converted_data.append(result)
                        stats["T5-Duration-CF"] += 1
            
            if item["category"] == "Stationarity" and item["label"] == "yes":
                if random.random() < 0.2:  # Sample 20% for T5
                    result = convert_t5_counterfactual_stationarity(item, sentence)
                    if result:
                        converted_data.append(result)
                        stats["T5-Stationarity-CF"] += 1
        
        # T3: Conflict Detection (requires multiple items)
        if random.random() < 0.1:  # 10% chance per sentence
            result = convert_t3_conflict(items, sentence)
            if result:
                converted_data.append(result)
                stats["T3-Conflict"] += 1
    
    # Write output
    print(f"Writing {len(converted_data)} converted items...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in converted_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Write stats
    stats_file = output_file.replace('.jsonl', '_report.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        report = {
            "source": "MCTACO",
            "split": split,
            "total_items": len(converted_data),
            "statistics": dict(stats),
            "task_distribution": {
                "T1": stats.get("T1-TimeCalc", 0) + stats.get("T1-TypicalTime", 0),
                "T2": stats.get("T2-Stationarity", 0) + stats.get("T2-Ordering", 0),
                "T3": stats.get("T3-Conflict", 0),
                "T4": stats.get("T4-Buried", 0) + stats.get("T4-Noisy", 0),
                "T5": stats.get("T5-Duration-CF", 0) + stats.get("T5-Stationarity-CF", 0)
            }
        }
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"Conversion complete. Stats: {dict(stats)}")
    return stats

def main():
    # Set random seed for reproducibility
    random.seed(42)    
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data", "MCTACO", "dataset")
    output_dir = os.path.join(base_dir, "converted_data_v3")
    
    # Convert dev set
    dev_input = os.path.join(data_dir, "dev_3783.tsv")
    dev_output = os.path.join(output_dir, "mctaco_conversational.jsonl")
    print("\n=== Converting DEV set ===")
    convert_mctaco_to_conversational(dev_input, dev_output, "dev")
    
    # Convert test set
    test_input = os.path.join(data_dir, "test_9442.tsv")
    test_output = os.path.join(output_dir, "mctaco_test_conversational.jsonl")
    print("\n=== Converting TEST set ===")
    convert_mctaco_to_conversational(test_input, test_output, "test")
    
    print("\n=== Conversion Complete ===")

if __name__ == "__main__":
    main()