#!/usr/bin/env python3
"""
Dataset Cleaning Pipeline for Timeaware Benchmark

This script:
1. Loads all 49 JSONL files from converted_data_v3
2. Deduplicates by context+query hash
3. Groups by sub-dimension using subtask_merge_map.json
4. Scores quality based on task relevance
5. Selects top N items per sub-dimension
6. Outputs cleaned data organized by capability (T1-T5)

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
INTERPRETATION_DIR = Path("D:/workspace/timeaware/data-Interpretation")

TARGET_PER_SUBDIM = 500  # Target items per sub-dimension


def load_subtask_map() -> Dict:
    """Load the subtask merge mapping."""
    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_hash(context: str, query: str) -> str:
    """Compute unique hash for context+query combination."""
    combined = f"{context}|{query}"
    return hashlib.md5(combined.encode('utf-8')).hexdigest()


def load_all_jsonl_files() -> Tuple[List[Dict], Dict[str, int]]:
    """Load all JSONL files and return items with source file counts."""
    all_items = []
    file_counts = {}
    
    jsonl_files = list(INPUT_DIR.glob("*.jsonl"))
    print(f"Found {len(jsonl_files)} JSONL files")
    
    for jsonl_file in jsonl_files:
        count = 0
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    item['_source_file'] = jsonl_file.name
                    all_items.append(item)
                    count += 1
                except json.JSONDecodeError as e:
                    print(f"Error parsing {jsonl_file.name}: {e}")
                    continue
        file_counts[jsonl_file.name] = count
        print(f"  {jsonl_file.name}: {count} items")
    
    return all_items, file_counts


def map_subtask_to_subdimension(item: Dict, subtask_map: Dict) -> str:
    """Map item's sub_task to a sub-dimension key."""
    task = item.get('task', '')
    sub_task = item.get('sub_task', '')
    
    if task not in subtask_map:
        return f"{task}_UNKNOWN"
    
    task_map = subtask_map[task]
    
    # Find which sub-dimension this sub_task belongs to
    for sub_dim, sub_task_data in task_map.items():
        if isinstance(sub_task_data, dict):
            for sub_task_type, files in sub_task_data.items():
                if sub_task_type == sub_task:
                    return f"{task}-{sub_dim}"
    
    # If not found, return sub_task as-is
    return sub_task


def deduplicate_items(items: List[Dict]) -> Tuple[List[Dict], Dict]:
    """Remove duplicates based on context+query hash."""
    seen_hashes = {}
    duplicates = defaultdict(int)
    
    unique_items = []
    for item in items:
        context = item.get('context', '')
        query = item.get('query', '')
        hash_key = compute_hash(context, query)
        
        if hash_key not in seen_hashes:
            seen_hashes[hash_key] = item
            unique_items.append(item)
        else:
            duplicates[item['_source_file']] += 1
    
    dup_stats = {
        'total_duplicates': sum(duplicates.values()),
        'duplicates_by_file': dict(duplicates)
    }
    
    return unique_items, dup_stats


def group_by_subdimension(items: List[Dict], subtask_map: Dict) -> Dict[str, List[Dict]]:
    """Group items by sub-dimension."""
    groups = defaultdict(list)
    
    for item in items:
        sub_dim = map_subtask_to_subdimension(item, subtask_map)
        groups[sub_dim].append(item)
    
    return dict(groups)


def analyze_groups(groups: Dict[str, List[Dict]]) -> Dict:
    """Analyze grouped items and return statistics."""
    stats = {}
    
    for sub_dim, items in sorted(groups.items()):
        # Extract task from sub_dim
        task = sub_dim.split('-')[0] if '-' in sub_dim else sub_dim[0]
        
        # Count by source file
        source_counts = defaultdict(int)
        difficulty_counts = defaultdict(int)
        
        for item in items:
            source_counts[item.get('_source_file', 'unknown')] += 1
            difficulty_counts[item.get('difficulty', 'unknown')] += 1
        
        stats[sub_dim] = {
            'task': task,
            'total_items': len(items),
            'source_distribution': dict(source_counts),
            'difficulty_distribution': dict(difficulty_counts),
            'unique_sources': len(source_counts)
        }
    
    return stats


def quality_score_item(item: Dict, sub_dim: str) -> float:
    """
    Score an item's quality based on task relevance.
    
    Criteria:
    1. Has non-empty context and query
    2. Answer is well-formed
    3. Has ground_truth data
    4. Conversation has multiple turns (bonus)
    5. Has meaningful state_info (bonus)
    """
    score = 0.0
    
    # Check basic fields (40 points)
    context = item.get('context', '')
    query = item.get('query', '')
    answer = item.get('answer', '')
    
    if context and len(context) > 10:
        score += 15
    if query and len(query) > 5:
        score += 15
    if answer and len(str(answer)) > 0:
        score += 10
    
    # Check ground_truth (20 points)
    ground_truth = item.get('ground_truth', {})
    if ground_truth:
        if ground_truth.get('correct_answer') or ground_truth.get('all_answers'):
            score += 10
        if ground_truth.get('original_question'):
            score += 10
    
    # Check conversation depth (20 points)
    conversation = item.get('conversation', [])
    if conversation:
        if len(conversation) >= 2:
            score += 10
        if len(conversation) >= 4:
            score += 10
    
    # Check state_info richness (20 points)
    state_info = item.get('state_info', {})
    if state_info:
        score += 5
        if state_info.get('type'):
            score += 5
        if state_info.get('time_constraint') or state_info.get('entity'):
            score += 5
        if len(state_info) > 3:
            score += 5
    
    return score


def select_top_items_per_subdim(
    groups: Dict[str, List[Dict]], 
    target: int = TARGET_PER_SUBDIM
) -> Dict[str, List[Dict]]:
    """Select top N items per sub-dimension with diversity."""
    selected = {}
    
    for sub_dim, items in groups.items():
        # Score all items
        scored_items = [(quality_score_item(item, sub_dim), item) for item in items]
        
        # Sort by score descending
        scored_items.sort(key=lambda x: x[0], reverse=True)
        
        # Select items with source diversity
        selected_items = []
        source_counts = defaultdict(int)
        target_per_source = max(1, target // max(1, len(set(item['_source_file'] for item in items))))
        
        for score, item in scored_items:
            source_file = item['_source_file']
            
            # Prefer diversity: limit per-source if we have multiple sources
            if source_counts[source_file] < target_per_source:
                selected_items.append(item)
                source_counts[source_file] += 1
            
            if len(selected_items) >= target:
                break
        
        # If we don't have enough from diversity, fill from remaining
        if len(selected_items) < target:
            for score, item in scored_items:
                if item not in selected_items:
                    selected_items.append(item)
                if len(selected_items) >= target:
                    break
        
        selected[sub_dim] = selected_items[:target]
    
    return selected


def save_cleaned_data(selected: Dict[str, List[Dict]], output_dir: Path):
    """Save cleaned data organized by capability."""
    
    # Create output directories
    for task in ['T1', 'T2', 'T3', 'T4', 'T5']:
        (output_dir / task).mkdir(parents=True, exist_ok=True)
    
    # Save each sub-dimension
    for sub_dim, items in selected.items():
        # Determine task folder
        task = sub_dim.split('-')[0] if '-' in sub_dim else sub_dim[0]
        
        # Create filename from sub_dim
        filename = f"{sub_dim}.jsonl"
        filepath = output_dir / task / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in items:
                # Remove temporary fields
                output_item = {k: v for k, v in item.items() if not k.startswith('_')}
                f.write(json.dumps(output_item, ensure_ascii=False) + '\n')
        
        print(f"  Saved {len(items)} items to {filepath}")
    
    # Save summary report
    summary = {
        'source_stats': {
            'total_files_processed': 0,
            'total_items_loaded': 0,
            'total_items_after_dedup': 0,
        },
        'sub_dimension_stats': {},
        'final_counts': {}
    }
    
    for sub_dim, items in selected.items():
        summary['final_counts'][sub_dim] = len(items)
    
    with open(output_dir / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def main():
    """Main pipeline execution."""
    print("=" * 60)
    print("Dataset Cleaning Pipeline")
    print("=" * 60)
    
    # Load subtask map
    print("\n[Phase 1] Loading subtask merge map...")
    subtask_map = load_subtask_map()
    print(f"  Loaded {len(subtask_map)} top-level tasks")
    
    # Load all JSONL files
    print("\n[Phase 1] Loading all JSONL files...")
    all_items, file_counts = load_all_jsonl_files()
    total_loaded = len(all_items)
    print(f"\n  Total items loaded: {total_loaded}")
    
    # Deduplicate
    print("\n[Phase 2] Deduplicating items...")
    unique_items, dup_stats = deduplicate_items(all_items)
    print(f"  Duplicates removed: {dup_stats['total_duplicates']}")
    print(f"  Unique items: {len(unique_items)}")
    
    # Group by sub-dimension
    print("\n[Phase 1] Grouping by sub-dimension...")
    groups = group_by_subdimension(unique_items, subtask_map)
    print(f"  Found {len(groups)} unique sub-dimensions")
    
    # Analyze groups
    print("\n[Analysis] Sub-dimension statistics:")
    stats = analyze_groups(groups)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUB-DIMENSION SUMMARY (after dedup)")
    print("=" * 60)
    
    for sub_dim in sorted(stats.keys()):
        s = stats[sub_dim]
        print(f"{sub_dim}: {s['total_items']} items from {s['unique_sources']} sources")
    
    # Count by task
    task_counts = defaultdict(int)
    for sub_dim, s in stats.items():
        task_counts[sub_dim.split('-')[0] if '-' in sub_dim else sub_dim[0]] += s['total_items']
    
    print("\n" + "-" * 40)
    print("By Capability:")
    for task in sorted(task_counts.keys()):
        print(f"  {task}: {task_counts[task]} items")
    print(f"  TOTAL: {sum(task_counts.values())} items")
    
    # Select top items
    print("\n[Phase 4] Selecting top items per sub-dimension...")
    selected = select_top_items_per_subdim(groups, target=TARGET_PER_SUBDIM)
    
    # Save cleaned data
    print("\n[Phase 5] Saving cleaned data...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_cleaned_data(selected, OUTPUT_DIR)
    
    # Final summary
    print("\n" + "=" * 60)
    print("CLEANING COMPLETE")
    print("=" * 60)
    print(f"Original items: {total_loaded}")
    print(f"After dedup: {len(unique_items)}")
    print(f"Final selected: {sum(len(items) for items in selected.values())}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Save detailed report
    report = {
        'original_count': total_loaded,
        'after_dedup_count': len(unique_items),
        'final_count': sum(len(items) for items in selected.values()),
        'file_counts': file_counts,
        'duplicate_stats': dup_stats,
        'sub_dimension_stats': stats,
        'target_per_subdim': TARGET_PER_SUBDIM
    }
    
    with open(OUTPUT_DIR / 'cleaning_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed report saved to: {OUTPUT_DIR / 'cleaning_report.json'}")


if __name__ == '__main__':
    main()