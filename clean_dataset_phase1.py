#!/usr/bin/env python3
"""
Efficient Dataset Cleaning Pipeline - Phase 1: Indexing & Dedup

This script processes the dataset in phases:
Phase 1: Fast indexing and deduplication (mutations-only)
Phase 2: Quality scoring (separate script)
Phase 3: Selection and output
"""

import json
import hashlib
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import sys

# Configuration
INPUT_DIR = Path("D:/workspace/timeaware/converted_data_v3")
OUTPUT_DIR = Path("D:/workspace/timeaware/converted_data_v3_cleaned")
MAP_FILE = Path("D:/workspace/timeaware/.sisyphus/subtask_merge_map.json")
CACHE_FILE = Path("D:/workspace/timeaware/.cache_indexed_data.json")

TARGET_PER_SUBDIM = 500


def compute_hash(context: str, query: str) -> str:
    """Compute unique hash for context+query combination."""
    combined = f"{context}|{query}"
    return hashlib.md5(combined.encode('utf-8')).hexdigest()


def load_subtask_map() -> Dict:
    """Load the subtask merge mapping."""
    print("Loading subtask merge map...")
    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def process_jsonl_file(jsonl_path: Path) -> Tuple[List[Dict], int]:
    """Process a single JSONL file efficiently."""
    items = []
    count = 0
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                # Extractonly essential fields for indexing
                minimal_item = {
                    'task': item.get('task', ''),
                    'sub_task': item.get('sub_task', ''),
                    'context': item.get('context', ''),
                    'query': item.get('query', ''),
                    'answer': item.get('answer', ''),
                    'difficulty': item.get('difficulty', ''),
                    '_source_file': jsonl_path.name,
                    '_hash': compute_hash(item.get('context', ''), item.get('query', '')),
                    '_full_item': item  # Keep full item for later
                }
                items.append(minimal_item)
                count += 1
            except json.JSONDecodeError as e:
                continue
    
    return items, count


def main():
    """Phase 1: Index and deduplicate."""
    print("=" * 60)
    print("Phase 1: Indexing and Deduplication")
    print("=" * 60)
    
    # Load subtask map
    subtask_map = load_subtask_map()
    print(f"Loaded {len(subtask_map)} tasks from subtask map")
    
    # Get all JSONL files
    jsonl_files = sorted(INPUT_DIR.glob("*.jsonl"))
    print(f"\nFound {len(jsonl_files)} JSONL files to process")
    
    # Process files and accumulate stats
    all_items = []
    file_counts = {}
    seen_hashes = {}
    
    print("\nProcessing files...")
    for i, jsonl_file in enumerate(jsonl_files):
        items, count = process_jsonl_file(jsonl_file)
        file_counts[jsonl_file.name] = count
        
        # Dedup on-the-fly
        dup_count = 0
        for item in items:
            h = item['_hash']
            if h not in seen_hashes:
                seen_hashes[h] = item
                all_items.append(item)
            else:
                dup_count += 1
        
        print(f"  [{i+1}/{len(jsonl_files)}] {jsonl_file.name}: {count} items, {dup_count} dups")
        sys.stdout.flush()
    
    print(f"\n{'='*60}")
    print("DEDUPLICATION SUMMARY")
    print("=" * 60)
    print(f"Total items loaded: {sum(file_counts.values())}")
    print(f"Duplicates removed: {sum(file_counts.values()) - len(all_items)}")
    print(f"Unique items: {len(all_items)}")
    
    # Group by sub-dimension
    print("\nGrouping by sub-dimension...")
    groups = defaultdict(list)
    
    for item in all_items:
        task = item['task']
        sub_task = item['sub_task']
        
        # Find sub-dimension from map
        sub_dim = sub_task  # Default
        if task in subtask_map:
            task_map = subtask_map[task]
            for sd, std in task_map.items():
                if isinstance(std, dict):
                    if sub_task in std:
                        sub_dim = f"{task}-{sd}"
                        break
        
        groups[sub_dim].append(item)
    
    print(f"Found {len(groups)} unique sub-dimensions")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUB-DIMENSION DISTRIBUTION")
    print("=" * 60)
    
    # Sort by count descending
    sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)
    
    for sub_dim, items in sorted_groups:
        task = sub_dim.split('-')[0] if '-' in sub_dim else sub_dim[0]
        sources = set(item['_source_file'] for item in items)
        print(f"  {sub_dim}: {len(items)} items ({len(sources)} sources)")
    
    # Count by task
    task_counts = defaultdict(int)
    for sub_dim, items in groups.items():
        task = sub_dim.split('-')[0] if '-' in sub_dim else sub_dim[0]
        task_counts[task] += len(items)
    
    print("\n" + "-" * 40)
    print("By Capability:")
    for task in sorted(task_counts.keys()):
        print(f"  {task}: {task_counts[task]:,} items")
    print(f"  TOTAL: {sum(task_counts.values()):,} items")
    
    # Save intermediate cache
    print("\nSaving intermediate cache...")
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as minimal JSON
    cache_data = {
        'groups': {},
        'stats': {
            'total_loaded': sum(file_counts.values()),
            'total_unique': len(all_items),
            'file_counts': file_counts,
            'sub_dim_counts': {sd: len(items) for sd, items in groups.items()},
            'task_counts': dict(task_counts)
        }
    }
    
    # Save groups (without full items for now)
    for sub_dim, items in groups.items():
        cache_data['groups'][sub_dim] = [
            {
                'task': item['task'],
                'sub_task': item['sub_task'],
                'hash': item['_hash'],
                'source_file': item['_source_file'],
                'difficulty': item['difficulty']
            }
            for item in items
        ]
    
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
    
    print(f"Cache saved to: {CACHE_FILE}")
    
    # Save stats report
    report_file = OUTPUT_DIR / 'phase1_report.json'
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    report = {
        'total_loaded': sum(file_counts.values()),
        'total_unique': len(all_items),
        'duplicates_removed': sum(file_counts.values()) - len(all_items),
        'sub_dimension_counts': {sd: len(items) for sd, items in groups.items()},
        'task_counts': dict(task_counts),
        'file_counts': file_counts
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Report saved to: {report_file}")
    print("\nPhase 1 complete!")


if __name__ == '__main__':
    main()