#!/usr/bin/env python3
"""
Dataset Cleaning Pipeline - Phase 2: Quality Scoring & Selection

This script:
1. Loads the indexed data from Phase 1
2. Scores each item for quality (task relevance)
3. Selects top N items per sub-dimension
4. Outputs cleaned data organized by capability

Target: ~500 items per sub-dimension (~29,000 total)
"""

import json
import hashlib
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import random

# Configuration
INPUT_DIR = Path("D:/workspace/timeaware/converted_data_v3")
OUTPUT_DIR = Path("D:/workspace/timeaware/converted_data_v3_cleaned")
MAP_FILE = Path("D:/workspace/timeaware/.sisyphus/subtask_merge_map.json")
REPORT_FILE = Path("D:/workspace/timeaware/converted_data_v3_cleaned/phase1_report.json")

TARGET_PER_SUBDIM = 500


def load_phase1_report() -> Dict:
    """Load the report from Phase 1."""
    with open(REPORT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_subtask_map() -> Dict:
    """Load the subtask merge mapping."""
    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_hash(context: str, query: str) -> str:
    """Compute unique hash for context+query combination."""
    combined = f"{context}|{query}"
    return hashlib.md5(combined.encode('utf-8')).hexdigest()


def quality_score_item(item: Dict) -> Tuple[float, Dict]:
    """
    Score an item's quality based on task relevance.
    
    Returns (score, score_breakdown)
    """
    score = 0.0
    breakdown = {}
    
    # 1. Context quality (25 points)
    context = item.get('context', '')
    if context:
        # Longer context = more information
        context_len = len(context)
        if context_len > 50:
            score += 10
            breakdown['context_length'] = 10
        if context_len > 200:
            score += 5
            breakdown['context_detail'] = 5
        
        # Specific task context
        if any(kw in context.lower() for kw in ['时间', 'time', '状态', 'state', '冲突', 'conflict', '记忆', 'memory', '反事实', 'counterfactual']):
            score += 10
            breakdown['context_relevance'] = 10
    
    # 2. Query quality (25 points)
    query = item.get('query', '')
    if query:
        query_len = len(query)
        if query_len > 10:
            score += 10
            breakdown['query_length'] = 10
        
        # Question mark indicates proper question
        if '？' in query or '?' in query:
            score += 5
            breakdown['query_format'] = 5
            
        # Contains temporal/state keywords
        if any(kw in query for kw in ['什么', '何时', '多少', 'where', 'when', 'how', '是否']):
            score += 10
            breakdown['query_type'] = 10
    
    # 3. Answer quality (25 points)
    answer = item.get('answer', '')
    if answer:
        answer_len = len(str(answer))
        if answer_len > 0:
            score += 10
            breakdown['answer_exists'] = 10
        if answer_len > 5:
            score += 10
            breakdown['answer_length'] = 10
        if answer_len > 20:
            score += 5
            breakdown['answer_detail'] = 5
    
    # 4. Ground truth quality (15 points)
    ground_truth = item.get('ground_truth', {})
    if ground_truth:
        score += 5
        breakdown['has_ground_truth'] = 5
        if ground_truth.get('correct_answer'):
            score += 5
            breakdown['correct_answer'] = 5
        if ground_truth.get('original_question'):
            score += 5
            breakdown['original_question'] = 5
    
    # 5. Conversation depth (10 points)
    conversation = item.get('conversation', [])
    if conversation:
        conv_len = len(conversation)
        if conv_len >= 2:
            score += 5
            breakdown['conversation_min'] = 5
        if conv_len >= 4:
            score += 5
            breakdown['conversation_depth'] = 5
    
    return score, breakdown


def select_items_smart(
    items: List[Dict], 
    target: int,
    source_diversity: bool = True
) -> List[Dict]:
    """
    Select top N items with smart sampling.
    
    For sub-dimensions with > target items:
    - Score all items
    - Select top items with source diversity
    """
    if len(items) <= target:
        return items
    
    # Score all items
    scored_items = [(quality_score_item(item)[0], item) for item in items]
    
    # Sort by score descending
    scored_items.sort(key=lambda x: x[0], reverse=True)
    
    if not source_diversity:
        # Simple: just take top N
        return [item for score, item in scored_items[:target]]
    
    # Diversified selection
    sources = set(item['_source_file'] for item in items)
    
    # If only one source, take top N
    if len(sources) == 1:
        return [item for score, item in scored_items[:target]]
    
    # Distribute across sources proportionally
    source_items = defaultdict(list)
    for score, item in scored_items:
        source_items[item['_source_file']].append((score, item))
    
    selected = []
    per_source_target = max(1, target // len(sources))
    
    # Take top per_source_target from each source
    remaining_target = target
    for source in sources:
        take = min(per_source_target, len(source_items[source]), remaining_target)
        selected.extend([item for score, item in source_items[source][:take]])
        remaining_target = target - len(selected)
    
    # Fill remaining from highest scores
    if remaining_target > 0:
        taken_hashes = set(compute_hash(item.get('context', ''), item.get('query', '')) for item in selected)
        for score, item in scored_items:
            h = compute_hash(item.get('context', ''), item.get('query', ''))
            if h not in taken_hashes:
                selected.append(item)
                if len(selected) >= target:
                    break
    
    return selected[:target]


def save_subdim_file(items: List[Dict], output_path: Path):
    """Save items to JSONL file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in items:
            # Remove internal fields
            output_item = {k: v for k, v in item.items() if not k.startswith('_')}
            f.write(json.dumps(output_item, ensure_ascii=False) + '\n')


def process_subdimension_files():
    """Process each source file and select items per sub-dimension."""
    
    # Load report
    report = load_phase1_report()
    subtask_map = load_subtask_map()
    
    print("=" * 60)
    print("Phase 2: Quality Scoring & Selection")
    print("=" * 60)
    print(f"Target: {TARGET_PER_SUBDIM} items per sub-dimension")
    
    # Get sub-dimension counts from Phase 1
    sub_dim_counts = report['sub_dimension_counts']
    
    print(f"\nSub-dimensions to process: {len(sub_dim_counts)}")
    
    # Group items by sub-dimension (reload from source files)
    print("\n[Loading items from source files...]")
    groups = defaultdict(list)
    
    jsonl_files = list(INPUT_DIR.glob("*.jsonl"))
    processed_files = 0
    
    for jsonl_file in jsonl_files:
        processed_files += 1
        if processed_files % 10 == 0:
            print(f"  Processing file {processed_files}/{len(jsonl_files)}...")
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    item['_source_file'] = jsonl_file.name
                    
                    # Get task and sub_task
                    task = item.get('task', '')
                    sub_task = item.get('sub_task', '')
                    
                    # Map to sub-dimension
                    sub_dim = sub_task
                    if task in subtask_map:
                        task_map = subtask_map[task]
                        for sd, std in task_map.items():
                            if isinstance(std, dict) and sub_task in std:
                                sub_dim = f"{task}-{sd}"
                                break
                    
                    groups[sub_dim].append(item)
                except json.JSONDecodeError:
                    continue
    
    print(f"  Loaded {sum(len(items) for items in groups.values())} unique items")
    
    # Select items per sub-dimension
    print("\n[Selecting items per sub-dimension...]")
    
    # Create output directories
    for task in ['T1', 'T2', 'T3', 'T4', 'T5']:
        (OUTPUT_DIR / task).mkdir(parents=True, exist_ok=True)
    
    selection_stats = {}
    total_selected = 0
    
    for sub_dim, items in sorted(groups.items()):
        # Determine task folder
        task = sub_dim.split('-')[0] if '-' in sub_dim else sub_dim[0]
        
        # Select items
        selected = select_items_smart(items, TARGET_PER_SUBDIM,source_diversity=True)
        
        # Save to file
        filename = f"{sub_dim}.jsonl"
        output_path = OUTPUT_DIR / task / filename
        save_subdim_file(selected, output_path)
        
        selection_stats[sub_dim] = {
            'original': len(items),
            'selected': len(selected),
            'sources': len(set(item['_source_file'] for item in items))
        }
        
        total_selected += len(selected)
        
        if len(items) > TARGET_PER_SUBDIM:
            print(f"  {sub_dim}: {len(items)} -> {len(selected)} items")
    
    # Summary
    print("\n" + "=" * 60)
    print("SELECTION SUMMARY")
    print("=" * 60)
    print(f"Total sub-dimensions: {len(selection_stats)}")
    print(f"Total items selected: {total_selected}")
    print(f"Target per sub-dim: {TARGET_PER_SUBDIM}")
    
    # Count by task
    task_stats = defaultdict(lambda: {'original': 0, 'selected': 0})
    for sub_dim, stats in selection_stats.items():
        task = sub_dim.split('-')[0] if '-' in sub_dim else sub_dim[0]
        task_stats[task]['original'] += stats['original']
        task_stats[task]['selected'] += stats['selected']
    
    print("\nBy Capability:")
    for task in sorted(task_stats.keys()):
        s = task_stats[task]
        print(f"  {task}: {s['original']:,} -> {s['selected']:,} items")
    
    # Save final report
    final_report = {
        'phase1': report,
        'selection': {
            'target_per_subdim': TARGET_PER_SUBDIM,
            'total_selected': total_selected,
            'sub_dimension_stats': selection_stats,
            'task_stats': dict(task_stats)
        }
    }
    
    with open(OUTPUT_DIR / 'cleaning_report.json', 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print(f"\nFinal report saved to: {OUTPUT_DIR / 'cleaning_report.json'}")
    print("\nPhase 2 complete!")


if __name__ == '__main__':
    process_subdimension_files()