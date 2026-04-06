#!/usr/bin/env python3
"""
重新执行数据合并：保留全部原始数据
流程：去重 → 合并维度 → 跨维度去重 → 输出
"""

import json
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

# 配置
INPUT_DIR = Path("D:/workspace/timeaware/converted_data_v3")  # 原始数据（不是cleaned）
OUTPUT_DIR = Path("D:/workspace/timeaware/dataset_final_v2")

# 维度映射（同之前）
DIMENSION_MAPPING = {
    "T1": {
        "Duration": ["T1-T1-Duration", "T1-TypicalTime", "T1-Convo-CommonSense", "T1-DurationCompare", "T1-Convo-Duration"],
        "Ordering": ["T1-T1-Ordering", "T1-T1-Sequence", "T1-T1-Causal", "T1-Ordering-MC", "T1-T1-Ordering-MC"],
        "Counting": ["T1-TimeCalc-HistNoise", "T1-TimeCalc-ConfusionNoise", "T1-TimeCalc-NumNoise", "T1-T1-MultiChoice", "T1-T1-Addition", "T1-T1-Parallel", "T1-T1-Multihop", "T1-T1-Distractor", "T1-TimeCalc", "T1-TypicalTime", "T1-T1-Addition", "T1-Convo-Addition"],
        "TimeBoundary": ["T1-T1-TimeBoundary"]
    },
    "T2": {
        "Location": ["T2-PositionTrack-Basic", "T2-PositionTrack-Timeline", "T2-PositionTrack-MC", "T2-PositionTrack-WithContext"],
        "Status": ["T2-T2-StateTrack", "T2-T2-SocialState", "T2-T2-Progressive", "T2-T2-Tense", "T2-T2-Stationarity", "T2-T2-StateTrack-Easy", "T2-T2-StateTrack-Hard", "T2-Timeline", "T2-T2-Timeline"],
        "Consequence": ["T2-T2-Consequence", "T2-T2-Evidence", "T2-StateTransition", "T2-StateTransition-BeforeAfter", "T2-StateTransition-MC", "T2-StateTransition-WithContext", "T2-T2-Location", "T2-T2-Ordering", "T2-Convo-Sequence"]
    },
    "T3": {
        "SpaceConflict": ["T3-T3-Conflict", "T3-T3-TimeConflict", "T3-T3-TimeOverlap", "T3-Convo-Conflict"],
        "ResourceConflict": ["T3-T3-Resource", "T3-T3-Concurrent", "T3-Convo-Resource"]
    },
    "T4": {
        "NoiseRetrieval": ["T4-T4-Buried", "T4-Buried-Info", "T4-Buried-Time", "T4-T4-Noise", "T4-Noise-Retrieval", "T4-Noisy-Retrieval", "T4-T4-Distractor", "T4-T4-Detail", "T4-Section-Nav", "T4-Convo-Dialog", "T4-Convo-Recall", "T4-Convo-Buried", "T4-Convo-Noisy", "T4-T4-Section", "T4-T4-Distractor"],
        "MultiHop": ["T4-Convo-Cross", "T4-Multi-hop"]
    },
    "T5": {
        "RuleReversal": ["T5-T5-Counterfactual", "T5-T5-RulePerturbation", "T5-T5-RuleChange", "T5-T5-Confusion", "T5-T5-Emotion", "T5-T5-SocialReverse", "T5-T5-ProcessReverse", "T5-T5-Twist", "T5-T5-WrongToRight", "T5-T5-ChoiceInversion", "T5-Convo-RuleReverse", "T5-Convo-Reversal", "T5-Convo-Contrastive", "T5-ExplicitReverse"]
    }
}

def compute_hash(context: str, query: str) -> str:
    """计算去重哈希"""
    return hashlib.md5(f"{context}|{query}".encode('utf-8')).hexdigest()

def load_all_jsonl_files(input_dir: Path) -> Dict[str, List[Dict]]:
    """加载所有JSONL文件"""
    print("加载所有原始数据...")
    file_data = {}
    
    for task in ["T1", "T2", "T3", "T4", "T5"]:
        task_dir = input_dir / task
        if not task_dir.exists():
            continue
        
        for jsonl_file in task_dir.glob("*.jsonl"):
            items = []
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            items.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            file_name = jsonl_file.stem
            file_data[file_name] = items
            print(f"  {file_name}: {len(items)} 条")
    
    print(f"\n加载完成，共 {len(file_data)} 个文件")
    return file_data

def merge_dimensions_v2(file_data: Dict[str, List[Dict]]) -> Dict[str, Dict[str, List[Dict]]]:
    """合并维度（保留全部数据）"""
    print("\n合并维度...")
    
    merged = defaultdict(lambda: defaultdict(list))
    stats = defaultdict(lambda: defaultdict(int))
    
    for task, subdimensions in DIMENSION_MAPPING.items():
        for new_subdim, old_subdims in subdimensions.items():
            seen_hashes = set()
            
            for old_subdim in old_subdims:
                # 查找匹配的文件
                matching_items = []
                for file_name, items in file_data.items():
                    # 检查文件名是否匹配
                    if old_subdim in file_name or file_name == old_subdim:
                        matching_items.extend(items)
                
                if not matching_items:
                    # 尝试其他命名格式
                    for file_name, items in file_data.items():
                        if task in file_name:
                            # 检查sub_task字段
                            for item in items:
                                if item.get('sub_task', '').startswith(old_subdim):
                                    matching_items.append(item)
                
                for item in matching_items:
                    h = compute_hash(item.get('context', ''), item.get('query', ''))
                    if h not in seen_hashes:
                        seen_hashes.add(h)
                        new_item = dict(item)
                        new_item['task'] = task
                        new_item['sub_task'] = f"{task}-{new_subdim}"
                        merged[task][new_subdim].append(new_item)
                
                stats[task][new_subdim] = len(merged[task][new_subdim])
            
            print(f"  {task}-{new_subdim}: {stats[task][new_subdim]} 条")
    
    return dict(merged), dict(stats)

def save_merged_data(merged: Dict, output_dir: Path):
    """保存合并后的数据"""
    print("\n保存合并数据...")
    
    for task, subdims in merged.items():
        task_dir = output_dir / task
        task_dir.mkdir(parents=True, exist_ok=True)
        
        for subdim, items in subdims.items():
            output_path = task_dir / f"{task}-{subdim}.jsonl"
            with open(output_path, 'w', encoding='utf-8') as f:
                for item in items:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            print(f"  {output_path.name}: {len(items)} 条")

def generate_report(stats: Dict, original_count: int, output_dir: Path):
    """生成报告"""
    report = {
        "original_total": original_count,
        "final_total": sum(sum(s.values()) for s in stats.values()),
        "statistics": stats,
        "dimension_mapping": DIMENSION_MAPPING
    }
    
    with open(output_dir / "merge_report_v2.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("汇总")
    print("=" * 60)
    
    total = 0
    for task in ["T1", "T2", "T3", "T4", "T5"]:
        if task in stats:
            task_total = sum(stats[task].values())
            total += task_total
            print(f"\n{task}: {task_total} 条")
            for subdim, count in stats[task].items():
                print(f"  {subdim}: {count}")
    
    print(f"\n总计: {total} 条")
    print(f"压缩率: {100 * (1 - total / original_count):.1f}%")

def main():
    """主函数"""
    print("=" * 60)
    print("数据合并 v2（保留全部原始数据）")
    print("=" * 60)
    
    # 加载所有文件
    INPUT_DIR = Path("D:/workspace/timeaware/converted_data_v3")
    file_data = load_all_jsonl_files(INPUT_DIR)
    
    # 计算原始总数
    original_count = sum(len(items) for items in file_data.values())
    print(f"\n原始数据总数: {original_count}")
    
    # 合并维度
    merged, stats = merge_dimensions_v2(file_data)
    
    # 保存
    OUTPUT_DIR = Path("D:/workspace/timeaware/dataset_final_v2")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_merged_data(merged, OUTPUT_DIR)
    
    # 生成报告
    generate_report(stats, original_count, OUTPUT_DIR)
    
    print("\n完成!")

if __name__ == '__main__':
    main()