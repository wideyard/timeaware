#!/usr/bin/env python3
"""
维度合并脚本
按照最终映射方案合并数据集
"""

import json
import os
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

# 配置
INPUT_DIR = Path("D:/workspace/timeaware/converted_data_v3_cleaned")
OUTPUT_DIR = Path("D:/workspace/timeaware/dataset_final")

# 维度映射
DIMENSION_MAPPING = {
    "T1": {
        "Duration": [
            "T1-T1-Duration",
            "T1-TypicalTime", 
            "T1-Convo-CommonSense",
            "T1-DurationCompare"
        ],
        "Ordering": [
            "T1-T1-Ordering",
            "T1-T1-Sequence",
            "T1-T1-Causal"
        ],
        "Counting": [
            "T1-TimeCalc-HistNoise",
            "T1-TimeCalc-ConfusionNoise",
            "T1-TimeCalc-NumNoise",
            "T1-T1-MultiChoice",
            "T1-T1-Addition",
            "T1-T1-Parallel",
            "T1-T1-Multihop",
            "T1-T1-Distractor"
        ],
        "TimeBoundary": [
            "T1-T1-TimeBoundary"
        ]
    },
    "T2": {
        "Location": [
            "T2-PositionTrack-Basic",
            "T2-PositionTrack-Timeline",
            "T2-PositionTrack-MC",
            "T2-PositionTrack-WithContext"
        ],
        "Status": [
            "T2-T2-StateTrack",
            "T2-T2-SocialState",
            "T2-T2-Progressive",
            "T2-T2-Tense",
            "T2-T2-Stationarity"
        ],
        "Consequence": [
            "T2-T2-Consequence",
            "T2-T2-Evidence",
            "T2-StateTransition",
            "T2-StateTransition-BeforeAfter",
            "T2-StateTransition-MC",
            "T2-StateTransition-WithContext",
            "T2-T2-Location",  # 重命名，实际是因果推理
            "T2-T2-Ordering"
        ]
    },
    "T3": {
        "SpaceConflict": [
            "T3-T3-Conflict",
            "T3-T3-TimeConflict",
            "T3-T3-TimeOverlap"
        ],
        "ResourceConflict": [
            "T3-T3-Resource",
            "T3-T3-Concurrent"
        ]
    },
    "T4": {
        "NoiseRetrieval": [
            "T4-T4-Buried",
            "T4-Buried-Info",
            "T4-Buried-Time",
            "T4-T4-Noise",
            "T4-Noise-Retrieval",
            "T4-Noisy-Retrieval",
            "T4-T4-Distractor",
            "T4-T4-Detail",
            "T4-Section-Nav",
            "T4-Convo-Dialog",
            "T4-Convo-Recall"
        ],
        "MultiHop": [
            "T4-Convo-Cross",
            "T4-Multi-hop"  # 新创建
        ]
    },
    "T5": {
        "RuleReversal": [
            "T5-T5-Counterfactual",
            "T5-T5-RulePerturbation",
            "T5-T5-RuleChange",
            "T5-T5-Confusion",
            "T5-T5-Emotion",
            "T5-T5-SocialReverse",
            "T5-T5-ProcessReverse",
            "T5-T5-Twist",
            "T5-T5-WrongToRight",
            "T5-T5-ChoiceInversion"
        ]
    }
}

# 要删除的子维度
DELETE_DIMENSIONS = [
    "T2-T2-Branch",
    "T2-T2-Rollback",
    "T2-T2-Commonsense",
    "T3-Convo-Location",
    "T3-Duration-Conflict"
]

def compute_hash(context: str, query: str) -> str:
    """计算去重哈希"""
    return hashlib.md5(f"{context}|{query}".encode('utf-8')).hexdigest()

def load_jsonl(filepath: Path) -> List[Dict]:
    """加载JSONL文件"""
    items = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items

def save_jsonl(items: List[Dict], filepath: Path):
    """保存JSONL文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def merge_dimensions():
    """合并维度"""
    print("=" * 60)
    print("维度合并")
    print("=" * 60)
    
    # 创建输出目录
    for task in ["T1", "T2", "T3", "T4", "T5"]:
        (OUTPUT_DIR / task).mkdir(parents=True, exist_ok=True)
    
    # 统计
    stats = defaultdict(lambda: defaultdict(int))
    total_items = defaultdict(int)
    
    # 处理每个维度
    for task, subdimensions in DIMENSION_MAPPING.items():
        print(f"\n处理 {task}:")
        
        for new_subdim, old_subdims in subdimensions.items():
            merged_items = []
            seen_hashes = set()
            
            print(f"  {new_subdim}:")
            
            for old_subdim in old_subdims:
                # 尝试不同命名格式
                possible_names = [
                    old_subdim,
                    f"{old_subdim}",
                    old_subdim.replace("-", "-T")
                ]
                
                filepath = None
                for name in possible_names:
                    candidate = INPUT_DIR / task / f"{name}.jsonl"
                    if candidate.exists():
                        filepath = candidate
                        break
                
                # 如果没有找到，检查是否有其他变体
                if not filepath:
                    # 搜索匹配的文件
                    for f in (INPUT_DIR / task).glob("*.jsonl"):
                        if old_subdim in f.name or f.stem == old_subdim:
                            filepath = f
                            break
                
                if filepath and filepath.exists():
                    items = load_jsonl(filepath)
                    original_count = len(items)
                    added_count = 0
                    
                    for item in items:
                        # 去重
                        h = compute_hash(item.get('context', ''), item.get('query', ''))
                        if h not in seen_hashes:
                            seen_hashes.add(h)
                            # 更新任务和子任务标签
                            item['task'] = task
                            item['sub_task'] = f"{task}-{new_subdim}"
                            merged_items.append(item)
                            added_count += 1
                    
                    print(f"    {old_subdim}: {original_count} -> {added_count} (去重后)")
                    stats[task][new_subdim] += added_count
                else:
                    print(f"    {old_subdim}: [跳过] 文件不存在")
            
            # 保存合并后的文件
            if merged_items:
                output_path = OUTPUT_DIR / task / f"{task}-{new_subdim}.jsonl"
                save_jsonl(merged_items, output_path)
                total_items[task] += len(merged_items)
                print(f"    -> 总计: {len(merged_items)} 条保存到 {output_path.name}")
    
    # 保存统计报告
    report = {
        "dimension_mapping": DIMENSION_MAPPING,
        "deleted_dimensions": DELETE_DIMENSIONS,
        "statistics": {task: dict(subdims) for task, subdims in stats.items()},
        "total_per_task": dict(total_items)
    }
    
    with open(OUTPUT_DIR / "merge_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 打印汇总
    print("\n" + "=" * 60)
    print("汇总")
    print("=" * 60)
    for task in ["T1", "T2", "T3", "T4", "T5"]:
        print(f"\n{task}: {total_items[task]} 条")
        for subdim, count in stats[task].items():
            print(f"  {subdim}: {count}")
    
    print(f"\n总计: {sum(total_items.values())} 条")
    print(f"\n报告已保存到: {OUTPUT_DIR / 'merge_report.json'}")

if __name__ == '__main__':
    merge_dimensions()