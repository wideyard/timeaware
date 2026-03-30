#!/usr/bin/env python3
"""Validate all reformatted datasets"""
import json
from pathlib import Path
from typing import Dict, List

def validate_all_datasets():
    """Validate all datasets in converted_data_v2"""
    input_dir = Path("converted_data_v2")
    results = {}
    total_count = 0
    valid_count = 0
    
    required_fields = ['id', 'task', 'sub_task', 'context', 'query', 'answer', 'ground_truth']
    
    for file_path in sorted(input_dir.glob('*.jsonl')):
        file_count = 0
        file_valid = 0
        file_errors = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f, 1):
                file_count += 1
                try:
                    data = json.loads(line.strip())
                    
                    # Check required fields
                    has_all = all(field in data and data[field] for field in required_fields)
                    
                    # Check ground_truth is not empty
                    has_gt = isinstance(data.get('ground_truth'), dict) and len(data['ground_truth']) > 0
                    
                    # Check answer is not empty
                    has_answer = bool(data.get('answer', ''))
                    
                    if has_all and has_gt and has_answer:
                        file_valid += 1
                    else:
                        if not has_all:
                            missing = [f for f in required_fields if not data.get(f)]
                            file_errors.append(f'Line {idx}: missing fields {missing}')
                        if not has_gt:
                            file_errors.append(f'Line {idx}: empty ground_truth')
                        if not has_answer:
                            file_errors.append(f'Line {idx}: empty answer')
                except Exception as e:
                    file_errors.append(f'Line {idx}: {str(e)}')
        
        rate = file_valid / file_count * 100 if file_count > 0 else 0
        results[file_path.stem] = {
            'total': file_count,
            'valid': file_valid,
            'rate': rate,
            'errors': file_errors[:5]  # First 5 errors only
        }
        total_count += file_count
        valid_count += file_valid
        
        status = "[OK]" if rate == 100 else "[FAIL]"
        print(f'{status} {file_path.stem}: {file_valid}/{file_count} ({rate:.1f}%)')
        
        if file_errors:
            print(f'  Sample errors:')
            for err in file_errors[:3]:
                print(f'    - {err}')
    
    print()
    print('=' * 60)
    print('VALIDATION SUMMARY')
    print('=' * 60)
    print(f'Total samples: {total_count}')
    print(f'Valid samples: {valid_count}')
    print(f'Overall rate: {valid_count/total_count*100:.1f}%')
    
    # Calculate per-task statistics
    task_stats = {}
    for name, stats in results.items():
        # Infer task from filename
        if 'timeqa' in name or 'drop' in name or 'mctaco' in name:
            task = 'T1_temporal'
        elif 'openpi' in name or 'pasta' in name or 'propara' in name or 'situated' in name:
            task = 'T2_state'
        elif 't3' in name or 'trip' in name or 'atomic' in name:
            task = 'T3_concurrency'
        elif 'longbench' in name or 'narrative' in name:
            task = 'T4_memory'
        elif 't5' in name or 'counterfactual' in name or 'dialogue' in name:
            task = 'T5_counterfactual'
        else:
            task = 'T1_temporal'  # Default
        
        if task not in task_stats:
            task_stats[task] = {'total': 0, 'valid': 0}
        task_stats[task]['total'] += stats['total']
        task_stats[task]['valid'] += stats['valid']
    
    print()
    print('Per-Task Statistics:')
    for task, stats in sorted(task_stats.items()):
        rate = stats['valid'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f'  {task}: {stats["valid"]}/{stats["total"]} ({rate:.1f}%)')
    
    # Save results
    output = {
        'summary': {
            'total_samples': total_count,
            'valid_samples': valid_count,
            'validation_rate': valid_count/total_count*100
        },
        'by_task': task_stats,
        'by_dataset': {k: {'total': v['total'], 'valid': v['valid'], 'rate': v['rate']} 
                       for k, v in results.items()}
    }
    
    with open(input_dir / 'validation_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print()
    print(f'Results saved to: {input_dir / "validation_results.json"}')
    
    return results


if __name__ == "__main__":
    validate_all_datasets()