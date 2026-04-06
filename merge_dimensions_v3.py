#!/usr/bin/env python3
"""
数据合并 v3：保留全部原始数据
从 converted_data_v3 的原始文件读取，按 sub_task 字段合并
"""

import json
import hashlib
from pathlib import Path
from collections import defaultdict

# 配置
INPUT_DIR = Path("D:/workspace/timeaware/converted_data_v3")
OUTPUT_DIR = Path("D:/workspace/timeaware/dataset_final_v2")

# 子维度到新维度的映射
SUBTASK_TO_NEW_DIM = {
    # T1 - Duration
    "T1-T1-Duration": ("T1", "Duration"),
    "T1-Convo-Duration": ("T1", "Duration"),
    "T1-DurationCompare": ("T1", "Duration"),
    "T1-TypicalTime": ("T1", "Duration"),
    "T1-Convo-CommonSense": ("T1", "Duration"),
    
    # T1 - Ordering
    "T1-T1-Ordering": ("T1", "Ordering"),
    "T1-Ordering-MC": ("T1", "Ordering"),
    "T1-T1-Sequence": ("T1", "Ordering"),
    "T1-T1-Causal": ("T1", "Ordering"),
    "T1-Convo-Ordering": ("T1", "Ordering"),
    
    # T1 - Counting
    "T1-TimeCalc-HistNoise": ("T1", "Counting"),
    "T1-TimeCalc-ConfusionNoise": ("T1", "Counting"),
    "T1-TimeCalc-NumNoise": ("T1", "Counting"),
    "T1-T1-MultiChoice": ("T1", "Counting"),
    "T1-T1-Addition": ("T1", "Counting"),
    "T1-T1-Parallel": ("T1", "Counting"),
    "T1-T1-Multihop": ("T1", "Counting"),
    "T1-T1-Distractor": ("T1", "Counting"),
    "T1-TypicalTime-HistNoise": ("T1", "Counting"),
    "T1-TypicalTime-ConfusionNoise": ("T1", "Counting"),
    "T1-TypicalTime-NumNoise": ("T1", "Counting"),
    
    # T1 - TimeBoundary
    "T1-T1-TimeBoundary": ("T1", "TimeBoundary"),
    
    # T2 - Location
    "T2-PositionTrack-Basic": ("T2", "Location"),
    "T2-PositionTrack-Timeline": ("T2", "Location"),
    "T2-PositionTrack-MC": ("T2", "Location"),
    "T2-PositionTrack-WithContext": ("T2", "Location"),
    
    # T2 - Status
    "T2-T2-StateTrack": ("T2", "Status"),
    "T2-T2-StateTrack-Easy": ("T2", "Status"),
    "T2-T2-StateTrack-Hard": ("T2", "Status"),
    "T2-T2-SocialState": ("T2", "Status"),
    "T2-T2-Progressive": ("T2", "Status"),
    "T2-T2-Tense": ("T2", "Status"),
    "T2-T2-Stationarity": ("T2", "Status"),
    
    # T2 - Consequence
    "T2-T2-Consequence": ("T2", "Consequence"),
    "T2-T2-Evidence": ("T2", "Consequence"),
    "T2-StateTransition": ("T2", "Consequence"),
    "T2-StateTransition-BeforeAfter": ("T2", "Consequence"),
    "T2-StateTransition-MC": ("T2", "Consequence"),
    "T2-StateTransition-WithContext": ("T2", "Consequence"),
    "T2-T2-Location": ("T2", "Consequence"),
    "T2-T2-Ordering": ("T2", "Consequence"),
    "T2-Convo-Sequence": ("T2", "Consequence"),
    
    # T3 - SpaceConflict
    "T3-T3-Conflict": ("T3", "SpaceConflict"),
    "T3-T3-TimeConflict": ("T3", "SpaceConflict"),
    "T3-T3-TimeOverlap": ("T3", "SpaceConflict"),
    "T3-Convo-Conflict": ("T3", "SpaceConflict"),
    
    # T3 - ResourceConflict
    "T3-T3-Resource": ("T3", "ResourceConflict"),
    "T3-T3-Concurrent": ("T3", "ResourceConflict"),
    "T3-Convo-Resource": ("T3", "ResourceConflict"),
    
    # T4 - NoiseRetrieval
    "T4-T4-Buried": ("T4", "NoiseRetrieval"),
    "T4-Buried-Info": ("T4", "NoiseRetrieval"),
    "T4-Buried-Time": ("T4", "NoiseRetrieval"),
    "T4-T4-Noise": ("T4", "NoiseRetrieval"),
    "T4-Noise-Retrieval": ("T4", "NoiseRetrieval"),
    "T4-Noisy-Retrieval": ("T4", "NoiseRetrieval"),
    "T4-T4-Distractor": ("T4", "NoiseRetrieval"),
    "T4-T4-Detail": ("T4", "NoiseRetrieval"),
    "T4-Section-Nav": ("T4", "NoiseRetrieval"),
    "T4-Convo-Dialog": ("T4", "NoiseRetrieval"),
    "T4-Convo-Recall": ("T4", "NoiseRetrieval"),
    "T4-Convo-Buried": ("T4", "NoiseRetrieval"),
    "T4-Convo-Noisy": ("T4", "NoiseRetrieval"),
    "T4-T4-Section": ("T4", "NoiseRetrieval"),
    
    # T4 - MultiHop
    "T4-Convo-Cross": ("T4", "MultiHop"),
    "T4-Multi-hop": ("T4", "MultiHop"),
    
    # T5 - RuleReversal
    "T5-T5-Counterfactual": ("T5", "RuleReversal"),
    "T5-T5-RulePerturbation": ("T5", "RuleReversal"),
    "T5-T5-RuleChange": ("T5", "RuleReversal"),
    "T5-T5-Confusion": ("T5", "RuleReversal"),
    "T5-T5-Emotion": ("T5", "RuleReversal"),
    "T5-T5-SocialReverse": ("T5", "RuleReversal"),
    "T5-T5-ProcessReverse": ("T5", "RuleReversal"),
    "T5-T5-Twist": ("T5", "RuleReversal"),
    "T5-T5-WrongToRight": ("T5", "RuleReversal"),
    "T5-T5-ChoiceInversion": ("T5", "RuleReversal"),
    "T5-Convo-RuleReverse": ("T5", "RuleReversal"),
    "T5-Convo-Reversal": ("T5", "RuleReversal"),
    "T5-Convo-Contrastive": ("T5", "RuleReversal"),
    "T5-ExplicitReverse": ("T5", "RuleReversal"),
}

def compute_hash(context: str, query: str) -> str:
    return hashlib.md5(f"{context}|{query}".encode('utf-8')).hexdigest()

def main():
    print("=" * 60)
    print("数据合并 v3（保留全部原始数据）")
    print("=" * 60)
    
    for task in ["T1", "T2", "T3", "T4", "T5"]:
        (OUTPUT_DIR / task).mkdir(parents=True, exist_ok=True)
    
    merged = defaultdict(lambda: defaultdict(list))
    seen_hashes = defaultdict(set)
    
    total_read = 0
    total_written = 0
    unmatched = defaultdict(int)
    
    jsonl_files = list(INPUT_DIR.glob("*.jsonl"))
    print(f"\n找到 {len(jsonl_files)} 个JSONL文件")
    
    for jsonl_file in jsonl_files:
        print(f"处理 {jsonl_file.name}...")
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    item = json.loads(line)
                    total_read += 1
                    
                    sub_task = item.get('sub_task', '')
                    
                    if sub_task in SUBTASK_TO_NEW_DIM:
                        new_task, new_subdim = SUBTASK_TO_NEW_DIM[sub_task]
                        
                        h = compute_hash(item.get('context', ''), item.get('query', ''))
                        if h not in seen_hashes[(new_task, new_subdim)]:
                            seen_hashes[(new_task, new_subdim)].add(h)
                            new_item = dict(item)
                            new_item['task'] = new_task
                            new_item['sub_task'] = f"{new_task}-{new_subdim}"
                            merged[new_task][new_subdim].append(new_item)
                            total_written += 1
                    else:
                        unmatched[sub_task] += 1
                        
                except json.JSONDecodeError:
                    continue
    
    print("\n保存合并数据...")
    for task in ["T1", "T2", "T3", "T4", "T5"]:
        for subdim in merged[task]:
            output_path = OUTPUT_DIR / task / f"{task}-{subdim}.jsonl"
            items = merged[task][subdim]
            with open(output_path, 'w', encoding='utf-8') as f:
                for item in items:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            print(f"  {task}-{subdim}: {len(items)} 条")
    
    print("\n" + "=" * 60)
    print("统计汇总")
    print("=" * 60)
    print(f"原始数据总数: {total_read:,}")
    print(f"合并后数据: {total_written:,}")
    if total_read > 0:
        print(f"压缩率: {100 * (1 - total_written / total_read):.1f}%")
    
    print("\n按维度统计:")
    for task in ["T1", "T2", "T3", "T4", "T5"]:
        if task in merged:
            task_total = sum(len(items) for items in merged[task].values())
            print(f"\n{task}: {task_total:,} 条")
            for subdim, items in merged[task].items():
                print(f"  {subdim}: {len(items):,} 条")
    
    print("\n未匹配的 sub_task (前20):")
    for sub_task, count in sorted(unmatched.items(), key=lambda x: -x[1])[:20]:
        if count > 0:
            print(f"  {sub_task}: {count}")
    
    report = {
        "total_read": total_read,
        "total_written": total_written,
        "statistics": {
            task: {subdim: len(items) for subdim, items in subdims.items()}
            for task, subdims in merged.items()
        },
        "unmatched_subtasks": dict(sorted(unmatched.items(), key=lambda x: -x[1])[:50])
    }
    
    with open(OUTPUT_DIR / "merge_report_v3.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n完成! 报告保存到: {OUTPUT_DIR / 'merge_report_v3.json'}")

if __name__ == '__main__':
    main()