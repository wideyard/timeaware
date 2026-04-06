#!/usr/bin/env python3
"""
构造T4 Multi-hop数据集
从T1-Multihop扩展成长对话格式（>1000字）
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Any

# 配置
INPUT_FILE = Path("D:/workspace/timeaware/converted_data_v3_cleaned/T1/T1-T1-Multihop.jsonl")
OUTPUT_FILE = Path("D:/workspace/timeaware/converted_data_v3_cleaned/T4/T4-Multi-hop.jsonl")
TARGET_COUNT = 500
MIN_LENGTH = 1000  # 最小字数

# 噪声对话模板（用于扩展长度）
NOISE_TEMPLATES = [
    ("user", "By the way, did you hear about the new restaurant downtown?"),
    ("assistant", "No, I haven't. What's special about it?"),
    ("user", "They say the food is amazing. I'm thinking of trying it this weekend."),
    ("assistant", "That sounds interesting. Let me know how it goes."),
    ("user", "I also wanted to ask about the weather forecast for tomorrow."),
    ("assistant", "I don't have access to real-time weather data, but you could check a weather app."),
    ("user", "Oh, I forgot my umbrella at home today. It started raining unexpectedly."),
    ("assistant", "That's unfortunate. Weather can be quite unpredictable sometimes."),
    ("user", "Speaking of unpredictable, have you been following the sports news lately?"),
    ("assistant", "I don't follow sports closely. Is there something big happening?"),
    ("user", "The championship finals are coming up next week. Very exciting!"),
    ("assistant", "I'm sure it will be exciting for the fans."),
    ("user", "I'm planning to watch it with friends at a sports bar."),
    ("assistant", "That sounds like a fun social event."),
    ("user", "By the way, I've been learning a new language recently."),
    ("assistant", "Which language are you learning?"),
    ("user", "I'm taking Spanish lessons online. The grammar is quite different from English."),
    ("assistant", "Spanish is a beautiful language. Regular practice is key to learning."),
    ("user", "I practice for about 30 minutes every day. It's slow progress but I'm improving."),
    ("assistant", "Consistency is the most important factor in language learning."),
    ("user", "Speaking of learning, I finished reading that book you recommended last month."),
    ("assistant", "What did you think of it?"),
    ("user", "It was thought-provoking. The ending surprised me completely."),
    ("assistant", "I'm glad you enjoyed it. Books that surprise us are often the most memorable."),
    ("user", "I've started another one by the same author. Can't put it down."),
    ("assistant", "That sounds like a page-turner. What genre is it?"),
    ("user", "It's science fiction. The world-building is absolutely incredible."),
    ("assistant", "Science fiction offers such creative possibilities for storytelling."),
    ("user", "I've also been trying to eat healthier lately."),
    ("assistant", "That's a great goal. What changes have you made?"),
    ("user", "I'm cutting down on processed foods and eating more vegetables."),
    ("assistant", "Small sustainable changes are better than drastic diets."),
    ("user", "I've also started going to the gym three times a week."),
    ("assistant", "Exercise combined with good nutrition is a powerful combination."),
    ("user", "The first week was hard, but now I'm getting used to the routine."),
    ("assistant", "Building healthy habits takes time, but it's worth the effort."),
    ("user", "I noticed my energy levels have improved significantly."),
    ("assistant", "That's a great sign that your efforts are paying off."),
]

def load_multihop_data() -> List[Dict]:
    """加载T1-Multihop数据"""
    items = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    print(f"Loaded {len(items)} Multihop items from {INPUT_FILE}")
    return items

def calculate_dialog_length(item: Dict) -> int:
    """计算对话总字数"""
    total = len(item.get('context', ''))
    for turn in item.get('conversation', []):
        total += len(turn.get('content', ''))
    total += len(item.get('query', ''))
    total += len(str(item.get('answer', '')))
    return total

def expand_conversation(item: Dict, target_length: int) -> Dict:
    """扩展对话长度"""
    expanded = dict(item)
    conversation = list(item.get('conversation', []))
    
    # 计算当前长度
    current_length = calculate_dialog_length(item)
    
    # 添加噪声对话
    noise_to_add = []
    added_length = 0
    
    while current_length + added_length < target_length:
        # 选择随机噪声模板（取一组，包含用户和助手交替）
        start_idx = random.randint(0, len(NOISE_TEMPLATES) - 10)
        end_idx = min(start_idx + 10, len(NOISE_TEMPLATES))
        
        for i in range(start_idx, end_idx):
            role, content = NOISE_TEMPLATES[i]
            noise_to_add.append({"role": role, "content": content})
            added_length += len(content)
        
        # 防止无限循环
        if len(noise_to_add) > 50:
            break
    
    # 在原始对话前插入噪声
    if noise_to_add:
        # 在对话中间插入噪声（不要在最开头或最结尾）
        insert_position = max(1, len(conversation) // 3)
        expanded_conversation = conversation[:insert_position] + noise_to_add[:min(len(noise_to_add), 20)] + conversation[insert_position:]
        expanded['conversation'] = expanded_conversation
    
    # 更新子任务
    expanded['sub_task'] = 'T4-Multi-hop'
    expanded['task'] = 'T4'
    
    return expanded

def create_multihop_sample(item: Dict) -> Dict:
    """创建单个T4 Multi-hop样本"""
    # 创建基础样本
    sample = {
        'task': 'T4',
        'sub_task': 'T4-Multi-hop',
        'context': item.get('context', ''),
        'conversation': item.get('conversation', []),
        'query': item.get('query', ''),
        'answer': item.get('answer', ''),
        'state_info': {
            'type': 'long_context_multihop',
            'original_task': item.get('task', ''),
            'original_sub_task': item.get('sub_task', ''),
            'source': 'T1-Multihop'
        },
        'ground_truth': item.get('ground_truth', {}),
        'difficulty': 'hard',
        'source_id': f"t4_multihop_{item.get('source_id', '')}"
    }
    
    # 扩展对话
    sample = expand_conversation(sample, MIN_LENGTH)
    
    return sample

def main():
    """主函数"""
    print("=" * 60)
    print("构造T4 Multi-hop数据集")
    print("=" * 60)
    print(f"输入: {INPUT_FILE}")
    print(f"输出: {OUTPUT_FILE}")
    print(f"目标数量: {TARGET_COUNT}")
    print(f"最小长度: {MIN_LENGTH} 字")
    print()
    
    # 加载原始数据
    source_items = load_multihop_data()
    
    # 选择并扩展样本
    selected = []
    
    # 如果源数据少于目标数量，就使用全部并复制
    while len(selected) < min(TARGET_COUNT, len(source_items)):
        for item in source_items[:TARGET_COUNT]:
            if len(selected) >= TARGET_COUNT:
                break
            sample = create_multihop_sample(item)
            selected.append(sample)
    
    # 如果仍然不够，随机复制
    while len(selected) < TARGET_COUNT:
        sample = create_multihop_sample(random.choice(source_items))
        selected.append(sample)
    
    # 统计长度分布
    lengths = [calculate_dialog_length(item) for item in selected]
    
    print(f"\n生成的数据统计:")
    print(f"  总数: {len(selected)}")
    print(f"  最小长度: {min(lengths)}")
    print(f"  最大长度: {max(lengths)}")
    print(f"  平均长度: {sum(lengths) / len(lengths):.0f}")
    print(f"  符合标准(>{MIN_LENGTH}): {sum(1 for l in lengths if l >= MIN_LENGTH)}")
    
    # 保存
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for item in selected:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n保存到: {OUTPUT_FILE}")
    print("=" * 60)
    print("完成!")

if __name__ == '__main__':
    main()