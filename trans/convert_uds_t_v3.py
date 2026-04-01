#!/usr/bin/env python3
"""
UDS_T_v1.0 Dataset Conversion Script for Time-Aware Benchmark

Converts UDS_T temporal relation annotations to conversational format following the analysis in UDS_T_v1.0.md.

Task Mapping:
- T1 (Time Calculation): Duration comparison, temporal ordering from Beg/End coordinates
- T3 (Concurrent Conflict): Interval overlap detection for concurrent events

Key Features:
- Fine-grained temporal annotations (Beg/End on 0-100 scale)
- Duration labels for predicates
- Inter-sentential temporal relations
"""

import csv
import os
import json
import random
import hashlib
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

def load_tsv_data(filepath: str) -> List[Dict]:
    """Load TSV data file."""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            data.append(row)
    return data

def generate_id(pred1_text: str, pred2_text: str, task: str) -> str:
    """Generate unique ID for each converted item."""
    hash_input = f"{pred1_text}_{pred2_text}_{task}"
    hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:10]
    return f"uds_t_{task}_{hash_val}"

def parse_numeric_value(value: str) -> Optional[float]:
    """Parse numeric value from TSV (handle empty/invalid values)."""
    try:
        value = value.strip()
        if not value:
            return None
        return float(value)
    except (ValueError, TypeError):
        return None

def calculate_overlap(beg1: float, end1: float, beg2: float, end2: float) -> float:
    """Calculate overlap percentage between two intervals."""
    # Overlap start = max(beg1, beg2)
    # Overlap end = min(end1, end2)
    overlap_start = max(beg1, beg2)
    overlap_end = min(end1, end2)
    
    if overlap_start >= overlap_end:
        return 0.0
    
    overlap_length = overlap_end - overlap_start
    
    # Calculate overlap relative to each interval
    len1 = end1 - beg1
    len2 = end2 - beg2
    
    if len1 <= 0 or len2 <= 0:
        return 0.0
    
    # Return average overlap percentage
    overlap_pct1 = overlap_length / len1
    overlap_pct2 = overlap_length / len2
    
    return (overlap_pct1 + overlap_pct2) / 2

def determine_ordering(beg1: float, end1: float, beg2: float, end2: float) -> str:
    """
    Determine temporal ordering relationship between two events.
    
    Returns: 'before', 'after', 'contains', 'contained', 'overlap', 'simultaneous'
    """
    # Ensure beg <= end
    if beg1 > end1:
        beg1, end1 = end1, beg1
    if beg2 > end2:
        beg2, end2 = end2, beg2
    
    # Case 1: e1 completely before e2
    if end1 < beg2:
        return 'before'
    
    # Case 2: e1 completely after e2
    if beg1 > end2:
        return 'after'
    
    # Case 3: e1 contains e2 (e2 is fully within e1)
    if beg1 <= beg2 and end1 >= end2:
        return 'contains'
    
    # Case 4: e2 contains e1 (e1 is fully within e2)
    if beg2 <= beg1 and end2 >= end1:
        return 'contained'
    
    # Case 5: Partial overlap
    if beg1 < beg2 < end1 < end2:
        return 'overlap'
    if beg2 < beg1 < end2 < end1:
        return 'overlap'
    
    # Case 6: They start at the same time
    if beg1 == beg2:
        if end1 == end2:
            return 'simultaneous'
        elif end1 < end2:
            return 'contained'
        else:
            return 'contains'
    
    return 'overlap'

# Duration labels mapping (from UDS-T paper)
DURATION_LABELS = {
    0: 'instantaneous (瞬间)',
    1: 'seconds (几秒)',
    2: 'minutes (几分钟)',
    3: 'hours (几小时)',
    4: 'days (几天)',
    5: 'weeks (几周)',
    6: 'months (几个月)',
    7: 'years (几年)',
    8: 'decades (几十年)',
    9: 'centuries (几世纪)',
    10: 'eternal (永久)'
}

# Mutually exclusive predicate pairs (for T3 conflict detection)
MUTUALLY_EXCLUSIVE = {
    # Physical impossibility
    ('run', 'sit'): 'physical_location',
    ('sit', 'stand'): 'physical_location',
    ('sleep', 'run'): 'physical_activity',
    ('eat', 'speak'): 'mouth_usage',
    ('swim', 'walk'): 'location_impossible',
    
    # Attention conflicts
    ('drive', 'sleep'): 'attention_critical',
    ('read', 'write'): 'visual_attention', # Can be simultaneous
    ('listen', 'speak'): 'auditory_attention', # Can be simultaneous
    
    #_location conflicts
    ('arrive', 'depart'): 'location_temporal',
    ('enter', 'exit'): 'location_directional',
}

def get_conflict_type(pred1_lemma: str, pred2_lemma: str) -> Optional[str]:
    """Determine if two predicates have a conflict."""
    key1 = (pred1_lemma.lower(), pred2_lemma.lower())
    key2 = (pred2_lemma.lower(), pred1_lemma.lower())
    
    if key1 in MUTUALLY_EXCLUSIVE:
        return MUTUALLY_EXCLUSIVE[key1]
    if key2 in MUTUALLY_EXCLUSIVE:
        return MUTUALLY_EXCLUSIVE[key2]
    
    # Heuristic: High overlap + common conflict patterns
    return None

# ============== T1: Time Calculation (Ordering & Duration) ==============

def convert_to_t1_ordering(row: Dict) -> List[Dict]:
    """
    Convert UDS_T row to T1 temporal ordering task.
    
    Tests understanding of event ordering from Beg/End coordinates.
    """
    results = []
    
    pred1_text = row.get('Pred1.Text', '').strip()
    pred2_text = row.get('Pred2.Text', '').strip()
    pred1_lemma = row.get('Pred1.Lemma', '').strip()
    pred2_lemma = row.get('Pred2.Lemma', '').strip()
    
    if not pred1_text or not pred2_text:
        return results
    
    beg1 = parse_numeric_value(row.get('Pred1.Beg', ''))
    end1 = parse_numeric_value(row.get('Pred1.End', ''))
    beg2 = parse_numeric_value(row.get('Pred2.Beg', ''))
    end2 = parse_numeric_value(row.get('Pred2.End', ''))
    
    if None in [beg1, end1, beg2, end2]:
        return results
    
    # Determine ordering
    ordering = determine_ordering(beg1, end1, beg2, end2)
    
    # Create ordering question
    if ordering == 'before':
        correct_answer = f'"{pred1_text}" 在 "{pred2_text}" 之前发生/完成'
        ordering_cn = '之前'
    elif ordering == 'after':
        correct_answer = f'"{pred1_text}" 在 "{pred2_text}" 之后发生'
        ordering_cn = '之后'
    elif ordering == 'contains':
        correct_answer = f'"{pred1_text}" 包含了 "{pred2_text}" 的整个过程'
        ordering_cn = '包含'
    elif ordering == 'contained':
        correct_answer = f'"{pred1_text}" 发生在 "{pred2_text}" 期间内'
        ordering_cn = '被包含'
    elif ordering == 'overlap':
        correct_answer = f'"{pred1_text}" 和 "{pred2_text}" 有部分时间重叠'
        ordering_cn = '重叠'
    elif ordering == 'simultaneous':
        correct_answer = f'"{pred1_text}" 和 "{pred2_text}" 同时发生'
        ordering_cn = '同时'
    else:
        correct_answer = f'"{pred1_text}" 和 "{pred2_text}" 有时间交集'
        ordering_cn = '相交'
    
    # ============== T1 Variant 1: Ordering Multiple Choice ==============
    
    options = [
        f'A. "{pred1_text}" 完全在 "{pred2_text}" 之前结束',
        f'B. "{pred1_text}" 包含了 "{pred2_text}"',
        f'C. "{pred2_text}" 包含了 "{pred1_text}"',
        f'D. 两者有时间重叠但不完全包含',
        f'E. 两者同时发生'
    ]
    
    if ordering == 'before':
        correct_option = 'A'
    elif ordering == 'contains':
        correct_option = 'B'
    elif ordering == 'contained':
        correct_option = 'C'
    elif ordering == 'overlap':
        correct_option = 'D'
    else:
        correct_option = 'E'
    
    conversation1 = [
        {"role": "user", "content": f"分析以下两个动作的时序关系："},
        {"role": "user", "content": f"动作1：{pred1_text}"},
        {"role": "user", "content": f"动作2：{pred2_text}"},
        {"role": "assistant", "content": "我需要分析这两个动作的时间顺序。请告诉我它们的时间坐标。"},
        {"role": "user", "content": f"动作1的时间范围：[{beg1:.1f}, {end1:.1f}]（虚拟时间轴）"},
        {"role": "user", "content": f"动作2的时间范围：[{beg2:.1f}, {end2:.1f}]（虚拟时间轴）"},
        {"role": "assistant", "content": "根据时间坐标，我可以分析它们的时序关系。"},
        {"role": "user", "content": f"这两个动作的时序关系是："},
        {"role": "user", "content": "\n".join(options)}
    ]
    
    result1 = {
        "task": "T1",
        "sub_task": "T1-Ordering-MC",
        "context": f"Temporal ordering between '{pred1_text}' and '{pred2_text}'",
        "conversation": conversation1,
        "query": "选择正确的时序关系：",
        "answer": f"{correct_option}. {correct_answer}",
        "state_info": {
            "type": "temporal_ordering",
            "pred1": {"text": pred1_text, "lemma": pred1_lemma, "range": [beg1, end1]},
            "pred2": {"text": pred2_text, "lemma": pred2_lemma, "range": [beg2, end2]},
            "ordering": ordering
        },
        "ground_truth": {
            "pred1_beg": beg1,
            "pred1_end": end1,
            "pred2_beg": beg2,
            "pred2_end": end2,
            "ordering": ordering,
            "correct_answer": correct_answer
        },
        "difficulty": "medium",
        "source_id": generate_id(pred1_text, pred2_text, "T1_order")
    }
    results.append(result1)
    
    # ============== T1 Variant 2: Ordering Direct Question ==============
    
    conversation2 = [
        {"role": "user", "content": f"在给定的文本中，存在两个动作。"},
        {"role": "user", "content": f'动作1: "{pred1_text}"(时间区间: {beg1:.1f} -{end1:.1f})'},
        {"role": "user", "content": f'动作2: "{pred2_text}"(时间区间: {beg2:.1f} -{end2:.1f})'},
        {"role": "assistant", "content": "我看到了两个动作及其对应的时间区间。"},
        {"role": "user", "content": f"请描述动作1相对于动作2的时间关系。"}
    ]
    
    result2 = {
        "task": "T1",
        "sub_task": "T1-Ordering-Direct",
        "context": f"Direct ordering question",
        "conversation": conversation2,
        "query": f"{pred1_text} 相对于 {pred2_text} 的时序是什么？",
        "answer": correct_answer,
        "state_info": {
            "type": "ordering_description",
            "ordering": ordering
        },
        "ground_truth": {
            "ordering": ordering,
            "beg1": beg1, "end1": end1,
            "beg2": beg2, "end2": end2
        },
        "difficulty": "easy",
        "source_id": generate_id(pred1_text, pred2_text, "T1_direct")
    }
    results.append(result2)
    
    return results

def convert_to_t1_duration(row: Dict) -> List[Dict]:
    """
    Convert UDS_T row to T1 duration comparison task.
    
    Tests understanding of event duration from Duration labels.
    """
    results = []
    
    pred1_text = row.get('Pred1.Text', '').strip()
    pred2_text = row.get('Pred2.Text', '').strip()
    pred1_lemma = row.get('Pred1.Lemma', '').strip()
    pred2_lemma = row.get('Pred2.Lemma', '').strip()
    duration1 = parse_numeric_value(row.get('Pred1.Duration', ''))
    duration2 = parse_numeric_value(row.get('Pred2.Duration', ''))
    
    if None in [duration1, duration2]:
        return results
    
    if not pred1_text or not pred2_text:
        return results
    
    duration1_label = DURATION_LABELS.get(int(duration1), f'Duration level {int(duration1)}')
    duration2_label = DURATION_LABELS.get(int(duration2), f'Duration level {int(duration2)}')
    
    # ============== T1 Variant: Duration Comparison ==============
    
    if duration1 > duration2:
        comparison = f'"{pred1_text}" 持续时间更长'
        longer = pred1_text
        shorter = pred2_text
    elif duration1 < duration2:
        comparison = f'"{pred2_text}" 持续时间更长'
        longer = pred2_text
        shorter = pred1_text
    else:
        comparison = f'两者持续时间相近'
        longer = pred1_text
        shorter = pred2_text
    
    # Duration difference explanation
    diff = abs(duration1 - duration2)
    if diff == 0:
        diff_explanation = "两者持续时间相同"
    elif diff == 1:
        diff_explanation = "持续时间差别较小（一个等级）"
    elif diff <= 3:
        diff_explanation = "持续时间有中等差别"
    else:
        diff_explanation = "持续时间差别很大"
    
    conversation = [
        {"role": "user", "content": f"比较以下两个动作的持续时间："},
        {"role": "user", "content": f"动作1：{pred1_text}"},
        {"role": "user", "content": f"动作2：{pred2_text}"},
        {"role": "assistant", "content": "我需要分析这两个动作通常持续多长时间。"},
        {"role": "user", "content": f"动作1的典型持续时间：{duration1_label}"},
        {"role": "user", "content": f"动作2的典型持续时间：{duration2_label}"},
        {"role": "assistant", "content": "根据常见情况，我可以比较它们的持续时间。"},
        {"role": "user", "content": f"哪个动作的持续时间更长？请解释原因。"}
    ]
    
    result = {
        "task": "T1",
        "sub_task": "T1-Duration-Compare",
        "context": f"Duration comparison between '{pred1_text}' and '{pred2_text}'",
        "conversation": conversation,
        "query": f"{pred1_text} 和 {pred2_text} 哪个持续时间更长？",
        "answer": comparison,
        "state_info": {
            "type": "duration_comparison",
            "pred1_duration": int(duration1),
            "pred2_duration": int(duration2),
            "duration1_label": duration1_label,
            "duration2_label": duration2_label
        },
        "ground_truth": {
            "pred1_text": pred1_text,
            "pred2_text": pred2_text,
            "duration1": int(duration1),
            "duration2": int(duration2),
            "comparison": comparison,
            "difference": int(diff)
        },
        "difficulty": "easy",
        "source_id": generate_id(pred1_text, pred2_text, "T1_dur")
    }
    results.append(result)
    
    return results

# ============== T3: Concurrent Conflict (Interval Overlap) ==============

def convert_to_t3_conflict(row: Dict) -> List[Dict]:
    """
    Convert UDS_T row to T3 concurrent conflict task.
    
    Detects potential resource conflicts from overlapping time intervals.
    """
    results = []
    
    pred1_text = row.get('Pred1.Text', '').strip()
    pred2_text = row.get('Pred2.Text', '').strip()
    pred1_lemma = row.get('Pred1.Lemma', '').strip().lower()
    pred2_lemma = row.get('Pred2.Lemma', '').strip().lower()
    
    if not pred1_text or not pred2_text:
        return results
    
    beg1 = parse_numeric_value(row.get('Pred1.Beg', ''))
    end1 = parse_numeric_value(row.get('Pred1.End', ''))
    beg2 = parse_numeric_value(row.get('Pred2.Beg', ''))
    end2 = parse_numeric_value(row.get('Pred2.End', ''))
    
    if None in [beg1, end1, beg2, end2]:
        return results
    
    # Calculate overlap
    overlap_pct = calculate_overlap(beg1, end1, beg2, end2)
    
    # Only process if there's significant overlap
    if overlap_pct < 0.3:
        return results
    
    # Determine conflict type
    conflict_type = get_conflict_type(pred1_lemma, pred2_lemma)
    
    # Determine ordering for context
    ordering = determine_ordering(beg1, end1, beg2, end2)
    
    # ============== T3 Variant 1: Overlap Detection ==============
    
    overlap_description = ""
    if ordering == 'contains':
        overlap_description = f'"{pred1_text}" 完全包含了 "{pred2_text}"'
    elif ordering == 'contained':
        overlap_description = f'"{pred2_text}" 完全包含了 "{pred1_text}"'
    elif ordering == 'overlap':
        overlap_description = f'两者有部分时间重叠'
    elif ordering == 'simultaneous':
        overlap_description = f'两者同时发生'
    else:
        overlap_description = f'时间区间有交集'
    
    conversation1 = [
        {"role": "user", "content": f"分析以下两个动作是否可能产生时间冲突："},
        {"role": "user", "content": f"动作1：{pred1_text}"},
        {"role": "user", "content": f"动作2：{pred2_text}"},
        {"role": "assistant", "content": "我需要分析它们的时间区间是否重叠。"},
        {"role": "user", "content": f"动作1时间区间：[{beg1:.1f}, {end1:.1f}]"},
        {"role": "user", "content": f"动作2时间区间：[{beg2:.1f}, {end2:.1f}]"},
        {"role": "assistant", "content": "让我计算它们的重叠程度..."},
        {"role": "user", "content": f"重叠程度约为 {overlap_pct*100:.1f}%。这两个动作在时间上是并发/重叠的吗？如果并发，是否存在资源冲突？"}
    ]
    
    # Determine if concurrent
    is_concurrent = overlap_pct > 0
    
    if is_concurrent:
        if conflict_type:
            concurrent_answer = f"是的，两者是并发的，重叠度约{overlap_pct*100:.1f}%。\n存在的资源冲突：{conflict_type}型冲突。\n建议：主要资源（如{conflict_type.replace('_', ' ')}）在同一时间需要被两个动作同时使用。"
        else:
            concurrent_answer = f"是的，两者是并发的，重叠度约{overlap_pct*100:.1f}%。\n潜在冲突分析：虽然时间重叠，但这两个动作在资源使用上可能不存在直接冲突。"
    else:
        concurrent_answer = f"不是并发的。两者在时间上是分开的。"
    
    result1 = {
        "task": "T3",
        "sub_task": "T3-ConcurrentDetect",
        "context": f"Concurrent conflict detection for '{pred1_text}' and '{pred2_text}'",
        "conversation": conversation1,
        "query": f"{pred1_text} 和 {pred2_text} 是否并发？如果并发，有资源冲突吗？",
        "answer": concurrent_answer,
        "state_info": {
            "type": "overlap_detection",
            "pred1": {"text": pred1_text, "range": [beg1, end1]},
            "pred2": {"text": pred2_text, "range": [beg2, end2]},
            "overlap_percentage": overlap_pct,
            "is_concurrent": is_concurrent,
            "conflict_type": conflict_type,
            "ordering": ordering
        },
        "ground_truth": {
            "beg1": beg1, "end1": end1,
            "beg2": beg2, "end2": end2,
            "overlap_pct": overlap_pct,
            "ordering": ordering,
            "has_conflict": conflict_type is not None
        },
        "difficulty": "medium",
        "source_id": generate_id(pred1_text, pred2_text, "T3_overlap")
    }
    results.append(result1)
    
    # ============== T3 Variant 2: High Overlap Warning ==============
    
    if overlap_pct >= 0.5 and conflict_type:
        conversation2 = [
            {"role": "user", "content": f"警告：检测到高重叠区间！"},
            {"role": "user", "content": f"动作1：{pred1_text} [{beg1:.1f}, {end1:.1f}]"},
            {"role": "user", "content": f"动作2：{pred2_text} [{beg2:.1f}, {end2:.1f}]"},
            {"role": "assistant", "content": f"重叠度达到 {overlap_pct*100:.1f}%，这是相当高的并发程度。"},
            {"role": "user", "content": f"这种并发情况是否可能导致问题？"},
            {"role": "assistant", "content": "需要分析资源使用情况..."},
            {"role": "user", "content": f"请判断：这种并发在物理或认知资源上是否存在潜在冲突？"}
        ]
        
        if conflict_type == 'physical_location':
            conflict_answer = f"存在物理位置冲突：两个动作需要占据不同的空间位置，无法同时进行。"
        elif conflict_type == 'physical_activity':
            conflict_answer = f"存在身体活动冲突：两项身体活动需要不可同时使用的身体部位或姿态。"
        elif conflict_type == 'attention_critical':
            conflict_answer = f"存在注意力冲突：两项活动都需要高度集中的注意力，分散可能导致危险。"
        elif conflict_type:
            conflict_answer = f"存在{conflict_type}型资源冲突。"
        else:
            conflict_answer = f"虽然高度并发，但这两个动作可能可以同时进行（共享资源）。"
        
        result2 = {
            "task": "T3",
            "sub_task": "T3-ConflictWarning",
            "context": f"High overlap conflict warning",
            "conversation": conversation2,
            "query": "这种高度并发是否存在资源冲突？",
            "answer": conflict_answer,
            "state_info": {
                "type": "conflict_warning",
                "overlap_pct": overlap_pct,
                "conflict_type": conflict_type
            },
            "ground_truth": {
                "overlap_pct": overlap_pct,
                "conflict_type": conflict_type
            },
            "difficulty": "hard",
            "source_id": generate_id(pred1_text, pred2_text, "T3_warning")
        }
        results.append(result2)
    
    return results

# ============== Main Conversion Function ==============

def convert_uds_t_to_conversational(data: List[Dict], split: str) -> Tuple[List[Dict], Dict]:
    """
    Convert UDS_T data to conversational format.
    """
    converted_data = []
    stats = defaultdict(int)
    
    for row in data:
        # Skip rows with missing essential data
        if not row.get('Pred1.Text') or not row.get('Pred2.Text'):
            continue
        
        # T1: Ordering tasks
        ordering_results = convert_to_t1_ordering(row)
        for r in ordering_results:
            stats['T1-Ordering'] += 1
        converted_data.extend(ordering_results)
        
        # T1: Duration comparison (sample for efficiency)
        if random.random() < 0.3:
            duration_results = convert_to_t1_duration(row)
            for r in duration_results:
                stats['T1-Duration'] += 1
            converted_data.extend(duration_results)
        
        # T3: Concurrent conflict (only for overlapping intervals)
        conflict_results = convert_to_t3_conflict(row)
        for r in conflict_results:
            stats['T3-Conflict'] += 1
        converted_data.extend(conflict_results)
    
    return converted_data, dict(stats)

def main():
    random.seed(42)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data", "UDS_T_v1.0")
    output_dir = os.path.join(base_dir, "converted_data_v3")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load TSV file
    tsv_file = os.path.join(data_dir, "time_eng_ud_v1.2_2015_10_30.tsv")
    
    if not os.path.exists(tsv_file):
        print(f"File not found: {tsv_file}")
        return
    
    print(f"Loading {tsv_file}...")
    all_data = load_tsv_data(tsv_file)
    print(f"Loaded {len(all_data)} total rows")
    
    # Split by Split column
    train_data = [row for row in all_data if row.get('Split', '').strip() == 'train']
    dev_data = [row for row in all_data if row.get('Split', '').strip() == 'dev']
    test_data = [row for row in all_data if row.get('Split', '').strip() == 'test']
    
    print(f"\nSplit sizes: train={len(train_data)}, dev={len(dev_data)}, test={len(test_data)}")
    
    all_stats = {}
    
    # Process train
    print("\n" + "="*50)
    print("Processing TRAIN split")
    print("="*50)
    if train_data:
        converted, stats = convert_uds_t_to_conversational(train_data, "train")
        output_file = os.path.join(output_dir, "uds_t_train_conversational.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in converted:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Wrote {len(converted)} items. Stats: {stats}")
        all_stats['train'] = stats
    
    # Process dev
    print("\n" + "="*50)
    print("Processing DEV split")
    print("="*50)
    if dev_data:
        converted, stats = convert_uds_t_to_conversational(dev_data, "dev")
        output_file = os.path.join(output_dir, "uds_t_dev_conversational.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in converted:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Wrote {len(converted)} items. Stats: {stats}")
        all_stats['dev'] = stats
    
    # Process test
    print("\n" + "="*50)
    print("Processing TEST split")
    print("="*50)
    if test_data:
        converted, stats = convert_uds_t_to_conversational(test_data, "test")
        output_file = os.path.join(output_dir, "uds_t_test_conversational.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in converted:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Wrote {len(converted)} items. Stats: {stats}")
        all_stats['test'] = stats
    
    # Summary
    print("\n" + "="*50)
    print("CONVERSION COMPLETE")
    print("="*50)
    
    total_t1_order = sum(s.get('T1-Ordering', 0) for s in all_stats.values())
    total_t1_dur = sum(s.get('T1-Duration', 0) for s in all_stats.values())
    total_t3 = sum(s.get('T3-Conflict', 0) for s in all_stats.values())
    
    print(f"Total T1 (Ordering) items: {total_t1_order}")
    print(f"Total T1 (Duration) items: {total_t1_dur}")
    print(f"Total T3 (Conflict) items: {total_t3}")
    print(f"\nDetailed stats:")
    for split_name, split_stats in all_stats.items():
        print(f"  {split_name}: {split_stats}")
    
    print(f"\nAll output files saved to: {output_dir}")

if __name__ == "__main__":
    main()