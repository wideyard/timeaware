"""从MCTACO数据集提取事件-持续时间对"""

import json
import re
import os
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# 时间单位转换为秒
TIME_UNITS = {
    'second': 1,
    'seconds': 1,
    'minute': 60,
    'minutes': 60,
    'hour': 3600,
    'hours': 3600,
    'day': 86400,
    'days': 86400,
    'week': 604800,
    'weeks': 604800,
    'month': 2592000,  # 30天
    'months': 2592000,
    'year': 31536000,  # 365天
    'years': 31536000,
}

# 数字词映射
NUMBER_WORDS = {
    'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11,
    'twelve': 12, 'dozen': 12, 'hundred': 100, 'hundreds': 100,
    'thousand': 1000, 'thousands': 1000, 'million': 1000000, 'billion': 1000000000,
}

def parse_duration_to_seconds(duration_str: str) -> Optional[float]:
    """将持续时间字符串转换为秒数
    
    Examples:
        "6 months" -> 15552000
        "an hour" -> 3600
        "2 hours" -> 7200
        "hundreds of years" -> 3153600000 (100 years)
    """
    duration_str = duration_str.lower().strip()
    
    # 处理 "X of Y" 格式，如 "hundreds of years"
    of_match = re.match(r'(\w+)\s+of\s+(\w+)', duration_str)
    if of_match:
        num_word = of_match.group(1)
        unit = of_match.group(2)
        if num_word in NUMBER_WORDS and unit in TIME_UNITS:
            return NUMBER_WORDS[num_word] * TIME_UNITS[unit]
    
    # 处理 "the storm lasted through the day" 这类描述性答案
    if 'lasted through' in duration_str:
        if 'morning' in duration_str or 'early morning' in duration_str:
            return 4 * 3600  # 约4小时
        if 'day' in duration_str:
            return 12 * 3600  # 约12小时
        if 'night' in duration_str:
            return 8 * 3600  # 约8小时
    
    # 处理标准格式：数字/单词 + 单位
    # 匹配模式：数字（或数字词）+ 可选的"s"+ 单位
    pattern = r'(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozen|hundred|thousand|million|billion)s?\s+(\w+)'
    match = re.search(pattern, duration_str)
    
    if match:
        num_str = match.group(1)
        unit = match.group(2)
        
        # 解析数字
        if num_str.isdigit():
            num = float(num_str)
        elif num_str in NUMBER_WORDS:
            num = NUMBER_WORDS[num_str]
        else:
            return None
        
        # 解析单位
        if unit in TIME_UNITS:
            return num * TIME_UNITS[unit]
    
    return None


def extract_event_from_question(question: str) -> str:
    """从问题中提取事件
    
    Examples:
        "How long was his mother ill?" -> "his mother was ill"
        "How long was the storm?" -> "the storm"
        "How long did the meeting last?" -> "the meeting"
    """
    question = question.strip()
    
    # 移除问号
    question = question.rstrip('?')
    
    # 常见的问题模式
    patterns = [
        r'[Hh]ow long (?:did|was|has|have) (.+)',
        r'[Hh]ow long (?:did|was|has|have) (.+?) (?:last|endure|continue)',
        r'[Hh]ow many (?:hours|minutes|seconds|days|weeks|months|years) (?:did|was|has|have) (.+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            event = match.group(1).strip()
            # 清理事件描述
            event = re.sub(r'\s+', ' ', event)
            return event
    
    # 如果没有匹配到模式，返回整个问题（去掉How long等）
    event = re.sub(r'^(?:[Hh]ow long|[Hh]ow many \w+)\s*', '', question)
    return event.strip()


def load_mctaco_data(file_path: str) -> List[Dict]:
    """加载MCTACO数据"""
    data = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) >= 5:
                data.append({
                    'sentence': parts[0],
                    'question': parts[1],
                    'answer': parts[2],
                    'label': parts[3],
                    'category': parts[4]
                })
    
    return data


def extract_event_durations(data: List[Dict]) -> List[Dict]:
    """提取事件-持续时间对"""
    # 按 (sentence, question) 分组
    grouped = defaultdict(list)
    
    for item in data:
        if item['category'] == 'Event Duration' and item['label'] == 'yes':
            key = (item['sentence'], item['question'])
            grouped[key].append(item['answer'])
    
    # 提取事件和持续时间
    results = []
    
    for (sentence, question), durations in grouped.items():
        event = extract_event_from_question(question)
        
        # 解析所有持续时间
        parsed_durations = []
        for dur in durations:
            seconds = parse_duration_to_seconds(dur)
            if seconds is not None:
                parsed_durations.append((dur, seconds))
        
        if not parsed_durations:
            continue
        
        # 排序找出最小和最大
        parsed_durations.sort(key=lambda x: x[1])
        
        results.append({
            'sentence': sentence,
            'question': question,
            'event': event,
            'min_duration': parsed_durations[0][0],
            'max_duration': parsed_durations[-1][0],
            'min_seconds': parsed_durations[0][1],
            'max_seconds': parsed_durations[-1][1],
            'all_durations': [d[0] for d in parsed_durations],
            'all_seconds': [d[1] for d in parsed_durations]
        })
    
    return results


def main():
    """主函数"""
    data_dir = os.path.join(os.path.dirname(__file__), 'data', 'MCTACO', 'dataset')
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载数据
    print("加载MCTACO数据...")
    
    dev_data = load_mctaco_data(os.path.join(data_dir, 'dev_3783.tsv'))
    test_data = load_mctaco_data(os.path.join(data_dir, 'test_9442.tsv'))
    
    print(f"  dev数据: {len(dev_data)} 条")
    print(f"  test数据: {len(test_data)} 条")
    
    # 合并数据
    all_data = dev_data + test_data
    print(f"  总计: {len(all_data)} 条")
    
    # 统计Event Duration且label为yes的数据
    event_duration_yes = [d for d in all_data if d['category'] == 'Event Duration' and d['label'] == 'yes']
    print(f"\nEvent Duration (yes) 数据: {len(event_duration_yes)} 条")
    
    # 提取事件-持续时间对
    print("\n提取事件-持续时间对...")
    results = extract_event_durations(all_data)
    print(f"  提取到 {len(results)} 个事件-持续时间对")
    
    # 显示一些示例
    print("\n示例:")
    for i, r in enumerate(results[:5]):
        print(f"\n{i+1}. 事件: {r['event']}")
        print(f"   最小: {r['min_duration']} ({r['min_seconds']}秒)")
        print(f"   最大: {r['max_duration']} ({r['max_seconds']}秒)")
        print(f"   所有: {', '.join(r['all_durations'])}")
    
    # 保存结果
    output_path = os.path.join(output_dir, 'mctaco_event_durations.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_path}")


if __name__ == '__main__':
    main()
