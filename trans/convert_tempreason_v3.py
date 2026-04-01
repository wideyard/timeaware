#!/usr/bin/env python3
"""
TempReason Dataset Conversion Script for Time-Aware Benchmark

Converts TempReason dataset to conversational format following the analysis in TempReason.md.

Task Mapping:
- T1 (Time Calculation): L1 data - pure time arithmetic with noise injection
- T2 (State Update): L2/L3 data - temporal position/state tracking

L1: Pure time offset/duration calculation
L2: Position held at a specific time (with fact_context)
L3: Before/after position questions (state transitions)
"""

import json
import os
import random
import re
import hashlib
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# ============== Noise Injection Resources ==============

# Historical noise facts (for T1 context interference)
HISTORICAL_NOISE = [
    "1185年是日本平安时代末期，发生了著名的坛之浦之战，平氏政权灭亡。",
    "1789年法国大革命爆发，巴士底狱被攻陷，标志着旧制度的终结。",
    "1914年第一次世界大战爆发，改变了欧洲的政治格局。",
    "1969年人类首次登上月球，阿波罗11号任务成功完成。",
    "1492年哥伦布发现美洲大陆，开启了大航海时代。",
    "1440年古腾堡发明活字印刷术，推动了欧洲文艺复兴。",
    "1776年美国独立宣言签署，标志着美利坚合众国的诞生。",
    "1666年伦敦大火烧毁了城市大部分建筑，但也带来了重建机会。",
    "1989年柏林墙倒塌，标志着冷战的结束。",
    "1519年麦哲伦开始环球航行，证明了地球是圆的。",
    "1896年现代奥林匹克运动会在雅典首次举办。",
    "1945年第二次世界大战结束，联合国成立。",
    "2001年中国加入世界贸易组织，成为全球经济的重要参与者。",
    "1347年黑死病在欧洲开始蔓延，造成了巨大的人口损失。",
    "1848年欧洲革命浪潮席卷多个国家，被称为'民族之春'。",
]

# Daily life noise (for T1 context interference)
DAILY_NOISE = [
    "顺便说一下，我今天下午有一个两小时的会议。",
    "对了，天气预报说明天有雨。",
    "我昨天买了一本关于历史的书。",
   "这个月的电费账单应该快来了。",
    "我记得上周看了个好电影。",
    "公交车每天早上7点开始运行。",
    "早餐我通常吃面包和咖啡。",
    "邻居家的猫又在叫了。",
    "今年的生日是在周二。",
    "那个商店周末会打折。",
]

# Time-related confusion noise (for increased difficulty)
TIME_CONFUSION_NOISE = [
    "（某人说：我记得是在三月，也可能是四月...）",
    "（这让我想起另一个时间点：大约三年前发生了一件类似的事情）",
    "（有传闻说是在更早的时候，但官方记录显示是更晚）",
    "（不同来源对具体月份有不同说法）",
    "（历史上的时间记录有时会有误差）",
]

def load_json_data(filepath: str) -> List[Dict]:
    """Load JSON/JSONL data file."""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        # Try to determine format
        if content.startswith('['):
            # Regular JSON array
            data = json.loads(content)
        else:
            # JSONL format (one JSON per line)
            for line in content.split('\n'):
                if line.strip():
                    data.append(json.loads(line))
    return data

def generate_id(prefix: str, content: str, task: str) -> str:
    """Generate unique ID for each converted item."""
    hash_input = f"{content}_{task}"
    hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:10]
    return f"tempreason_{prefix}_{hash_val}"

# ============== T1: Time Calculation (L1 Data) ==============

def parse_time_question(question: str) -> Optional[Tuple[str, str]]:
    """Parse time offset from question."""
    # Pattern: "What is the time X year and Y month after/before [Month, Year]"
    patterns = [
        r"What is the time (\d+) year and (\d+) month (after|before) (\w+),\s*(\d+)",
        r"What is the time (\d+) year (after|before) (\w+),\s*(\d+)",
        r"What is the time (\d+) month (after|before) (\w+),\s*(\d+)",
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.match(pattern, question, re.IGNORECASE)
        if match:
            if i == 0:
                return (f"{match.group(1)}年{match.group(2)}月", match.group(3))
            elif i == 1:
                return (f"{match.group(1)}年", match.group(2))
            else:
                return (f"{match.group(1)}月", match.group(2))
    return None

def convert_l1_to_t1(item: Dict) -> List[Dict]:
    """
    Convert L1 pure calculation to T1 time calculation with noise injection.
    
    Strategy: Embed the time calculation in distracting context
    """
    results = []
    
    question = item.get('question', '')
    answer = item.get('text_answers', {}).get('text', [''])[0]
    ref_date = item.get('date', '')
    item_id = item.get('id', '0')
    
    if not question or not answer:
        return results
    
    # Parse the time offset
    parsed = parse_time_question(question)
    if parsed:
        offset_str, direction = parsed
    else:
        offset_str = "时间偏移"
        direction = "after"
    
    # Format reference date for Chinese
    # Extract month and year from ref_date like "March 26, 1873"
    date_match = re.search(r'(\w+)\s+\d+,\s*(\d+)', ref_date)
    if date_match:
        month_name, year = date_match.groups()
        month_map = {
            'January': '1月', 'February': '2月', 'March': '3月', 'April': '4月',
            'May': '5月', 'June': '6月', 'July': '7月', 'August': '8月',
            'September': '9月', 'October': '10月', 'November': '11月', 'December': '12月'
        }
        month_cn = month_map.get(month_name, month_name)
        ref_date_cn = f"{year}年{month_cn}"
    else:
        ref_date_cn = ref_date
    
    direction_cn = "之后" if direction == "after" else "之前"
    
    # ============== Create T1 variants with different noise levels ==============
    
    # Variant 1: Historical context noise
    noise1 = random.choice(HISTORICAL_NOISE)
    noise2 = random.choice(DAILY_NOISE)
    
    conversation1 = [
        {"role": "user", "content": noise1},
        {"role": "assistant", "content": "好的，我了解了这个历史背景。"},
        {"role": "user", "content": f"现在有一个时间计算问题：假设某个事件发生在{ref_date_cn}{direction_cn}{offset_str}。"},
        {"role": "assistant", "content": "我理解了时间偏移计算的要求。"},
        {"role": "user", "content": noise2},
        {"role": "assistant", "content": "好的，这与时间计算无关，但我会记住这个信息。"},
        {"role": "user", "content": "请计算该事件结束的具体时间（年月）。"}
    ]
    
    result1 = {
        "task": "T1",
        "sub_task": "T1-TimeCalc-HistNoise",
        "context": f"Time calculation with historical noise: {question}",
        "conversation": conversation1,
        "query": f"起始时间：{ref_date_cn}，偏移：{offset_str}（{direction_cn}），结束时间是？",
        "answer": answer,
        "state_info": {
            "type": "time_offset_calculation",
            "reference_date": ref_date_cn,
            "offset": offset_str,
            "direction": direction,
            "noise_type": "historical"
        },
        "ground_truth": {
            "original_question": question,
            "reference_date": ref_date,
            "offset": offset_str,
            "correct_answer": answer
        },
        "difficulty": "medium",
        "source_id": generate_id("L1_hist", question, "T1")
    }
    results.append(result1)
    
    # Variant 2: Time confusion noise
    noise_time = random.choice(TIME_CONFUSION_NOISE)
    noise_hist = random.choice(HISTORICAL_NOISE[:7])
    
    conversation2 = [
        {"role": "user", "content": f"关于时间计算，有一个重要的事实：{noise_hist}"},
        {"role": "assistant", "content": "明白了，这是相关的历史背景信息。"},
        {"role": "user", "content": f"{noise_time}"},
        {"role": "assistant", "content": "我注意到这里有关于时间的混淆信息。"},
        {"role": "user", "content": f"现在请忽略这些干扰：起始时间是{ref_date_cn}，计算{offset_str}{direction_cn}的时间点。"}
    ]
    
    result2 = {
        "task": "T1",
        "sub_task": "T1-TimeCalc-ConfusionNoise",
        "context": f"Time calculation with confusion noise: {question}",
        "conversation": conversation2,
        "query": f"忽略干扰，计算{ref_date_cn}{direction_cn}{offset_str}的时间点。",
        "answer": answer,
        "state_info": {
            "type": "time_offset_calculation",
            "noise_type": "confusion"
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer
        },
        "difficulty": "hard",
        "source_id": generate_id("L1_conf", question, "T1")
    }
    results.append(result2)
    
    # Variant 3: Multi-step calculation (noise with numbers)
    number_noise = f"顺便提一下，这段历史持续了{random.randint(3,15)}年，涉及{random.randint(10,100)}个重要人物。"
    
    conversation3 = [
        {"role": "user", "content": f"让我们进行一个时间计算练习。"},
        {"role": "assistant", "content": "好的，请提供起始时间和偏移量。"},
        {"role": "user", "content": f"{number_noise}忽略这些数字，它们与此题无关。"},
        {"role": "assistant", "content": "我会忽略无关的数字，专注于时间计算。"},
        {"role": "user", "content": f"起始时间：{ref_date_cn}。需要计算{offset_str}{direction_cn}的时间点。"}
    ]
    
    result3 = {
        "task": "T1",
        "sub_task": "T1-TimeCalc-NumNoise",
        "context": f"Time calculation with numeric noise: {question}",
        "conversation": conversation3,
        "query": f"起始时间{ref_date_cn}，{direction_cn}{offset_str}，结果时间是？",
        "answer": answer,
        "state_info": {
            "type": "time_offset_calculation",
            "noise_type": "numeric"
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer
        },
        "difficulty": "hard",
        "source_id": generate_id("L1_num", question, "T1")
    }
    results.append(result3)
    
    return results

# ============== T2: State Update (L2 Data) ==============

def parse_position_timeframes(fact_context: str) -> List[Dict]:
    """Parse position timeframes from fact_context."""
    positions = []
    
    # Pattern: "X holds the position of Y from [start] to [end]"
    pattern = r'([^.]+?)\s*holds the position of\s+([^;.\n]+?)\s+from\s+([A-Za-z]+,?\s*\d+)\s+to\s+([A-Za-z]+,?\s*\d+)'
    
    for match in re.finditer(pattern, fact_context, re.IGNORECASE):
        person = match.group(1).strip()
        position = match.group(2).strip()
        start_time = match.group(3).strip()
        end_time = match.group(4).strip()
        positions.append({
            'person': person,
            'position': position,
            'start': start_time,
            'end': end_time
        })
    
    return positions

def convert_timeframe_to_state(positions: List[Dict]) -> str:
    """Convert position timeframes to state sequence narrative."""
    if not positions:
        return ""
    
    narratives = []
    for pos in positions:
        # Normalize time format
        start = pos['start'].replace(',', '').strip()
        end = pos['end'].replace(',', '').strip()
        narratives.append(f"{start}--{pos['position']}的开始--")
        narratives.append(f"{end}--{pos['position']}的结束--")
    
    return "\n".join(narratives)

def convert_l2_to_t2(item: Dict) -> List[Dict]:
    """
    Convert L2 position query to T2 state tracking task.
    
    L2: "Which position did X hold in [Month, Year]?"
    fact_context contains explicit time ranges for positions.
    """
    results = []
    
    question = item.get('question', '')
    answer = item.get('text_answers', {}).get('text', [''])[0]
    fact_context = item.get('fact_context', '')
    context = item.get('context', '')
    query_date = item.get('date', '')
    neg_answers = item.get('neg_answers', [])
    
    if not question or not answer:
        return results
    
    # Parse position timeframes from fact_context
    positions = parse_position_timeframes(fact_context)
    
    if not positions:
        # Fallback: create basic state task from context
        return create_basic_state_task(item, "L2_basic")
    
    # Extract person name from question
    person_match = re.search(r'Which position did\s+([A-Za-z\s]+?)\s+hold', question)
    person_name = person_match.group(1).strip() if person_match else "某人"
    
    # Format query date
    date_match = re.search(r'(\w+),?\s*(\d+)', query_date)
    if date_match:
        month_name, year = date_match.groups()
        month_map = {
            'January': '1月', 'February': '2月', 'March': '3月', 'April': '4月',
            'May': '5月', 'June': '6月', 'July': '7月', 'August': '8月',
            'September': '9月', 'October': '10月', 'November': '11月', 'December': '12月'
        }
        month_cn = month_map.get(month_name, month_name)
        query_date_cn = f"{year}年{month_cn}"
    else:
        query_date_cn = query_date
    
    # ============== T2 Variant 1: State Timeline Tracking ==============
    
    # Build state sequence
    state_sequence = []
    for pos in positions:
        state_sequence.append(f"- 从{pos['start']}到{pos['end']}：担任{pos['position']}")
    
    conversation1 = [
        {"role": "user", "content": f"让我们追踪{person_name}的职业/职位变化。"},
        {"role": "assistant", "content": "好的，请提供相关信息。"},
        {"role": "user", "content": "以下是该人物的任职时间线："},
        {"role": "user", "content": "\n".join(state_sequence)},
        {"role": "assistant", "content": "我已了解这个时间线信息。"},
        {"role": "user", "content": f"问题：在{query_date_cn}，{person_name}担任什么职位？"}
    ]
    
    result1 = {
        "task": "T2",
        "sub_task": "T2-PositionTrack-Timeline",
        "context": f"Position tracking for {person_name} with explicit timeframes",
        "conversation": conversation1,
        "query": f"给定时间线，{query_date_cn}时该人物担任什么职位？",
        "answer": answer,
        "state_info": {
            "type": "position_tracking",
            "person": person_name,
            "query_date": query_date_cn,
            "positions": positions
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer,
            "neg_answers": neg_answers,
            "fact_context": fact_context,
            "all_positions": positions
        },
        "difficulty": "medium",
        "source_id": generate_id("L2", question, "T2_1")
    }
    results.append(result1)
    
    # ============== T2 Variant 2: State with Background Noise ==============
    
    # Use context as background noise
    context_summary = context[:300] + "..." if len(context) > 300 else context
    
    conversation2 = [
        {"role": "user", "content": f"背景信息：{context_summary}"},
        {"role": "assistant", "content": "我已经了解了背景信息。"},
        {"role": "user", "content": "现在关注时间节点上的职位变化："},
        {"role": "user", "content": "\n".join(state_sequence)},
        {"role": "assistant", "content": "我理解了这些职位时间线。"},
        {"role": "user", "content": f"请告诉我，在{query_date_cn}，该人物是什么职位？"}
    ]
    
    result2 = {
        "task": "T2",
        "sub_task": "T2-PositionTrack-WithContext",
        "context": f"Position tracking with biographical context",
        "conversation": conversation2,
        "query": f"结合背景和时间线，{query_date_cn}时的职位是？",
        "answer": answer,
        "state_info": {
            "type": "position_tracking",
            "noise_type": "background_context"
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer,
            "neg_answers": neg_answers,
            "all_positions": positions
        },
        "difficulty": "hard",
        "source_id": generate_id("L2", question, "T2_2")
    }
    results.append(result2)
    
    # ============== T2 Variant 3: Multiple Choice with Confidence ==============
    
    options_text = f"A. {answer}\nB. {neg_answers[0] if neg_answers else '其他职位1'}\nC. {neg_answers[1] if len(neg_answers) > 1 else '其他职位2'}"
    
    conversation3 = [
        {"role": "user", "content": "根据以下时间线进行状态追踪："},
        {"role": "user", "content": "\n".join(state_sequence)},
        {"role": "assistant", "content": "我已掌握时间线信息。"},
        {"role": "user", "content": f"在{query_date_cn}时，{person_name}的职位是什么？选择正确答案："},
        {"role": "user", "content": options_text}
    ]
    
    result3 = {
        "task": "T2",
        "sub_task": "T2-PositionTrack-MC",
        "context": f"Multiple choice position tracking",
        "conversation": conversation3,
        "query": f"选择{query_date_cn}时的正确职位。",
        "answer": f"A. {answer}",
        "state_info": {
            "type": "multiple_choice",
            "correct_option": "A"
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer,
            "neg_answers": neg_answers
        },
        "difficulty": "easy",
        "source_id": generate_id("L2", question, "T2_3")
    }
    results.append(result3)
    
    return results

def create_basic_state_task(item: Dict, prefix: str) -> List[Dict]:
    """Create basic state task when no position timeframes can be parsed."""
    results = []
    
    question = item.get('question', '')
    answer = item.get('text_answers', {}).get('text', [''])[0]
    context = item.get('context', '')
    
    if not question or not answer:
        return results
    
    # Basic conversion without explicit timeframes
    conversation = [
        {"role": "user", "content": f"阅读以下信息：{context[:200]}..."},
        {"role": "assistant", "content": "我已阅读。"},
        {"role": "user", "content": question}
    ]
    
    result = {
        "task": "T2",
        "sub_task": "T2-PositionTrack-Basic",
        "context": f"Basic position tracking from context",
        "conversation": conversation,
        "query": question,
        "answer": answer,
        "state_info": {
            "type": "basic_tracking"
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer
        },
        "difficulty": "easy",
        "source_id": generate_id(prefix, question, "T2_basic")
    }
    results.append(result)
    
    return results

# ============== T2: State Transitions (L3 Data) ==============

def convert_l3_to_t2(item: Dict) -> List[Dict]:
    """
    Convert L3 before/after questions to T2 state transition task.
    
    L3: "Which position did X hold before/after [position]?"
    Requires understanding state transitions over time.
    """
    results = []
    
    question = item.get('question', '')
    answer = item.get('text_answers', {}).get('text', [''])[0]
    fact_context = item.get('fact_context', '')
    context = item.get('context', '')
    neg_answers = item.get('neg_answers', [])
    
    if not question or not answer:
        return results
    
    # Parse position timeframes
    positions = parse_position_timeframes(fact_context)
    
    if not positions:
        return create_basic_state_task(item, "L3")
    
    # Determine if before/after
    is_before = 'before' in question.lower()
    is_after = 'after' in question.lower()
    
    # Extract person name
    person_match = re.search(r'Which position did\s+([A-Za-z\s]+?)\s+hold (before|after)', question)
    person_name = person_match.group(1).strip() if person_match else "某人"
    
    # Extract reference position
    ref_pos_match = re.search(r'(?:before|after)\s+(.+?)\?$', question)
    ref_position = ref_pos_match.group(1).strip('?') if ref_pos_match else "某职位"
    
    # Build ordered timeline
    timeline = []
    for pos in positions:
        # Sort by start time (simplified - actual implementation would parse dates)
        timeline.append({
            'position': pos['position'],
            'start': pos['start'],
            'end': pos['end']
        })
    
    # ============== T2 Transition Variant 1: Sequence Tracking ==============
    
    # Build state change narrative
    state_changes = []
    for i, pos in enumerate(positions):
        state_changes.append(f"{i+1}. 从{pos['start']}到{pos['end']}：{pos['position']}")
    
    transition_type = "前序职位" if is_before else "后继职位"
    direction_hint = "更早" if is_before else "更晚"
    
    conversation1 = [
        {"role": "user", "content": f"让我们分析{person_name}的职业生涯状态变化。"},
        {"role": "assistant", "content": "好的，请提供该人物的任职顺序。"},
        {"role": "user", "content": "以下是按时间顺序排列的职位变化："},
        {"role": "user", "content": "\n".join(state_changes)},
        {"role": "assistant", "content": "我已了解职位时间线。"},
        {"role": "user", "content": f"问题：{person_name}在担任'{ref_position}'之{transition_type}是什么？"},
        {"role": "assistant", "content": f"需要找出比'{ref_position}'时间上{direction_hint}的职位。"},
        {"role": "user", "content": "请回答具体的职位名称。"}
    ]
    
    result1 = {
        "task": "T2",
        "sub_task": "T2-StateTransition-BeforeAfter",
        "context": f"State transition: {transition_type} of {ref_position}",
        "conversation": conversation1,
        "query": f"在'{ref_position}'之{transition_type}，该人物担任什么职位？",
        "answer": answer,
        "state_info": {
            "type": "state_transition",
            "transition_type": "predecessor" if is_before else "successor",
            "reference_position": ref_position,
            "timeline": timeline
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer,
            "neg_answers": neg_answers,
            "transition_direction": "before" if is_before else "after"
        },
        "difficulty": "medium",
        "source_id": generate_id("L3_before" if is_before else "L3_after", question, "T2_1")
    }
    results.append(result1)
    
    # ============== T2 Transition Variant 2: With Background ==============
    
    context_summary = context[:250] + "..." if len(context) > 250 else context
    
    conversation2 = [
        {"role": "user", "content": f"背景：{context_summary}"},
        {"role": "assistant", "content": "了解了人物的背景信息。"},
        {"role": "user", "content": "职位变化时间线："},
        {"role": "user", "content": "\n".join(state_changes)},
        {"role": "assistant", "content": "已记录职位时间线。"},
        {"role": "user", "content": f"{person_name}从'{ref_position}'刚{( '卸任转入' if is_after else '之前担任' )}什么职位？"}
    ]
    
    result2 = {
        "task": "T2",
        "sub_task": "T2-StateTransition-WithContext",
        "context": f"State transition with biographical context",
        "conversation": conversation2,
        "query": f"根据时间线，{transition_type}的职位是？",
        "answer": answer,
        "state_info": {
            "type": "state_transition",
            "noise_type": "background_context"
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer,
            "neg_answers": neg_answers
        },
        "difficulty": "hard",
        "source_id": generate_id("L3_context", question, "T2_2")
    }
    results.append(result2)
    
    # ============== T2 Transition Variant 3: Multiple Choice ==============
    
    options_text = f"A. {answer}\nB. {neg_answers[0] if neg_answers else '其他职位'}\nC. {neg_answers[1] if len(neg_answers) > 1 else '另一职位'}"
    
    conversation3 = [
        {"role": "user", "content": "根据职位时间线回答问题："},
        {"role": "user", "content": "\n".join(state_changes)},
        {"role": "assistant", "content": "已理解时间线。"},
        {"role": "user", "content": f"{person_name}在'{ref_position}'之{transition_type}的职位是什么？"},
        {"role": "user", "content": f"选择正确答案：\n{options_text}"}
    ]
    
    result3 = {
        "task": "T2",
        "sub_task": "T2-StateTransition-MC",
        "context": f"Multiple choice state transition",
        "conversation": conversation3,
        "query": f"选择{transition_type}的正确职位。",
        "answer": f"A. {answer}",
        "state_info": {
            "type": "multiple_choice",
            "correct_option": "A"
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer,
            "neg_answers": neg_answers
        },
        "difficulty": "easy",
        "source_id": generate_id("L3_mc", question, "T2_3")
    }
    results.append(result3)
    
    return results

# ============== Main Conversion Function ==============

def convert_tempreason_to_conversational(input_file: str, output_file: str, level: str, split: str):
    """
    Main conversion function for TempReason data.
    
    Level: 'L1', 'L2', or 'L3'
    """
    print(f"Loading {input_file}...")
    data = load_json_data(input_file)
    print(f"Loaded {len(data)} examples for {level}")
    
    converted_data = []
    stats = defaultdict(int)
    
    for item in data:
        if level == 'L1':
            # T1: Time Calculation with noise
            results = convert_l1_to_t1(item)
            for r in results:
                if 'HistNoise' in r['sub_task']:
                    stats['T1-HistNoise'] += 1
                elif 'ConfusionNoise' in r['sub_task']:
                    stats['T1-ConfusionNoise'] += 1
                elif 'NumNoise' in r['sub_task']:
                    stats['T1-NumNoise'] += 1
                else:
                    stats['T1-Other'] += 1
        
        elif level == 'L2':
            # T2: State Update (Position at time)
            results = convert_l2_to_t2(item)
            for r in results:
                if 'Timeline' in r['sub_task']:
                    stats['T2-Timeline'] += 1
                elif 'WithContext' in r['sub_task']:
                    stats['T2-WithContext'] += 1
                elif 'MC' in r['sub_task']:
                    stats['T2-MC'] += 1
                else:
                    stats['T2-Basic'] += 1
        
        elif level == 'L3':
            # T2: State Transitions (Before/After)
            results = convert_l3_to_t2(item)
            for r in results:
                if 'BeforeAfter' in r['sub_task']:
                    stats['T2-BeforeAfter'] += 1
                elif 'WithContext' in r['sub_task']:
                    stats['T2-TransitionWithContext'] += 1
                elif 'MC' in r['sub_task']:
                    stats['T2-TransitionMC'] += 1
                else:
                    stats['T2-Transition'] += 1
        
        else:
            results = []
        
        converted_data.extend(results)
    
    # Write output
    print(f"Writing {len(converted_data)} converted items for {level}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in converted_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Write stats
    stats_file = output_file.replace('.jsonl', '_report.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        report = {
            "source": "TempReason",
            "level": level,
            "split": split,
            "total_items": len(converted_data),
            "total_examples": len(data),
            "statistics": dict(stats),
            "task_distribution": {
                "T1_TimeCalc": sum(v for k, v in stats.items() if k.startswith('T1')),
                "T2_StateTrack": sum(v for k, v in stats.items() if k.startswith('T2'))
            }
        }
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"{level} conversion complete. Stats: {dict(stats)}")
    return stats

def main():
    # Set random seed for reproducibility
    random.seed(42)
    
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data", "TempReason")
    output_dir = os.path.join(base_dir, "converted_data_v3")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    all_stats = {}
    
    # ============== Process L1 (Time Calculation) ==============
    print("\n" + "="*50)
    print("Processing L1 - Time Calculation")
    print("="*50)
    
    # Train L1
    train_l1 = os.path.join(data_dir, "train_l1.json")
    if os.path.exists(train_l1):
        output = os.path.join(output_dir, "tempreason_l1_train_conversational.jsonl")
        all_stats['L1_train'] = convert_tempreason_to_conversational(train_l1, output, "L1", "train")
    else:
        print(f"File not found: {train_l1}")
    
    # Val L1
    val_l1 = os.path.join(data_dir, "val_l1.json")
    if os.path.exists(val_l1):
        output = os.path.join(output_dir, "tempreason_l1_val_conversational.jsonl")
        all_stats['L1_val'] = convert_tempreason_to_conversational(val_l1, output, "L1", "val")
    else:
        print(f"File not found: {val_l1}")
    
    # Test L1
    test_l1 = os.path.join(data_dir, "test_l1.jsonl")
    if os.path.exists(test_l1):
        output = os.path.join(output_dir, "tempreason_l1_test_conversational.jsonl")
        all_stats['L1_test'] = convert_tempreason_to_conversational(test_l1, output, "L1", "test")
    else:
        print(f"File not found: {test_l1}")
    
    # ============== Process L2 (Position at Time) ==============
    print("\n" + "="*50)
    print("Processing L2 - Position at Time (State Tracking)")
    print("="*50)
    
    # Train L2
    train_l2 = os.path.join(data_dir, "train_l2.json")
    if os.path.exists(train_l2):
        output = os.path.join(output_dir, "tempreason_l2_train_conversational.jsonl")
        all_stats['L2_train'] = convert_tempreason_to_conversational(train_l2, output, "L2", "train")
    else:
        print(f"File not found: {train_l2}")
    
    # Val L2
    val_l2 = os.path.join(data_dir, "val_l2.json")
    if os.path.exists(val_l2):
        output = os.path.join(output_dir, "tempreason_l2_val_conversational.jsonl")
        all_stats['L2_val'] = convert_tempreason_to_conversational(val_l2, output, "L2", "val")
    else:
        print(f"File not found: {val_l2}")
    
    # Test L2
    test_l2 = os.path.join(data_dir, "test_l2.json")
    if os.path.exists(test_l2):
        output = os.path.join(output_dir, "tempreason_l2_test_conversational.jsonl")
        all_stats['L2_test'] = convert_tempreason_to_conversational(test_l2, output, "L2", "test")
    else:
        print(f"File not found: {test_l2}")
    
    # ============== Process L3 (Before/After Transitions) ==============
    print("\n" + "="*50)
    print("Processing L3 - Before/After (State Transitions)")
    print("="*50)
    
    # Train L3
    train_l3 = os.path.join(data_dir, "train_l3.json")
    if os.path.exists(train_l3):
        output = os.path.join(output_dir, "tempreason_l3_train_conversational.jsonl")
        all_stats['L3_train'] = convert_tempreason_to_conversational(train_l3, output, "L3", "train")
    else:
        print(f"File not found: {train_l3}")
    
    # Val L3
    val_l3 = os.path.join(data_dir, "val_l3.json")
    if os.path.exists(val_l3):
        output = os.path.join(output_dir, "tempreason_l3_val_conversational.jsonl")
        all_stats['L3_val'] = convert_tempreason_to_conversational(val_l3, output, "L3", "val")
    else:
        print(f"File not found: {val_l3}")
    
    # Test L3
    test_l3 = os.path.join(data_dir, "test_l3.json")
    if os.path.exists(test_l3):
        output = os.path.join(output_dir, "tempreason_l3_test_conversational.jsonl")
        all_stats['L3_test'] = convert_tempreason_to_conversational(test_l3, output, "L3", "test")
    else:
        print(f"File not found: {test_l3}")
    
    # ============== Summary ==============
    print("\n" + "="*50)
    print("CONVERSION COMPLETE")
    print("="*50)
    
    total_t1 = sum(s.get('T1-TimeCalc', 0) + s.get('T1-HistNoise', 0) + s.get('T1-ConfusionNoise', 0) + s.get('T1-NumNoise', 0) + s.get('T1-Other', 0) for s in all_stats.values() if isinstance(s, dict))
    total_t2 = sum(s.get('T2-Timeline', 0) + s.get('T2-WithContext', 0) + s.get('T2-MC', 0) + s.get('T2-Basic', 0) + s.get('T2-BeforeAfter', 0) + s.get('T2-TransitionWithContext', 0) + s.get('T2-TransitionMC', 0) + s.get('T2-Transition', 0) for s in all_stats.values() if isinstance(s, dict))
    
    print(f"Total T1 (Time Calculation) items: {total_t1}")
    print(f"Total T2 (State Tracking) items: {total_t2}")
    print(f"All output files saved to: {output_dir}")

if __name__ == "__main__":
    main()