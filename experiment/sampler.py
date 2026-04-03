"""Data sampler for the Timeaware Benchmark Experiment.

Loads jsonl files from converted_data_v3, finds samples matching target subtasks,
and performs stratified sampling across atomic tasks.
"""

import json
import os
import random
from typing import Dict, List, Any, Optional
from collections import defaultdict

from experiment.subtask_config import SUBTASK_CONFIG, DATA_DIR


def _discover_jsonl_files() -> Dict[str, str]:
    """Build a mapping: sub_task_name -> jsonl_file_path.
    
    Scans actual jsonl files to find which files contain which subtasks.
    Falls back to report files if jsonl scanning fails.
    Returns: {sub_task: jsonl_path}
    """
    subtask_to_file = {}
    
    # First, scan actual jsonl files for accurate sub_task names
    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.endswith('.jsonl'):
            continue
        
        jsonl_path = os.path.join(DATA_DIR, fname)
        seen_subtasks = set()
        
        try:
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i > 20:  # Check first 20 lines only
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        st = data.get('sub_task', '')
                        if st and st not in seen_subtasks:
                            seen_subtasks.add(st)
                            subtask_to_file[st] = jsonl_path
                    except json.JSONDecodeError:
                        continue
        except Exception:
            continue
    
    # Fall back to report files for any subtasks not found in jsonl scanning
    for fname in os.listdir(DATA_DIR):
        if not fname.endswith('_report.json'):
            continue
        
        report_path = os.path.join(DATA_DIR, fname)
        jsonl_path = report_path.replace('_report.json', '.jsonl')
        
        if not os.path.exists(jsonl_path):
            continue
        
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        # Check both 'subtask_distribution' and 'statistics'
        subtask_dist = report.get('subtask_distribution', report.get('statistics', {}))
        
        for subtask_name in subtask_dist.keys():
            if subtask_name not in subtask_to_file:
                subtask_to_file[subtask_name] = jsonl_path
    
    return subtask_to_file


# Cache the discovery result
_SUBTASK_FILE_MAP = None

def _get_subtask_file_map() -> Dict[str, str]:
    global _SUBTASK_FILE_MAP
    if _SUBTASK_FILE_MAP is None:
        _SUBTASK_FILE_MAP = _discover_jsonl_files()
    return _SUBTASK_FILE_MAP


def _load_samples_from_file(jsonl_path: str, target_subtasks: List[str],
                             max_per_subtask: Optional[int] = None) -> Dict[str, List[Dict]]:
    """Load samples from a jsonl file, filtering by target subtasks.
    
    Returns: {sub_task: [sample_dicts]}
    """
    results = defaultdict(list)
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                sub_task = data.get('sub_task', '')
                if sub_task in target_subtasks:
                    if max_per_subtask is None or len(results[sub_task]) < max_per_subtask:
                        results[sub_task].append(data)
            except json.JSONDecodeError:
                continue
    
    return dict(results)


def sample_subtask(subtask_key: str, sample_count: int = 10, 
                    seed: int = 42) -> List[Dict[str, Any]]:
    """Sample data for a single subtask configuration.
    
    Args:
        subtask_key: Key in SUBTASK_CONFIG (e.g., "T1-Ordering")
        sample_count: Number of samples to draw per atomic task
        seed: Random seed for reproducibility
    
    Returns:
        List of sample dicts, each enriched with:
            - _subtask_key: the merged subtask key
            - _atomic_task: the original sub_task name
            - _source_file: the jsonl file it came from
    """
    config = SUBTASK_CONFIG[subtask_key]
    atomic_tasks = config['atomic_tasks']
    file_map = _get_subtask_file_map()
    
    random.seed(seed)
    all_samples = []
    
    for atomic_task in atomic_tasks:
        jsonl_path = file_map.get(atomic_task)
        if not jsonl_path or not os.path.exists(jsonl_path):
            print(f"  [WARN] File not found for atomic task: {atomic_task}")
            continue
        
        # Load all matching samples
        loaded = _load_samples_from_file(jsonl_path, [atomic_task], max_per_subtask=sample_count + 50)
        samples = loaded.get(atomic_task, [])
        
        if not samples:
            print(f"  [WARN] No samples found for: {atomic_task}")
            continue
        
        # Sample
        n = min(sample_count, len(samples))
        sampled = random.sample(samples, n)
        
        for s in sampled:
            s['_subtask_key'] = subtask_key
            s['_atomic_task'] = atomic_task
            s['_source_file'] = os.path.basename(jsonl_path)
        
        all_samples.extend(sampled)
        print(f"  {atomic_task}: sampled {n}/{len(samples)}")
    
    return all_samples


def sample_all_subtasks(sample_count: int = 10, 
                         seed: int = 42,
                         subtask_filter: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
    """Sample data for all (or filtered) subtasks.
    
    Args:
        sample_count: Default samples per atomic task
        seed: Random seed
        subtask_filter: If provided, only sample these subtask keys
    
    Returns:
        {subtask_key: [sample_dicts]}
    """
    results = {}
    
    keys_to_sample = subtask_filter or list(SUBTASK_CONFIG.keys())
    
    for subtask_key in keys_to_sample:
        if subtask_key not in SUBTASK_CONFIG:
            print(f"[WARN] Unknown subtask key: {subtask_key}")
            continue
        
        config = SUBTASK_CONFIG[subtask_key]
        # Use passed sample_count parameter, not config value
        n = sample_count if sample_count else config.get('sample_count', 10)
        if n == 'all':
            n = 999999  # effectively all
        
        print(f"\nSampling {subtask_key} (target: {n} per atomic task)...")
        samples = sample_subtask(subtask_key, sample_count=n, seed=seed)
        results[subtask_key] = samples
        print(f"  Total: {len(samples)} samples")
    
    return results


def get_sample_statistics(samples: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """Generate statistics about the sampled data."""
    stats = {
        "total_samples": 0,
        "by_dimension": defaultdict(int),
        "by_subtask": {},
        "by_difficulty": defaultdict(int),
    }
    
    for subtask_key, samples_list in samples.items():
        stats["by_subtask"][subtask_key] = len(samples_list)
        stats["total_samples"] += len(samples_list)
        
        dim = SUBTASK_CONFIG[subtask_key]['dimension']
        stats["by_dimension"][dim] += len(samples_list)
        
        for s in samples_list:
            diff = s.get('difficulty', 'unknown')
            stats["by_difficulty"][diff] += 1
    
    # Convert defaultdicts to dicts for JSON serialization
    stats["by_dimension"] = dict(stats["by_dimension"])
    stats["by_difficulty"] = dict(stats["by_difficulty"])
    
    return stats
