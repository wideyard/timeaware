"""Generate _report.json files for jsonl files that are missing them."""
import json
import os
from collections import Counter

DATA_DIR = r"D:\workspace\timeaware\converted_data_v3"

# Find all jsonl files
jsonl_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.jsonl')])

# Find all existing report files
report_files = set(f for f in os.listdir(DATA_DIR) if f.endswith('_report.json'))

# Identify missing reports
missing = []
for jf in jsonl_files:
    base = jf.replace('.jsonl', '')
    report_name = f"{base}_report.json"
    if report_name not in report_files:
        missing.append(jf)

print(f"Total jsonl files: {len(jsonl_files)}")
print(f"Existing reports: {len(report_files)}")
print(f"Missing reports: {len(missing)}")
print("\nMissing files:")
for f in missing:
    print(f"  - {f}")

# Generate reports for missing files
for jf in missing:
    filepath = os.path.join(DATA_DIR, jf)
    print(f"\nProcessing {jf}...")
    
    task_counter = Counter()
    subtask_counter = Counter()
    difficulty_counter = Counter()
    total = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                total += 1
                task = data.get('task', 'unknown')
                subtask = data.get('sub_task', 'unknown')
                difficulty = data.get('difficulty', 'unknown')
                
                task_counter[task] += 1
                subtask_counter[subtask] += 1
                difficulty_counter[difficulty] += 1
            except json.JSONDecodeError:
                continue
    
    report = {
        "source": jf.replace('_conversational.jsonl', '').replace('_', ' ').title(),
        "total_samples": total,
        "task_distribution": dict(sorted(task_counter.items())),
        "subtask_distribution": dict(sorted(subtask_counter.items())),
        "difficulty_distribution": dict(sorted(difficulty_counter.items()))
    }
    
    report_path = os.path.join(DATA_DIR, jf.replace('.jsonl', '_report.json'))
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"  Total: {total}")
    print(f"  Tasks: {dict(task_counter)}")
    print(f"  Subtasks: {dict(subtask_counter)}")
    print(f"  Saved to: {report_path}")

print("\n\nDone! All missing reports generated.")
