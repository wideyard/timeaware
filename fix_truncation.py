#!/usr/bin/env python3
"""
批量修复转换器中的截断问题
将 [:200], [:300], [:500] 替换为完整文本或 [:2000]
"""

import os
from pathlib import Path

TRANS_DIR = Path("D:/workspace/timeaware/trans")

# 需要修复的文件和模式
FIXES = {
    "cosmosqa_conversational_converter.py": [
        ("context[:500]", "context"),
        ("context_first_person[:200]", "context_first_person"),
    ],
    "drop_conversational_converter.py": [
        ("passage[:500]", "passage"),
    ],
    "hellaswag_conversational_converter.py": [
        ("context[:300]", "context"),
    ],
    "longbench_conversational_converter.py": [
        ("key_para[:200]", "key_para"),
        ("key_para[:300]", "key_para"),
    ],
    "narrativeqa_conversational_converter.py": [
        ("relevant[0][:200]", "relevant[0]"),
        ("s.strip()[:200]", "s.strip()"),
    ],
    "tracie_conversational_converter.py": [
        ("story[:500]", "story"),
    ],
    "udst_durationqa_conversational_converter.py": [
        ("sentence[:500]", "sentence"),
    ],
}

# PIQA 截断修复 (line 628)
PIQA_FIXES = {
    "piqa_conversational_converter.py": [
        ("{sol1[:30]}, B: {sol2[:30]}", "{sol1}, B: {sol2}"),  # Increase from 30 to full
    ]
}

def fix_file(filepath, replacements):
    """修复文件中的截断"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = 0
    
    for old, new in replacements:
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            changes += count
            print(f"  - Replaced '{old[:50]}...' ({count} occurrences)")
    
    if changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] Saved {changes} changes")
    else:
        print(f"  [SKIP] No matches found")
    
    return changes

def main():
    """主函数"""
    print("=" * 60)
    print("修复转换器截断问题")
    print("=" * 60)
    
    total_changes = 0
    
    for filename, replacements in FIXES.items():
        filepath = TRANS_DIR / filename
        print(f"\n{filename}:")
        if not filepath.exists():
            print(f"  [ERROR] File not found")
            continue
        changes = fix_file(filepath, replacements)
        total_changes += changes
    
    # PIQA特殊处理
    print(f"\npiqa_conversational_converter.py:")
    filepath = TRANS_DIR / "piqa_conversational_converter.py"
    if filepath.exists():
        changes = fix_file(filepath, PIQA_FIXES.get("piqa_conversational_converter.py", []))
        total_changes += changes
    
    print("\n" + "=" * 60)
    print(f"完成! 共修改 {total_changes} 处截断")
    print("=" * 60)

if __name__ == "__main__":
    main()