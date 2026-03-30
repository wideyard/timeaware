#!/usr/bin/env python3
"""
TimeQA Dataset Conversion Script for Time-Aware Benchmark

Converts TimeQA dataset to conversational format following the analysis in TimeQA.md.

Task Mapping:
- T2 (State Update): Track position/location changes with time constraints
- T4 (Long-term Memory): Multi-turn retrieval from long context (paragraph-split)
- T1 (Time Calculation): Complex time boundary reasoning (between/intersection)

Key Features:
- Long context (~2000 words) for realistic long-context testing
- Easy/Hard splits for difficulty levels
- Human-authored questions for natural language
"""

import json
import os
import gzip
import random
import re
import hashlib
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

def load_json_data(filepath: str) -> List[Dict]:
    """Load JSON/JSONL/JSONL.GZIP data file."""
    data = []
    
    if filepath.endswith('.gzip'):
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    elif filepath.endswith('.jsonl'):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    else:
        # Regular JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content.startswith('['):
                data = json.loads(content)
            else:
                for line in content.split('\n'):
                    if line.strip():
                        data.append(json.loads(line))
    return data

def generate_id(prefix: str, content: str, task: str) -> str:
    """Generate unique ID for each converted item."""
    hash_input = f"{content[:100]}_{task}"
    hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:10]
    return f"timeqa_{prefix}_{hash_val}"

def parse_time_constraint(question: str) -> Dict:
    """Parse time constraint from question."""
    result = {
        'type': 'unknown',
        'time_start': None,
        'time_end': None,
        'time_point': None,
        'constraint_text': ''
    }
    
    # from X to Y (interval)
    match = re.search(r'from\s+(\w+\s*\d{0,4})\s+to\s+(\w+\s*\d{0,4})', question, re.IGNORECASE)
    if match:
        result['type'] = 'interval'
        result['time_start'] = match.group(1).strip()
        result['time_end'] = match.group(2).strip()
        result['constraint_text'] = f"from {result['time_start']} to {result['time_end']}"
        return result
    
    # between X and Y
    match = re.search(r'between\s+(\w+\s*\d{0,4})\s+and\s+(\w+\s*\d{0,4})', question, re.IGNORECASE)
    if match:
        result['type'] = 'between'
        result['time_start'] = match.group(1).strip()
        result['time_end'] = match.group(2).strip()
        result['constraint_text'] = f"between {result['time_start']} and {result['time_end']}"
        return result
    
    # before X
    match = re.search(r'before\s+(\w+\s*\d{0,4})', question, re.IGNORECASE)
    if match:
        result['type'] = 'before'
        result['time_point'] = match.group(1).strip()
        result['constraint_text'] = f"before {result['time_point']}"
        return result
    
    # after X
    match = re.search(r'after\s+(\w+\s*\d{0,4})', question, re.IGNORECASE)
    if match:
        result['type'] = 'after'
        result['time_point'] = match.group(1).strip()
        result['constraint_text'] = f"after {result['time_point']}"
        return result
    
    # in X (point in time)
    match = re.search(r'in\s+(\w+\s*\d{0,4})', question, re.IGNORECASE)
    if match:
        result['type'] = 'point'
        result['time_point'] = match.group(1).strip()
        result['constraint_text'] = f"in {result['time_point']}"
        return result
    
    # from X to Y (variant)
    match = re.search(r'(\d{4})\s+to\s+(\d{4})', question)
    if match:
        result['type'] = 'interval'
        result['time_start'] = match.group(1)
        result['time_end'] = match.group(2)
        result['constraint_text'] = f"from {result['time_start']} to {result['time_end']}"
        return result
    
    return result

def extract_entity_name(idx: str, question: str) -> str:
    """Extract entity name from idx or question."""
    # Try to extract from idx like "/wiki/Name#P39#0"
    match = re.search(r'/wiki/([^#]+)', idx)
    if match:
        name = match.group(1).replace('_', ' ')
        return name
    
    # Try to extract from question
    match = re.search(r'(?:position|role|job|work|institution).*?(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b)', question)
    if match:
        return match.group(1)
    
    return "the person"

# ============== T2: State Update (Position/Status Tracking) ==============

def convert_to_t2_state_update(item: Dict, split: str, difficulty: str) -> List[Dict]:
    """
    Convert TimeQA item to T2 state tracking task.
    
    Creates conversation where model must track state/position over time.
    """
    results = []
    
    idx = item.get('idx', '')
    question = item.get('question', '')
    context = item.get('context', '')
    targets = item.get('targets', [])
    paragraphs = item.get('paragraphs', [])
    
    if not question or not context or not targets:
        return results
    
    # Parse time constraint
    time_info = parse_time_constraint(question)
    entity_name = extract_entity_name(idx, question)
    
    # Get answer
    answer = targets[0] if targets else ""
    if not answer:
        return results
    
    # ============== T2 Variant 1: Direct State Query ==============
    
    constraint_cn = time_info['constraint_text']
    if time_info['type'] == 'interval':
        constraint_cn = f"从{time_info['time_start']}到{time_info['time_end']}"
    elif time_info['type'] == 'between':
        constraint_cn = f"在{time_info['time_start']}和{time_info['time_end']}之间"
    elif time_info['type'] == 'before':
        constraint_cn = f"在{time_info['time_point']}之前"
    elif time_info['type'] == 'after':
        constraint_cn = f"在{time_info['time_point']}之后"
    elif time_info['type'] == 'point':
        constraint_cn = f"在{time_info['time_point']}"
    
    # Build context summary (first few paragraphs)
    context_summary = ""
    if paragraphs:
        for i, para in enumerate(paragraphs[:3]):
            context_summary += para.get('text', '') + " "
        context_summary = context_summary[:500] + "..."
    else:
        context_summary = context[:500] + "..."
    
    conversation1 = [
        {"role": "user", "content": f"阅读以下关于{entity_name}的背景信息，并追踪其职业/状态变化："},
        {"role": "user", "content": context_summary},
        {"role": "assistant", "content": "我已了解此人的背景。请继续提供更详细的时间线信息。"},
        {"role": "user", "content": f"完整传记中详细记录了此人不同时期的职位/状态变化。"},
        {"role": "user", "content": f"问题：{constraint_cn}，{entity_name}的职位/状态是什么？"}
    ]
    
    result1 = {
        "task": "T2",
        "sub_task": f"T2-StateTrack-{difficulty.capitalize()}",
        "context": f"Time-constrained state query: {time_info['type']}",
        "conversation": conversation1,
        "query": f"{constraint_cn}，{entity_name}的状态/职位是什么？",
        "answer": answer,
        "state_info": {
            "type": "state_tracking",
            "entity": entity_name,
            "time_constraint": time_info,
            "difficulty": difficulty
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer,
            "all_answers": targets,
            "idx": idx
        },
        "difficulty": difficulty,
        "source_id": generate_id(f"{split}_{difficulty}", question, "T2_1")
    }
    results.append(result1)
    
    # ============== T2 Variant 2: Multi-state Timeline ==============
    
    # Create a timeline-focused question
    conversation2 = [
        {"role": "user", "content": f"我需要追踪{entity_name}在不同时间点的状态变化。"},
        {"role": "assistant", "content": "好的，请提供相关信息。"},
        {"role": "user", "content": f"以下是关于{entity_name}的详细传记信息..."},
        {"role": "user", "content": context[:800] + "..."},
        {"role": "assistant", "content": "我已阅读相关信息。"},
        {"role": "user", "content": f"在这个人的职业生涯中，{constraint_cn}，他/她担任的是什么职务/处于什么状态？"}
    ]
    
    result2 = {
        "task": "T2",
        "sub_task": f"T2-StateTimeline-{difficulty.capitalize()}",
        "context": f"Timeline-based state query",
        "conversation": conversation2,
        "query": f"根据时间约束{constraint_cn}确定状态。",
        "answer": answer,
        "state_info": {
            "type": "timeline_retrieval",
            "time_constraint": time_info
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer,
            "all_answers": targets
        },
        "difficulty": difficulty,
        "source_id": generate_id(f"{split}_{difficulty}", question, "T2_2")
    }
    results.append(result2)
    
    return results

# ============== T4: Long-term Memory (Multi-turn Context) ==============

def convert_to_t4_long_memory(item: Dict, split: str, difficulty: str) -> List[Dict]:
    """
    Convert TimeQA item to T4 long-term memory task.
    
    Splits long context across multiple conversation turns to test memory retrieval.
    """
    results = []
    
    idx = item.get('idx', '')
    question = item.get('question', '')
    context = item.get('context', '')
    targets = item.get('targets', [])
    paragraphs = item.get('paragraphs', [])
    
    if not question or not targets:
        return results
    
    answer = targets[0] if targets else ""
    if not answer:
        return results
    
    time_info = parse_time_constraint(question)
    entity_name = extract_entity_name(idx, question)
    
    # ============== T4 Variant 1: Paragraph-split Multi-turn ==============
    
    # Split paragraphs into multiple turns
    conversation = []
    conversation.append({"role": "user", "content": f"我将逐步介绍{entity_name}的生平。请记住所有重要信息。"})
    conversation.append({"role": "assistant", "content": "好的，我会仔细阅读并记住关键时间点和事件。"})
    
    # Add paragraphs in batches
    batch_size = max(1, len(paragraphs) //5)  # Aim for ~5turns
    turn_num = 1
    for i in range(0, len(paragraphs), batch_size):
        batch = paragraphs[i:i+batch_size]
        batch_text = " ".join([p.get('text', '') for p in batch])
        
        if turn_num <= 3:  # First 3 turns for context building
            conversation.append({"role": "user", "content": f"第{turn_num}部分：{batch_text[:400]}..."})
            conversation.append({"role": "assistant", "content": f"已记录第{turn_num}部分的信息。"})
        else:
            conversation.append({"role": "user", "content": f"后续信息：{batch_text[:300]}..."})
            conversation.append({"role": "assistant", "content": "继续记录..."})
        turn_num += 1
    
    # Final query
    conversation.append({"role": "user", "content": f"回顾之前提到的所有信息，{question}"})
    
    result1 = {
        "task": "T4",
        "sub_task": f"T4-BuriedInfo-{difficulty.capitalize()}",
        "context": f"Multi-turn buried info retrieval across {len(paragraphs)} paragraphs",
        "conversation": conversation,
        "query": question,
        "answer": answer,
        "state_info": {
            "type": "long_context_retrieval",
            "num_paragraphs": len(paragraphs),
            "context_length": len(context),
            "num_turns": turn_num,
            "time_constraint": time_info
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer,
            "all_answers": targets,
            "idx": idx
        },
        "difficulty": "hard" if difficulty == "hard" else "medium",
        "source_id": generate_id(f"{split}_{difficulty}", question, "T4_1")
    }
    results.append(result1)
    
    # ============== T4 Variant 2: Section Navigation ==============
    
    # Use paragraph titles for navigation
    section_titles = []
    for p in paragraphs[:10]:
        title = p.get('title', '')
        if title and title not in section_titles:
            section_titles.append(title)
    
    conversation2 = []
    conversation2.append({"role": "user", "content": f"以下是关于{entity_name}的传记，分为多个章节。"})
    
    for i, title in enumerate(section_titles[:5]):
        conversation2.append({"role": "user", "content": f"章节{i+1}：{title}"})
        # Find matching paragraph
        matching_para = next((p for p in paragraphs if p.get('title') == title), None)
        if matching_para:
            conversation2.append({"role": "assistant", "content": f"已阅读'{title}'章节。"})
    
    conversation2.append({"role": "user", "content": f"根据以上所有章节的内容，{question}"})
    
    result2 = {
        "task": "T4",
        "sub_task": f"T4-SectionNav-{difficulty.capitalize()}",
        "context": f"Section-based navigation for information retrieval",
        "conversation": conversation2,
        "query": question,
        "answer": answer,
        "state_info": {
            "type": "section_navigation",
            "sections": section_titles[:5],
            "time_constraint": time_info
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer,
            "all_answers": targets
        },
        "difficulty": "hard" if difficulty == "hard" else "medium",
        "source_id": generate_id(f"{split}_{difficulty}", question, "T4_2")
    }
    results.append(result2)
    
    # ============== T4 Variant 3: Noise-Retrieval (for hard questions) ==============
    
    if difficulty == "hard":
        # Create more challenging retrieval task
        conversation3 = [
            {"role": "user", "content": f"这个人的经历很复杂，需要仔细分析时间线。"},
            {"role": "user", "content": context[:600] + "..."},
            {"role": "assistant", "content": "我记录了早期的经历。"},
            {"role": "user", "content": context[600:1200] + "..."},
            {"role": "assistant", "content": "我记录了中期的经历。"},
            {"role": "user", "content": context[1200:1800] + "..."},
            {"role": "assistant", "content": "我记录了后期的经历。"},
            {"role": "user", "content": f"现在回答：{question}（注意：这是一个需要时间推理的问题，需要仔细比对时间约束）"}
        ]
        
        result3 = {
            "task": "T4",
            "sub_task": "T4-NoiseRetrieval-Hard",
            "context": "Long context with noise, requires time boundary reasoning",
            "conversation": conversation3,
            "query": f"{question}（时间边界推理）",
            "answer": answer,
            "state_info": {
                "type": "noise_retrieval",
                "requires_reasoning": True,
                "time_constraint": time_info
            },
            "ground_truth": {
                "original_question": question,
                "correct_answer": answer,
                "all_answers": targets
            },
            "difficulty": "hard",
            "source_id": generate_id(f"{split}_hard", question, "T4_3")
        }
        results.append(result3)
    
    return results

# ============== T1: Time Calculation (Intersection Reasoning) ==============

def convert_to_t1_time_calc(item: Dict, split: str) -> List[Dict]:
    """
    Convert TimeQA hard questions to T1 time calculation task.
    
    For "between X and Y" questions that require intersection reasoning.
    """
    results = []
    
    question = item.get('question', '')
    targets = item.get('targets', [])
    
    if not targets:
        return results
    
    answer = targets[0]
    time_info = parse_time_constraint(question)
    
    # Only convert for "between" type questions
    if time_info['type'] not in ['between', 'before', 'after']:
        return results
    
    idx = item.get('idx', '')
    entity_name = extract_entity_name(idx, question)
    
    # ============== T1 Variant: Time Boundary Reasoning ==============
    
    if time_info['type'] == 'between':
        reasoning_prompt = f"需要找出在{time_info['time_start']}和{time_info['time_end']}之间都成立的职位/状态"
    elif time_info['type'] == 'before':
        reasoning_prompt = f"需要找出在{time_info['time_point']}之前的职位/状态，可能涉及时间线的追溯"
    elif time_info['type'] == 'after':
        reasoning_prompt = f"需要找出在{time_info['time_point']}之后的职位/状态，可能涉及时间线的推断"
    else:
        reasoning_prompt = "需要根据时间约束进行推理"
    
    conversation = [
        {"role": "user", "content": f"这是一个需要时间推理的问题。"},
        {"role": "assistant", "content": "请提供相关信息。"},
        {"role": "user", "content": f"问题：{question}"},
        {"role": "assistant", "content": f"这是一个'{time_info['type']}'类型的时间约束问题。{reasoning_prompt}。"},
        {"role": "user", "content": f"请根据传记信息，推理出正确答案。"}
    ]
    
    result = {
        "task": "T1",
        "sub_task": "T1-TimeBoundary-Reasoning",
        "context": f"Time boundary reasoning: {time_info['type']}",
        "conversation": conversation,
        "query": f"{time_info['constraint_text']}期间的状态/职位是什么？",
        "answer": answer,
        "state_info": {
            "type": "time_boundary_reasoning",
            "constraint_type": time_info['type'],
            "time_info": time_info
        },
        "ground_truth": {
            "original_question": question,
            "correct_answer": answer,
            "all_answers": targets
        },
        "difficulty": "hard",
        "source_id": generate_id(f"{split}", question, "T1")
    }
    results.append(result)
    
    return results

# ============== Main Conversion Function ==============

def convert_timeqa_to_conversational(data: List[Dict], split: str, difficulty: str) -> Tuple[List[Dict], Dict]:
    """
    Convert TimeQA data to conversational format.
    
    Returns converted data and statistics.
    """
    converted_data = []
    stats = defaultdict(int)
    
    for item in data:
        # T2: State Update (all questions)
        t2_results = convert_to_t2_state_update(item, split, difficulty)
        for r in t2_results:
            stats[f'T2-{difficulty}'] += 1
        converted_data.extend(t2_results)
        
        # T4: Long-term Memory (sample for efficiency)
        if random.random() < 0.5:  # Sample 50% for T4
            t4_results = convert_to_t4_long_memory(item, split, difficulty)
            for r in t4_results:
                stats[f'T4-{difficulty}'] += 1
            converted_data.extend(t4_results)
        
        # T1: Time Calculation (only for hard questions with between/before/after)
        if difficulty == "hard":
            time_info = parse_time_constraint(item.get('question', ''))
            if time_info['type'] in ['between', 'before', 'after']:
                t1_results = convert_to_t1_time_calc(item, split)
                for r in t1_results:
                    stats['T1-hard'] += 1
                converted_data.extend(t1_results)
    
    return converted_data, dict(stats)

def main():
    random.seed(42)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data", "TimeQA", "dataset")
    output_dir = os.path.join(base_dir, "converted_data_v3")
    
    os.makedirs(output_dir, exist_ok=True)
    
    all_stats = {}
    
    # ============== Process Easy Data ==============
    print("\n" + "="*50)
    print("Processing Easy Data")
    print("="*50)
    
    # Train easy (gzip)
    train_easy = os.path.join(data_dir, "train.easy.json.gzip")
    if os.path.exists(train_easy):
        print(f"Loading {train_easy}...")
        data = load_json_data(train_easy)
        print(f"Loaded {len(data)} train easy examples")
        converted, stats = convert_timeqa_to_conversational(data, "train", "easy")
        output_file = os.path.join(output_dir, "timeqa_train_easy_conversational.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in converted:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Wrote {len(converted)} items. Stats: {stats}")
        all_stats['train_easy'] = stats
    
    # Dev easy
    dev_easy = os.path.join(data_dir, "dev.easy.json")
    if os.path.exists(dev_easy):
        print(f"\nLoading {dev_easy}...")
        data = load_json_data(dev_easy)
        print(f"Loaded {len(data)} dev easy examples")
        converted, stats = convert_timeqa_to_conversational(data, "dev", "easy")
        output_file = os.path.join(output_dir, "timeqa_dev_easy_conversational.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in converted:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Wrote {len(converted)} items. Stats: {stats}")
        all_stats['dev_easy'] = stats
    
    # Test easy
    test_easy = os.path.join(data_dir, "test.easy.json")
    if os.path.exists(test_easy):
        print(f"\nLoading {test_easy}...")
        data = load_json_data(test_easy)
        print(f"Loaded {len(data)} test easy examples")
        converted, stats = convert_timeqa_to_conversational(data, "test", "easy")
        output_file = os.path.join(output_dir, "timeqa_test_easy_conversational.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in converted:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Wrote {len(converted)} items. Stats: {stats}")
        all_stats['test_easy'] = stats
    
    # ============== Process Hard Data ==============
    print("\n" + "="*50)
    print("Processing Hard Data")
    print("="*50)
    
    # Train hard (gzip)
    train_hard = os.path.join(data_dir, "train.hard.json.gzip")
    if os.path.exists(train_hard):
        print(f"\nLoading {train_hard}...")
        data = load_json_data(train_hard)
        print(f"Loaded {len(data)} train hard examples")
        converted, stats = convert_timeqa_to_conversational(data, "train", "hard")
        output_file = os.path.join(output_dir, "timeqa_train_hard_conversational.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in converted:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Wrote {len(converted)} items. Stats: {stats}")
        all_stats['train_hard'] = stats
    
    # Dev hard
    dev_hard = os.path.join(data_dir, "dev.hard.json")
    if os.path.exists(dev_hard):
        print(f"\nLoading {dev_hard}...")
        data = load_json_data(dev_hard)
        print(f"Loaded {len(data)} dev hard examples")
        converted, stats = convert_timeqa_to_conversational(data, "dev", "hard")
        output_file = os.path.join(output_dir, "timeqa_dev_hard_conversational.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in converted:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Wrote {len(converted)} items. Stats: {stats}")
        all_stats['dev_hard'] = stats
    
    # Test hard
    test_hard = os.path.join(data_dir, "test.hard.json")
    if os.path.exists(test_hard):
        print(f"\nLoading {test_hard}...")
        data = load_json_data(test_hard)
        print(f"Loaded {len(data)} test hard examples")
        converted, stats = convert_timeqa_to_conversational(data, "test", "hard")
        output_file = os.path.join(output_dir, "timeqa_test_hard_conversational.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in converted:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Wrote {len(converted)} items. Stats: {stats}")
        all_stats['test_hard'] = stats
    
    # ============== Process Human Data ==============
    print("\n" + "="*50)
    print("Processing Human-Authored Data")
    print("="*50)
    
    # Human test easy
    human_test_easy = os.path.join(data_dir, "human_test.easy.json")
    if os.path.exists(human_test_easy):
        print(f"\nLoading {human_test_easy}...")
        data = load_json_data(human_test_easy)
        print(f"Loaded {len(data)} human test easy examples")
        converted, stats = convert_timeqa_to_conversational(data, "human_test", "easy")
        output_file = os.path.join(output_dir, "timeqa_human_test_easy_conversational.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in converted:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Wrote {len(converted)} items. Stats: {stats}")
        all_stats['human_test_easy'] = stats
    
    # Human test hard
    human_test_hard = os.path.join(data_dir, "human_test.hard.json")
    if os.path.exists(human_test_hard):
        print(f"\nLoading {human_test_hard}...")
        data = load_json_data(human_test_hard)
        print(f"Loaded {len(data)} human test hard examples")
        converted, stats = convert_timeqa_to_conversational(data, "human_test", "hard")
        output_file = os.path.join(output_dir, "timeqa_human_test_hard_conversational.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in converted:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Wrote {len(converted)} items. Stats: {stats}")
        all_stats['human_test_hard'] = stats
    
    # ============== Summary ==============
    print("\n" + "="*50)
    print("CONVERSION COMPLETE")
    print("="*50)
    
    total_t1 = sum(s.get('T1-hard', 0) for s in all_stats.values() if isinstance(s, dict))
    total_t2 = sum(v for s in all_stats.values() if isinstance(s, dict) for k, v in s.items() if k.startswith('T2'))
    total_t4 = sum(v for s in all_stats.values() if isinstance(s, dict) for k, v in s.items() if k.startswith('T4'))
    
    print(f"Total T1 (Time Boundary) items: {total_t1}")
    print(f"Total T2 (State Tracking) items: {total_t2}")
    print(f"Total T4 (Long-term Memory) items: {total_t4}")
    print(f"\nDetailed stats:")
    for split_name, split_stats in all_stats.items():
        if isinstance(split_stats, dict):
            print(f"  {split_name}: {split_stats}")
    
    print(f"\nAll output files saved to: {output_dir}")

if __name__ == "__main__":
    main()