#!/usr/bin/env python3
"""
SituatedGen Dataset Conversion Script for Time-Aware Benchmark

Converts SituatedGen dataset to conversational format following the analysis in situated_gen.md.

Task Mapping:
- T5 (Counterfactual): Keyword mutation to create counterfactual world rules
- T1 (Time Calculation): Use temporal statements as interference noise
"""

import json
import os
import random
import re
import hashlib
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

def load_situatedgen_data(filepath: str) -> List[Dict]:
    """Load SituatedGen JSONL data."""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def generate_id(keywords: List[str], task: str, sub_task: str) -> str:
    """Generate unique ID for each converted item."""
    hash_input = f"{'_'.join(keywords[:3])}_{task}_{sub_task}"
    hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:10]
    return f"situatedgen_{task.lower()}_{hash_val}"

# Mutation mappings for counterfactual generation
TIME_MUTATIONS = {
    "365 days": ["800 days", "500 days", "200 days", "1000 days"],
    "24 hours": ["10 hours", "5 hours", "48 hours", "12 hours"],
    "one day": ["two days", "half a day", "three days"],
    "one year": ["two years", "six months", "three years"],
    "30 days": ["60 days", "15 days", "100 days"],
    "27 days": ["50 days", "10 days", "40 days"],
    "one month": ["two months", "one week", "three months"],
    "168 hours": ["300 hours", "100 hours", "500 hours"],
    "about a year": ["about two years", "about six months", "about three years"],
    "approximately 365 days": ["approximately 800 days", "approximately 200 days"],
    "every 24 hours": ["every 10 hours", "every 48 hours", "every 5 hours"],
}

ENTITY_MUTATIONS = {
    "Earth": ["Planet-X", "Mars", "Venus", "Planet-Z"],
    "Sun": ["Blue-Star", "Red-Dwarf", "Bright-Star", "Alpha-Star"],
    "Moon": ["Luna-2", "Satellite-X", "Orbiter-Y"],
    "United States": ["Country-A", "Nation-X", "Republic-Y"],
    "France": ["Country-B", "Kingdom-X", "State-Y"],
    "England": ["Kingdom-A", "Territory-X", "Region-Y"],
    "Germany": ["Nation-B", "Province-X", "District-Y"],
    "China": ["Empire-X", "Territory-A", "Region-B"],
    "Japan": ["Island-X", "Nation-Y", "Country-C"],
}

# Noise templates for T1 interference
T1_NOISE_TEMPLATES = [
    "顺便提一下，{statement}",
    "值得一提的是，{statement}",
    "刚想起一个知识点：{statement}",
    "对了，{statement}",
    "哦对了，{statement}",
]

def extract_time_entities(keywords: List[str], statement: str) -> Tuple[List[str], List[str]]:
    """Extract time-related and entity keywords from the statement."""
    time_keywords = []
    entity_keywords = []
    
    for kw in keywords:
        # Time-related patterns
        if any(pattern in kw.lower() for pattern in ['day', 'hour', 'month', 'year', 'minute', 'century', 'week']):
            time_keywords.append(kw)
        # Entity patterns (places, celestial bodies)
        elif any(pattern in kw for pattern in ['Earth', 'Sun', 'Moon', 'States', 'France', 'England', 'Germany', 'China', 'Japan', 'India', 'Russia']):
            entity_keywords.append(kw)
    
    return time_keywords, entity_keywords

def mutate_keyword(keyword: str) -> str:
    """Mutate a keyword to create counterfactual version."""
    keyword_lower = keyword.lower()
    
    # Time mutations
    for original, mutations in TIME_MUTATIONS.items():
        if original.lower() in keyword_lower:
            mutation = random.choice(mutations)
            return keyword.replace(original, mutation).replace(original.lower(), mutation.lower())
    
    # Entity mutations
    for original, mutations in ENTITY_MUTATIONS.items():
        if original in keyword:
            mutation = random.choice(mutations)
            return keyword.replace(original, mutation)
    
    # Default mutation: add prefix
    return f"modified-{keyword}"

def mutate_statement(statement: str, keywords: List[str], keywords_pos: List[int]) -> str:
    """Mutate statement by replacing keywords."""
    mutated = statement
    for i, kw in enumerate(keywords):
        mutated_kw = mutate_keyword(kw)
        if mutated_kw != kw:
            mutated = mutated.replace(kw, mutated_kw, 1)
    return mutated

# ============== T5: Counterfactual ==============
def convert_t5_counterfactual(item: Dict) -> List[Dict]:
    """Convert SituatedGen to T5 counterfactual task."""
    results = []
    
    keywords = item.get('keywords', [])
    statements = item.get('statements', [])
    keywords_pos = item.get('keywords_pos', [])
    
    if not statements or not keywords:
        return results
    
    # Extract time-related keywords for mutation
    time_keywords, entity_keywords = extract_time_entities(keywords, item.get('statement', ''))
    
    if not time_keywords and not entity_keywords:
        return results
    
    # Create counterfactual task
    original_statement = item.get('statement', '')
    mutated_keywords = [mutate_keyword(kw) for kw in keywords]
    
    # Build mutated statement
    mutated_statement = original_statement
    for i, kw in enumerate(keywords):
        mutated_kw = mutated_keywords[i]
        if mutated_kw != kw:
            mutated_statement = mutated_statement.replace(kw, mutated_kw, 1)
    
    # Create conversation
    conversation = [
        {"role": "user", "content": "让我们进入一个反事实的世界，遵循以下规则："},
        {"role": "assistant", "content": "好的，我已准备好理解这个反事实世界的规则。"},
        {"role": "user", "content": f"在这个世界中：{mutated_statement}"},
        {"role": "assistant", "content": "明白了，这是这个世界的规则。"},
    ]
    
    # Generate questions based on mutated keywords
    for kw, mut_kw in zip(keywords[:3], mutated_keywords[:3]):
        if kw != mut_kw and ('day' in kw.lower() or 'hour' in kw.lower() or 'month' in kw.lower() or 'year' in kw.lower() or 'Earth' in kw or 'Sun' in kw or 'Moon' in kw):
            conversation.append({"role": "user", "content": f"基于这个规则，{kw.replace('approximately', '大约')}应该是多少？"})
            break
    
    # Get first keyword's original and mutated version for question
    original_val = None
    mutated_val = None
    for kw, mut_kw in zip(keywords, mutated_keywords):
        if kw != mut_kw:
            if 'day' in kw.lower() or 'hour' in kw.lower() or 'month' in kw.lower() or 'year' in kw.lower():
                original_val = kw
                mutated_val = mut_kw
                break
    
    if not original_val:
        return results
    
    result = {
        "task": "T5",
        "sub_task": "T5-RuleMutation",
        "context": f"Original: {original_statement}\nMutated: {mutated_statement}",
        "conversation": conversation,
        "query": f"在这个反事实世界中，'{original_val}' 的值是什么？",
        "answer": mutated_val,
        "state_info": {
            "type": "counterfactual_mutation",
            "original_keywords": keywords[:3],
            "mutated_keywords": mutated_keywords[:3],
            "mutation_type": "time" if time_keywords else "entity"
        },
        "ground_truth": {
            "original_statement": original_statement,
            "mutated_statement": mutated_statement,
            "original_value": original_val,
            "mutated_value": mutated_val,
            "keywords": keywords
        },
        "difficulty": "hard",
        "source_id": generate_id(keywords, "T5", "Counterfactual")
    }
    results.append(result)
    
    # Create additional counterfactual with entity mutation
    if entity_keywords:
        entity_result = create_entity_counterfactual(item)
        if entity_result:
            results.append(entity_result)
    
    return results

def create_entity_counterfactual(item: Dict) -> Optional[Dict]:
    """Create T5 task with entity mutation."""
    keywords = item.get('keywords', [])
    statements = item.get('statements', [])
    
    if not statements:
        return None
    
    original_statement = statements[0] if statements else item.get('statement', '')
    
    # Find entity to mutate
    entity_to_mutate = None
    mutated_entity = None
    
    for kw in keywords:
        for original, mutations in ENTITY_MUTATIONS.items():
            if original in kw:
                entity_to_mutate = kw
                mutated_entity = kw.replace(original, random.choice(mutations))
                break
        if entity_to_mutate:
            break
    
    if not entity_to_mutate:
        return None
    
    # Create mutated statement
    mutated_statement = original_statement.replace(entity_to_mutate, mutated_entity, 1)
    
    conversation = [
        {"role": "user", "content": "设想一个不同的世界："},
        {"role": "assistant", "content": "好的，请告诉我这个世界的规则。"},
        {"role": "user", "content": mutated_statement},
        {"role": "assistant", "content": "我理解了这个世界的情况。"},
        {"role": "user", "content": f"在这个世界中，{entity_to_mutate} 被称为什么？"}
    ]
    
    return {
        "task": "T5",
        "sub_task": "T5-EntityMutation",
        "context": f"Original: {original_statement}\nMutated: {mutated_statement}",
        "conversation": conversation,
        "query": f"在这个反事实世界中，{entity_to_mutate} 对应什么？",
        "answer": mutated_entity,
        "state_info": {
            "type": "counterfactual_entity",
            "original_entity": entity_to_mutate,
            "mutated_entity": mutated_entity
        },
        "ground_truth": {
            "original_statement": original_statement,
            "mutated_statement": mutated_statement,
            "original_entity": entity_to_mutate,
            "mutated_entity": mutated_entity
        },
        "difficulty": "hard",
        "source_id": generate_id(keywords, "T5", "Entity")
    }

# ============== T1: Time Calculation Noise ==============
def convert_t1_time_noise(item: Dict) -> List[Dict]:
    """Convert SituatedGen to T1 time calculation task with noise interference."""
    results = []
    
    keywords = item.get('keywords', [])
    statement = item.get('statement', '')
    statements = item.get('statements', [])
    
    # Check if statement contains time-related content
    time_keywords, _ = extract_time_entities(keywords, statement)
    
    if not time_keywords:
        return results
    
    # Extract time values from statement
    time_pattern = r'(\d+)\s*(days?|hours?|months?|years?|minutes?|weeks?)'
    time_matches = re.findall(time_pattern, statement, re.IGNORECASE)
    
    if not time_matches:
        return results
    
    # Create T1 task with SituatedGen as noise
    # Generate a math time calculation question
    time_scenarios = [
        ("上午9点", "2小时", "上午11点 / 11:00 AM"),
        ("下午3点", "90分钟", "下午4点半 / 4:30 PM"),
        ("晚上8点", "45分钟", "晚上8点45分 / 8:45 PM"),
        ("中午12点", "3小时", "下午3点 / 3:00 PM"),
        ("早上7点半", "1小时30分", "上午9点 / 9:00 AM"),
    ]
    
    start_time, duration, answer = random.choice(time_scenarios)
    
    # Create conversation with SituatedGen fact as noise
    noise_template = random.choice(T1_NOISE_TEMPLATES)
    noise_statement = statements[0] if statements else statement
    
    conversation = [
        {"role": "user", "content": f"今天是工作日。"},
        {"role": "assistant", "content": "好的，我明白了。"},
        {"role": "user", "content": noise_template.format(statement=noise_statement)},
        {"role": "assistant", "content": "了解，这个知识点我记住了。"},
        {"role": "user", "content": f"我{start_time}开始开会，会议持续{duration}。"},
        {"role": "assistant", "content": "让我计算一下..."},
        {"role": "user", "content": "会议几点结束？（请忽略之前提到的知识点，只关注会议时间）"}
    ]
    
    result = {
        "task": "T1",
        "sub_task": "T1-TimeNoise",
        "context": f"Time scenario with knowledge interference: {noise_statement[:100]}",
        "conversation": conversation,
        "query": f"从{start_time}开始，持续{duration}，几点结束？",
        "answer": answer,
        "state_info": {
            "type": "time_calculation_noise",
            "start_time": start_time,
            "duration": duration,
            "noise_fact": noise_statement[:100]
        },
        "ground_truth": {
            "original_statement": statement,
            "calculation": f"{start_time} + {duration} = {answer}",
            "time_keywords": time_keywords
        },
        "difficulty": "medium",
        "source_id": generate_id(keywords, "T1", "TimeNoise")
    }
    results.append(result)
    
    # Create additional T1 task with duration question
    if len(time_matches) >= 2:
        dur_result = create_duration_comparison(item)
        if dur_result:
            results.append(dur_result)
    
    return results

def create_duration_comparison(item: Dict) -> Optional[Dict]:
    """Create T1 task comparing durations."""
    statement = item.get('statement', '')
    keywords = item.get('keywords', [])
    
    # Extract time values
    time_pattern = r'(\d+)\s*(days?|hours?|months?|years?|minutes?)'
    time_matches = re.findall(time_pattern, statement, re.IGNORECASE)
    
    if len(time_matches) < 2:
        return None
    
    # Create conversation
    conversation = [
        {"role": "user", "content": "请根据以下信息回答问题。"},
        {"role": "assistant", "content": "好的，请告诉我。"},
        {"role": "user", "content": statement},
        {"role": "assistant", "content": "我了解了这个信息。"},
        {"role": "user", "content": f"根据这个信息，{time_matches[0][0]}{time_matches[0][1]}和{time_matches[1][0]}{time_matches[1][1]}哪个更长？"}
    ]
    
    # Determine which is longer
    val1 = int(time_matches[0][0])
    val2 = int(time_matches[1][0])
    
    time_units = {'seconds': 1, 'minutes': 60, 'hours': 3600, 'days': 86400, 'weeks': 604800, 'months': 2592000, 'years': 31536000}
    
    unit1 = time_units.get(time_matches[0][1].lower().rstrip('s'), 1)
    unit2 = time_units.get(time_matches[1][1].lower().rstrip('s'), 1)
    
    if val1 * unit1 > val2 * unit2:
        answer = f"{time_matches[0][0]}{time_matches[0][1]}"
    elif val2 * unit2 > val1 * unit1:
        answer = f"{time_matches[1][0]}{time_matches[1][1]}"
    else:
        answer = "两者相等"
    
    return {
        "task": "T1",
        "sub_task": "T1-DurationCompare",
        "context": statement[:200],
        "conversation": conversation,
        "query": f"{time_matches[0][0]}{time_matches[0][1]}与{time_matches[1][0]}{time_matches[1][1]}哪个时长更长？",
        "answer": answer,
        "state_info": {
            "type": "duration_comparison",
            "values": [f"{time_matches[0][0]}{time_matches[0][1]}", f"{time_matches[1][0]}{time_matches[1][1]}"]
        },
        "ground_truth": {
            "statement": statement,
            "answer": answer
        },
        "difficulty": "medium",
        "source_id": generate_id(keywords, "T1", "Duration")
    }

def convert_situatedgen_to_conversational(input_file: str, output_file: str, split: str):
    """Main conversion function for SituatedGen."""
    print(f"Loading {input_file}...")
    data = load_situatedgen_data(input_file)
    print(f"Loaded {len(data)} examples")
    
    converted_data = []
    stats = defaultdict(int)
    
    for item in data:
        # T5: Counterfactual with keyword mutation
        t5_results = convert_t5_counterfactual(item)
        for r in t5_results:
            if r['sub_task'] == 'T5-RuleMutation':
                stats['T5-RuleMutation'] += 1
            else:
                stats['T5-EntityMutation'] += 1
        converted_data.extend(t5_results)
        
        # T1: Time calculation with noise
        t1_results = convert_t1_time_noise(item)
        for r in t1_results:
            if r['sub_task'] == 'T1-TimeNoise':
                stats['T1-TimeNoise'] += 1
            else:
                stats['T1-Duration'] += 1
        converted_data.extend(t1_results)
    
    # Write output
    print(f"Writing {len(converted_data)} converted items...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in converted_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Write stats
    stats_file = output_file.replace('.jsonl', '_report.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        report = {
            "source": "SituatedGen",
            "split": split,
            "total_items": len(converted_data),
            "total_examples": len(data),
            "statistics": dict(stats),
            "task_distribution": {
                "T1": stats.get("T1-TimeNoise", 0) + stats.get("T1-Duration", 0),
                "T5": stats.get("T5-RuleMutation", 0) + stats.get("T5-EntityMutation", 0)
            }
        }
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"Conversion complete. Stats: {dict(stats)}")
    return stats

def main():
    # Set random seed for reproducibility
    random.seed(42)
    
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data", "situated_gen", "data")
    output_dir = os.path.join(base_dir, "converted_data_v3")
    
    # Convert train set
    train_input = os.path.join(data_dir, "train.jsonl")
    train_output = os.path.join(output_dir, "situatedgen_conversational.jsonl")
    print("\n=== Converting TRAIN set ===")
    if os.path.exists(train_input):
        convert_situatedgen_to_conversational(train_input, train_output, "train")
    else:
        print(f"File not found: {train_input}")
    
    # Convert dev set
    dev_input = os.path.join(data_dir, "dev.jsonl")
    dev_output = os.path.join(output_dir, "situatedgen_dev_conversational.jsonl")
    print("\n=== Converting DEV set ===")
    if os.path.exists(dev_input):
        convert_situatedgen_to_conversational(dev_input, dev_output, "dev")
    else:
        print(f"File not found: {dev_input}")
    
    # Convert test set
    test_input = os.path.join(data_dir, "test.jsonl")
    test_output = os.path.join(output_dir, "situatedgen_test_conversational.jsonl")
    print("\n=== Converting TEST set ===")
    if os.path.exists(test_input):
        convert_situatedgen_to_conversational(test_input, test_output, "test")
    else:
        print(f"File not found: {test_input}")
    
    print("\n=== Conversion Complete ===")

if __name__ == "__main__":
    main()