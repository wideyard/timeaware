#!/usr/bin/env python3
"""
检查T4数据集的对话长度分布
目标: 对话总字数 > 1000字
"""

import json
import os
from pathlib import Path
from collections import defaultdict

# 配置
INPUT_DIR = Path("D:/workspace/timeaware/converted_data_v3_cleaned")
OUTPUT_DIR = Path("D:/workspace/timeaware/dataset_analysis")

TARGET_LENGTH = 1000  # 目标最小字数


def count_dialog_length(item):
    """计算对话总字数（包括context）"""
    total = 0
    
    # context字数
    total += len(item.get('context', ''))
    
    # conversation字数
    for turn in item.get('conversation', []):
        total += len(turn.get('content', ''))
    
    # query和answer字数
    total += len(item.get('query', ''))
    total += len(item.get('answer', ''))
    
    return total


def check_truncation(item):
    """检查是否有截断问题（以"..."结尾）"""
    issues = []
    
    # 检查context
    context = item.get('context', '')
    if context.endswith('...'):
        issues.append('context_truncated')
    
    # 检查conversation
    for i, turn in enumerate(item.get('conversation', [])):
        content = turn.get('content', '')
        if content.endswith('...'):
            issues.append(f'conversation[{i}]_truncated')
    
    # 检查answer
    answer = item.get('answer', '')
    if isinstance(answer, str) and answer.endswith('...'):
        issues.append('answer_truncated')
    
    return issues


def analyze_file(filepath):
    """分析单个JSONL文件"""
    items = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                length = count_dialog_length(item)
                truncation_issues = check_truncation(item)
                items.append({
                    'length': length,
                    'truncation': truncation_issues,
                    'source_id': item.get('source_id', '')
                })
            except json.JSONDecodeError:
                continue
    
    return items


def main():
    """主函数"""
    print("=" * 60)
    print("T4数据集对话长度分析")
    print("=" * 60)
    print(f"目标: 对话总字数 > {TARGET_LENGTH}")
    print()
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 找到所有T4文件
    t4_dir = INPUT_DIR / "T4"
    t4_files = sorted(t4_dir.glob("*.jsonl"))
    
    print(f"找到 {len(t4_files)} 个T4子维度文件\n")
    
    # 分析每个文件
    results = {}
    
    for filepath in t4_files:
        filename = filepath.name
        items = analyze_file(filepath)
        
        if not items:
            continue
        
        lengths = [item['length'] for item in items]
        truncated = [item for item in items if item['truncation']]
        meeting_target = [item for item in items if item['length'] >= TARGET_LENGTH]
        
        results[filename] = {
            'total_items': len(items),
            'items_meeting_target': len(meeting_target),
            'items_below_target': len(items) - len(meeting_target),
            'truncated_items': len(truncated),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'avg_length': sum(lengths) / len(lengths),
            'median_length': sorted(lengths)[len(lengths) // 2],
            'truncation_examples': [
                {
                    'source_id': item['source_id'],
                    'issues': item['truncation'][:3]  # 只显示前3个问题
                }
                for item in truncated[:5]  # 只显示前5个
            ]
        }
        
        # 打印结果
        status = "[OK]" if results[filename]['items_meeting_target'] == len(items) else "[X]"
        trunc_status = f" (WARNING: {results[filename]['truncated_items']} truncated)" if results[filename]['truncated_items'] > 0 else ""
        
        print(f"{status} {filename}")
        print(f"    数量: {results[filename]['total_items']}")
        print(f"    符合标准: {results[filename]['items_meeting_target']}/{results[filename]['total_items']}")
        print(f"    平均长度: {results[filename]['avg_length']:.0f} 字")
        print(f"    范围: {results[filename]['min_length']} - {results[filename]['max_length']} 字")
        if trunc_status:
            print(f"    {trunc_status}")
        print()
    
    # 保存详细报告
    report_path = OUTPUT_DIR / "t4_length_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print("汇总")
    print("=" * 60)
    
    total_items = sum(r['total_items'] for r in results.values())
    total_meeting_target = sum(r['items_meeting_target'] for r in results.values())
    total_truncated = sum(r['truncated_items'] for r in results.values())
    
    print(f"总数据量: {total_items}")
    print(f"符合标准 (>1000字): {total_meeting_target} ({100*total_meeting_target/total_items:.1f}%)")
    print(f"有截断问题: {total_truncated}")
    print(f"\n详细报告已保存到: {report_path}")
    
    # 识别需要扩展的数据集
    print("\n" + "=" * 60)
    print("需要扩展的数据集（平均长度 < 1000字）")
    print("=" * 60)
    
    need_expansion = [
        (filename, r) 
        for filename, r in results.items() 
        if r['avg_length'] < TARGET_LENGTH
    ]
    need_expansion.sort(key=lambda x: x[1]['avg_length'])
    
    for filename, r in need_expansion:
        print(f"  {filename}: 平均 {r['avg_length']:.0f} 字, 需要 +{TARGET_LENGTH - int(r['avg_length'])} 字")


if __name__ == '__main__':
    main()