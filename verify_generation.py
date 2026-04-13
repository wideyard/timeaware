#!/usr/bin/env python3
import os

datasets = {
    'MCTACO_full_T5': 'd:\\workspace\\timeaware\\data-converted\\MCTACO\\full_T5',
    'UDST_full_T5': 'd:\\workspace\\timeaware\\data-converted\\UDST-DurationQA\\full_T5',
    'TempReason_sample_T5': 'd:\\workspace\\timeaware\\data-converted\\TempReason\\sample_T5',
    'tracie_sample_T5': 'd:\\workspace\\timeaware\\data-converted\\tracie\\sample_T5',
    'TimeDial_sample_T5': 'd:\\workspace\\timeaware\\data-converted\\TimeDial\\sample_T5',
    'TRIP_sample_T5': 'd:\\workspace\\timeaware\\data-converted\\TRIP\\sample_T5',
}

print("=" * 70)
print("FINAL GENERATION REPORT")
print("=" * 70)

total_samples = 0
for dataset_name, path in datasets.items():
    if os.path.exists(path):
        files = [f for f in os.listdir(path) if f.endswith('.jsonl')]
        if files:
            total_lines = 0
            for f in files:
                with open(os.path.join(path, f)) as fp:
                    lines = sum(1 for _ in fp)
                    total_lines += lines
            total_samples += total_lines
            print(f"\n{dataset_name}:")
            print(f"  Files: {len(files)}")
            print(f"  Total samples: {total_lines}")
            for f in sorted(files):
                with open(os.path.join(path, f)) as fp:
                    lines = sum(1 for _ in fp)
                print(f"    - {f}: {lines} samples")
    else:
        print(f"\n{dataset_name}: [NOT FOUND]")

print("\n" + "=" * 70)
print(f"GRAND TOTAL: {total_samples} samples generated")
print("=" * 70)
