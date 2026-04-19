#!/usr/bin/env python3
import json

datasets_to_check = [
    ('d:\\workspace\\timeaware\\data-converted\\TempReason\\sample_T5\\TEMPREASON_single.jsonl', 'TEMPREASON'),
    ('d:\\workspace\\timeaware\\data-converted\\tracie\\sample_T3\\TRACIE_single.jsonl', 'TRACIE'),
    ('d:\\workspace\\timeaware\\data-converted\\TimeDial\\sample_T1\\TIMEDIAL_single.jsonl', 'TIMEDIAL'),
]

for filepath, dataset_name in datasets_to_check:
    try:
        with open(filepath) as f:
            data = json.loads(f.readline())
            print(f"\n=== {dataset_name} SAMPLE ===")
            print(f"Task Type: {data.get('task_type')}")
            print(f"Rule Applied: {data['metadata'].get('rule_applied')}")
            print(f"Original Label: {data['metadata'].get('original_label')}")
            print(f"Computed Answer: {data['metadata'].get('computed_answer')}")
            print(f"Messages: {len(data.get('messages', []))} turns")
            if data.get('messages'):
                print(f"First message (user): {data['messages'][0].get('content', '')[:80]}...")
    except Exception as e:
        print(f"\nError reading {dataset_name}: {str(e)}")
