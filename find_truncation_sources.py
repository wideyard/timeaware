#!/usr/bin/env python3
"""
修复截断数据并检查来源

这个脚本会：
1. 找到所有有截断问题的数据集
2. 定位原始数据来源
3. 检查原始数据是否完整
4. 如果完整，重新提取；如果不完整，标记删除
"""

import json
import os
from pathlib import Path
from collections import defaultdict

# 配置
CLEANED_DIR = Path("D:/workspace/timeaware/converted_data_v3_cleaned")
ORIGINAL_DATA_DIR = Path("D:/workspace/timeaware/data")
TRANS_DIR = Path("D:/workspace/timeaware/trans")

# 需要检查的文件
TRUNCATION_ISSUES = {
    "T2-T2-Tense": "cosmosqa_conversational.jsonl",
    "T2-T2-Progressive": "choice75_conversational.jsonl",
    "T3-T3-Concurrent": "uds_t_dev_conversational.jsonl",
    "T4-T4-Distractor": "longbench_conversational.jsonl",
    "T4-Convo-Cross": "narrativeqa_conversational.jsonl",
    "T4-Convo-Dialog": "cosmosqa_conversational.jsonl",
    "T4-Convo-Recall": "qasper_conversational.jsonl",
    "T4-Buried-Time": "timeqa_train_hard_conversational.jsonl",
    "T4-T4-Detail": "narrativeqa_conversational.jsonl",
    "T4-T4-Buried": "narrativeqa_conversational.jsonl",
    "T4-T4-Noise": "qasper_conversational.jsonl",
    "T5-T5-Emotion": "cosmosqa_conversational.jsonl",
    "T5-T5-ChoiceInversion": "piqa_conversational.jsonl",
}


def check_truncation_in_file(filepath):
    """检查文件中的截断问题"""
    issues = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                
                # 检查context
                context = item.get('context', '')
                if context.endswith('...'):
                    issues.append({
                        'line': line_num,
                        'field': 'context',
                        'source_id': item.get('source_id', ''),
                        'truncated_text': context[-100:] if len(context) > 100 else context
                    })
                
                # 检查conversation
                for i, turn in enumerate(item.get('conversation', [])):
                    content = turn.get('content', '')
                    if content.endswith('...'):
                        issues.append({
                            'line': line_num,
                            'field': f'conversation[{i}]',
                            'source_id': item.get('source_id', ''),
                            'truncated_text': content[-100:] if len(content) > 100 else content
                        })
                
                # 检查answer
                answer = item.get('answer', '')
                if isinstance(answer, str) and answer.endswith('...'):
                    issues.append({
                        'line': line_num,
                        'field': 'answer',
                        'source_id': item.get('source_id', ''),
                        'truncated_text': answer[-100:] if len(answer) > 100 else answer
                    })
                    
            except json.JSONDecodeError:
                continue
    
    return issues


def find_source_converter(target_file):
    """找到生成目标文件的转换器"""
    converter_map = {
        "cosmosqa_conversational.jsonl": "cosmosqa_conversational_converter.py",
        "choice75_conversational.jsonl": "choice75_conversational_converter.py",
        "narrativeqa_conversational.jsonl": "narrativeqa_conversational_converter.py",
        "longbench_conversational.jsonl": "longbench_conversational_converter.py",
        "qasper_conversational.jsonl": "qasper_conversational_converter.py",
        "timeqa_train_hard_conversational.jsonl": "timeqa_conversational_converter.py",
        "piqa_conversational.jsonl": "piqa_conversational_converter.py",
        "propara_conversational.jsonl": "propara_conversational_converter.py",
    }
    
    for pattern, converter in converter_map.items():
        if pattern in target_file:
            return converter
    return None


def main():
    """主函数"""
    print("=" * 60)
    print("截断数据来源分析")
    print("=" * 60)
    
    results = {}
    
    for subdim, source_file in TRUNCATION_ISSUES.items():
        # 确定任务类型
        task = subdim.split('-')[0]
        filepath = CLEANED_DIR / task / f"{subdim}.jsonl"
        
        if not filepath.exists():
            print(f"[X] {subdim}: 文件不存在")
            continue
        
        # 检查截断
        issues = check_truncation_in_file(filepath)
        
        if not issues:
            print(f"[OK] {subdim}: 无截断问题")
            continue
        
        # 找到转换器
        converter = find_source_converter(source_file)
        
        # 找到原始数据
        original_patterns = {
            "cosmosqa": "data/CosmosQA/data",
            "narrativeqa": "data/narrativeqa",
            "longbench": "data/LongBench/data",
            "qasper": "data/qasper",
            "timeqa": "data/TimeQA",
            "piqa": "data/PIQA",
        }
        
        original_dir = None
        for pattern, dir_path in original_patterns.items():
            if pattern in source_file.lower():
                original_dir = Path(dir_path)
                break
        
        results[subdim] = {
            'total_items': sum(1 for _ in open(filepath, 'r', encoding='utf-8') if _.strip()),
            'truncated_items': len(issues),
            'source_file': source_file,
            'converter': converter,
            'original_dir': str(original_dir) if original_dir else 'Unknown',
            'sample_issues': issues[:3]  # 只显示前3个
        }
        
        print(f"\n[!] {subdim}")
        print(f"    文件: {filepath.name}")
        print(f"    总条数: {results[subdim]['total_items']}")
        print(f"    截断条数: {results[subdim]['truncated_items']}")
        print(f"    来源: {source_file}")
        print(f"    转换器: {converter}")
        print(f"    原始数据: {results[subdim]['original_dir']}")
        if issues:
            print(f"    示例截断:")
            for issue in issues[:2]:
                print(f"      - {issue['field']}: ...{issue['truncated_text'][-50:]}")
    
    # 保存报告
    output_file = Path("D:/workspace/timeaware/dataset_analysis/truncation_report.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"报告已保存到: {output_file}")
    
    # 输出修复建议
    print(f"\n{'='*60}")
    print("修复建议:")
    print(f"{'='*60}")
    
    for subdim, info in results.items():
        if info['truncated_items'] > 0:
            print(f"\n{subdim}:")
            print(f"  1. 找到 {info['converter']}")
            print(f"  2. 原始数据位于 {info['original_dir']}")
            print(f"  3. 检查转换器中的截断逻辑")
            print(f"  4. 修改截断限制或从原始数据重新提取")


if __name__ == '__main__':
    main()