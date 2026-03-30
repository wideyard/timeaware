#!/usr/bin/env python3
"""
Generate Final Dataset Statistics Report
========================================
"""
import json
from pathlib import Path
from collections import defaultdict

def generate_final_report():
    """Generate comprehensive statistics report"""
    input_dir = Path("converted_data_v2")
    
    # Task mapping
    TASK_MAPPING = {
        'timeqa': 'T1', 'drop': 'T1', 'mctaco': 'T1',
        'openpi': 'T2', 'pasta': 'T2', 'propara': 'T2', 'situated': 'T2',
        't3': 'T3', 'trip': 'T3', 'atomic': 'T3',
        'longbench': 'T4', 'narrative': 'T4',
        't5': 'T5', 'counterfactual': 'T5', 'dialogue': 'T5',
        'piqa': 'T5', 'hellaswag': 'T5', 'winogrande': 'T5',
        'cosmosqa': 'T3', 'socialiqa': 'T3', 'choice': 'T2'
    }
    
    dataset_stats = {}
    task_stats = defaultdict(lambda: {'total': 0, 'files': []})
    
    for file_path in sorted(input_dir.glob('*.jsonl')):
        if file_path.name in ['validation_results.json', 'reformat_summary.json']:
            continue
        
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for _ in f:
                count += 1
        
        dataset_name = file_path.stem
        
        # Map to task
        task = None
        for key, t in TASK_MAPPING.items():
            if key in dataset_name.lower():
                task = t
                break
        if not task:
            task = 'T1'  # Default
        
        # Special handling
        if 'dialogue' in dataset_name.lower():
            task = 'T2'  # Dialogue temporal is T2
        
        dataset_stats[dataset_name] = {
            'total': count,
            'task': task,
            'file': str(file_path.name)
        }
        
        task_stats[task]['total'] += count
        task_stats[task]['files'].append(dataset_name)
    
    # Generate report
    print("=" * 70)
    print("TEMPORAL WORLD MODELING BENCHMARK - FINAL DATASET STATISTICS")
    print("=" * 70)
    
    print("\n## Overview\n")
    total_samples = sum(s['total'] for s in dataset_stats.values())
    print(f"Total Datasets: {len(dataset_stats)}")
    print(f"Total Samples: {total_samples:,}")
    
    print("\n## Task Distribution\n")
    print("| Task | Task Name | Samples | Datasets |")
    print("|------|------------|---------|----------|")
    
    task_names = {
        'T1': 'Temporal Calculation',
        'T2': 'State Tracking',
        'T3': 'Concurrency/Conflict',
        'T4': 'Long-term Memory',
        'T5': 'Counterfactual'
    }
    
    for task in ['T1', 'T2', 'T3', 'T4', 'T5']:
        stats = task_stats[task]
        print(f"| {task} | {task_names[task]} | {stats['total']:,} | {len(stats['files'])} |")
    
    print("\n## Dataset Details\n")
    print("| Dataset | Task | Samples | Description |")
    print("|----------|------|---------|-------------|")
    
    dataset_descriptions = {
        'timeqa_dev': 'Time reasoning QA (dev)',
        'timeqa_train': 'Time reasoning QA (train)',
        'timeqa_easy': 'Time reasoning QA (easy, unlabeled)',
        'timeqa_hard': 'Time reasoning QA (hard, unlabeled)',
        'timeqa_test': 'Time reasoning QA (test)',
        'drop': 'Numerical reasoning with temporal context',
        'mctaco': 'Temporal commonsense',
        'openpi2_t2': 'Entity state tracking',
        'pasta_t2_t5': 'Participant states with counterfactuals',
        'propara': 'Procedure state tracking',
        'propara_fixed': 'ProPara with fixed answers',
        'propara_fixed_v2': 'ProPara with complete state info',
        'situated_gen_t2_t5': 'Situated generation',
        't3_conflict_detection': 'Conflict detection synthetic',
        'atomic_fixed': 'Commonsense reasoning',
        'trip_conflict_t3': 'Travel planning conflicts',
        'longbench_qasper_t4': 'Long document QA',
        'narrativeqa': 'Narrative understanding',
        't5_counterfactual': 'Rule perturbation reasoning',
        'dialogue_temporal_benchmark': 'Dialogue temporal reasoning',
        'piqa': 'Physical commonsense',
        'hellaswag': 'Context completion',
        'winogrande': 'Coreference resolution',
        'cosmosqa': 'Commonsense story QA',
        'socialiqa_train': 'Social intelligence QA',
    }
    
    for dataset, stats in sorted(dataset_stats.items(), key=lambda x: x[1]['total'], reverse=True):
        desc = dataset_descriptions.get(dataset, '')
        print(f"| {dataset} | {stats['task']} | {stats['total']:,} | {desc} |")
    
    print("\n## Validation Summary\n")
    
    # Read validation results
    val_file = input_dir / 'validation_results.json'
    if val_file.exists():
        with open(val_file, 'r', encoding='utf-8') as f:
            val_results = json.load(f)
        
        valid_rate = val_results['summary']['validation_rate']
        print(f"- Overall Validation Rate: {valid_rate:.1f}%")
        print(f"- Valid Samples: {val_results['summary']['valid_samples']:,}")
        print(f"- Total Samples: {val_results['summary']['total_samples']:,}")
    
    print("\n## Notes\n")
    print("- `timeqa_easy` and `timeqa_hard` have empty answers (test sets for model prediction)")
    print("- `propara` has some samples with unknown states (empty answers)")
    print("- `situated_gen` has some samples without answers (context generation tasks)")
    print("- All other datasets have complete ground truth annotations")
    
    print("\n## File Locations\n")
    print(f"- Directory: `{input_dir}`")
    print(f"- Validation Report: `{input_dir / 'validation_results.json'}`")
    print(f"- Reformat Summary: `{input_dir / 'reformat_summary.json'}`")
    
    # Save final report
    final_report = {
        'summary': {
            'total_datasets': len(dataset_stats),
            'total_samples': total_samples,
            'validation_rate': val_results['summary']['validation_rate'] if val_file.exists() else None
        },
        'task_distribution': {k: {'total': v['total'], 'datasets': v['files']} 
                            for k, v in task_stats.items()},
        'datasets': dataset_stats
    }
    
    with open(input_dir / 'final_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print(f"\nFinal statistics saved to: {input_dir / 'final_statistics.json'}")


if __name__ == "__main__":
    generate_final_report()