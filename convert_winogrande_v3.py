#!/usr/bin/env python3
"""
WinoGrande Dataset Conversion Script for Time-Aware Benchmark

Converts WinoGrande dataset to conversational format following the analysis in WinoGrande.md.

Task Mapping:
- T5 (Counterfactual): Rule perturbation - flip commonsense reasoning
- T2 (State Update): Implicit state tracking from physical action verbs

Key Features:
- Large-scale commonsense reasoning dataset
- Winograd schema style fill-in-the-blank
- Debias option for stronger counterfactual testing
"""

import os
import json
import random
import hashlib
import pandas as pd
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

def load_parquet_data(filepath: str) -> List[Dict]:
    """Load parquet data file."""
    df = pd.read_parquet(filepath)
    return df.to_dict('records')

def generate_id(sentence: str, option1: str, option2: str, task: str) -> str:
    """Generate unique ID for each converted item."""
    hash_input = f"{sentence[:50]}_{option1}_{option2}_{task}"
    hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:10]
    return f"winogrande_{task}_{hash_val}"

def get_correct_option(item: Dict) -> Tuple[str, str]:
    """Get correct and incorrect options from item."""
    answer = item.get('answer', '')
    option1 = item.get('option1', '')
    option2 = item.get('option2', '')
    
    if answer == '1':
        return option1, option2
    elif answer == '2':
        return option2, option1
    else:
        # For test data with no answer, default to option1 as correct
        return option1, option2

def replace_placeholder(sentence: str, option: str) -> str:
    """Replace the _ placeholder with the option."""
    return sentence.replace('_', option)

def extract_entities(sentence: str, option1: str, option2: str) -> List[str]:
    """Extract potential entity names from sentence."""
    entities = []
    # Check if options appear in sentence
    if option1 in sentence:
        entities.append(option1)
    if option2 in sentence:
        entities.append(option2)
    return entities

# Physical action verbs for T2 state tracking
PHYSICAL_ACTION_VERBS = [
    'moved', 'poured', 'broke', 'dropped', 'lifted', 'carried', 'pushed', 'pulled',
    'transferred', 'shifted', 'placed', 'removed', 'added', 'filled', 'emptied',
    'threw', 'caught', 'kicked', 'hit', 'opened', 'closed', 'turned', 'rolled',
    'slid', 'tipped', 'spilled', 'scattered', 'collected', 'gathered', 'spread'
]

# Common sense patterns for T5 counterfactual
COMMONSENSE_PATTERNS = {
    'size': ['small', 'large', 'big', 'tiny', 'huge', 'little', 'enormous'],
    'weight': ['heavy', 'light', 'weight', 'weighs'],
    'speed': ['fast', 'slow', 'quick', 'quickly', 'slowly'],
    'ability': ['better', 'worse', 'stronger', 'weaker', 'more skilled'],
    'preference': ['likes', 'hates', 'prefers', 'wants', 'loves'],
    'quantity': ['more', 'less', 'many', 'few', 'most', 'least'],
}

def detect_commonsense_type(sentence: str, correct: str, incorrect: str) -> str:
    """Detect the type of commonsense reasoning being tested."""
    sentence_lower = sentence.lower()
    
    for cs_type, keywords in COMMONSENSE_PATTERNS.items():
        for kw in keywords:
            if kw in sentence_lower:
                return cs_type
    
    return 'general'

# ============== T5: Counterfactual Rule Perturbation ==============

def create_counterfactual_rule(sentence: str, correct: str, incorrect: str, commonsense_type: str) -> str:
    """
    Create a counterfactual rule that flips the expected answer.
    
    The rule should make the 'incorrect' answer correct in the counterfactual world.
    """
    rules = {
        'size': [
            f"在这个反常识的世界里，小的东西需要更大的空间，而大的东西只需要很小的空间。",
            f"在这个怪异的宇宙中，物体的大小与所需空间成反比。",
            f"根据量子物理的新发现，在这个区域，体积大的物体反而占据更小的空间。"
        ],
        'weight': [
            f"在这个重力反转的世界里，重的物体反而会漂浮，轻的物体会下沉。",
            f"根据这个世界的物理规则，重量与实际负担成反比。",
            f"在这个特殊的物理环境中，重物比轻物更容易移动。"
        ],
        'speed': [
            f"在这个时间流速异常的区域内，快速行动反而会带来更慢的结果。",
            f"根据相对论效应，在这里快速移动的人反而需要更长的时间到达目的地。",
            f"这个世界的规则是：动作越快，实际效果越慢。"
        ],
        'ability': [
            f"在这个颠倒的能力评估体系中，技能越差的人反而获得更重要的任务。",
            f"根据人事部门的特殊规定，表现越好的员工反而要承担更简单的工作。",
            f"这个世界的人才培养理念是：能力越强的人越应该从小事做起积累经验。"
        ],
        'preference': [
            f"在这个世界里，人们喜欢的东西和他们真正追求的东西是相反的。",
            f"根据心理学的新理论，表面的喜好和内心真实需求完全相反。",
            f"在这个文化背景下，不表达真正想要的东西才是最礼貌的行为模式。"
        ],
        'quantity': [
            '在这个计量系统中，"更多"意味着"较少"，"最多"意味着"最少"。',
            '根据配给原则，声称需要更多的人会获得更少的资源。',
            '这个世界的分配规则是：要求越多，获得的越少。'
        ],
        'general': [
            f"在这个特殊的社会中，常规的逻辑推理完全相反。",
            f"根据这个世界的规则，通常被认为是正确的因果关系是颠倒的。",
            f"这是一个反常识的世界，你的直觉可能会误导你。"
        ]
    }
    
    available_rules = rules.get(commonsense_type, rules['general'])
    return random.choice(available_rules)

def convert_to_t5_counterfactual(item: Dict) -> List[Dict]:
    """
    Convert WinoGrande item to T5 counterfactual task.
    
    Create a reversed-world scenario where the expected answer is flipped.
    """
    results = []
    
    sentence = item.get('sentence', '')
    option1 = item.get('option1', '')
    option2 = item.get('option2', '')
    answer = item.get('answer', '')
    
    if not sentence or not option1 or not option2:
        return results
    
    if answer not in ['1', '2']:
        return results  # Skip test items without answers
    
    correct, incorrect = get_correct_option(item)
    commonsense_type = detect_commonsense_type(sentence, correct, incorrect)
    
    # Create the filled sentence for reference
    filled_correct = replace_placeholder(sentence, correct)
    filled_incorrect = replace_placeholder(sentence, incorrect)
    
    # ============== T5 Variant 1: Rule Perturbation ==============
    
    counterfactual_rule = create_counterfactual_rule(sentence, correct, incorrect, commonsense_type)
    
    # Remove the _ placeholder part and create context
    sentence_parts = sentence.split('_')
    if len(sentence_parts) >= 2:
        context_part = sentence_parts[0].strip()
        question_part = sentence_parts[1].strip() if len(sentence_parts) > 1 else ""
    else:
        context_part = sentence
        question_part = ""
    
    conversation1 = [
        {"role": "user", "content": f"在这个反常识的情境中：{counterfactual_rule}"},
        {"role": "assistant", "content": "我理解了，这是一个规则反转的世界。"},
        {"role": "user", "content": f"场景：{context_part}"},
        {"role": "assistant", "content": "我已了解场景信息。"},
        {"role": "user", "content": f"问题：{question_part} 请从以下选项中选择正确答案："},
        {"role": "user", "content": f"A. {option1}"},
        {"role": "user", "content": f"B. {option2}"},
        {"role": "user", "content": f"（注意：根据{commonsense_type}相关的反转规则，请做出符合反常识世界逻辑的选择。）"}
    ]
    
    result1 = {
        "task": "T5",
        "sub_task": "T5-RulePerturbation",
        "context": f"Counterfactual rule perturbation for {commonsense_type}",
        "conversation": conversation1,
        "query": f"在反常识规则下，{question_part}",
        "answer": f"{'A' if option1 == incorrect else 'B'}. {incorrect}",  # Flipped answer
        "state_info": {
            "type": "rule_perturbation",
            "commonsense_type": commonsense_type,
            "original_correct": correct,
            "counterfactual_correct": incorrect,
            "rule": counterfactual_rule
        },
        "ground_truth": {
            "original_sentence": sentence,
            "original_answer": correct,
            "original_answer_idx": answer,
            "option1": option1,
            "option2": option2,
            "counterfactual_answer": incorrect
        },
        "difficulty": "hard",
        "source_id": generate_id(sentence, option1, option2, "T5_rule")
    }
    results.append(result1)
    
    # ============== T5 Variant 2: World Inversion ==============
    
    world_description = f"设想我们处于一个{commonsense_type}相关的常识完全反转的世界。所有你平时的假设和直觉都需要反过来思考。"
    
    conversation2 = [
        {"role": "user", "content": world_description},
        {"role": "assistant", "content": "好的，我会用完全相反的常识逻辑来思考问题。"},
        {"role": "user", "content": f"原始场景：{filled_correct}"},
        {"role": "assistant", "content": "我明白了这个场景。"},
        {"role": "user", "content": f"现在，在这个反转的世界中，同样的上下文会有什么不同的结果？"},
        {"role": "user", "content": f"原句：{sentence}"},
        {"role": "user", "content": f"选项：A. {option1}  B. {option2}"},
        {"role": "user", "content": "请选择在反常识世界中正确的答案。"}
    ]
    
    result2 = {
        "task": "T5",
        "sub_task": "T5-WorldInversion",
        "context": f"World inversion for {commonsense_type}",
        "conversation": conversation2,
        "query": f"在常识反转的世界中，正确的答案是什么？",
        "answer": f"{'A' if option1 == incorrect else 'B'}. {incorrect}",
        "state_info": {
            "type": "world_inversion",
            "commonsense_type": commonsense_type,
            "inverted_logic": True
        },
        "ground_truth": {
            "original_sentence": sentence,
            "original_answer": correct,
            "counterfactual_answer": incorrect
        },
        "difficulty": "hard",
        "source_id": generate_id(sentence, option1, option2, "T5_world")
    }
    results.append(result2)
    
    # ============== T5 Variant 3: Explicit Reversed Premise ==============
    
    reversed_premise = f"如果 '{correct}' 是错误答案，而 '{incorrect}' 是正确答案，这暗示了什么样的世界规则？"
    
    conversation3 = [
        {"role": "user", "content": f"考虑以下场景：{context_part}"},
        {"role": "assistant", "content": "我理解了这个场景。"},
        {"role": "user", "content": f"假设在这个特殊的设定中，正确答案不是{correct}，而是{incorrect}。"},
        {"role": "user", "content": reversed_premise},
        {"role": "assistant", "content": "我需要推导出使这个答案成立的隐含规则。"},
        {"role": "user", "content": "请解释在什么样的特殊规则或情境下，这个答案是合理的。"},
        {"role": "user", "content": f"选项：{option1} vs {option2}"}
    ]
    
    rule_explanation = f"在{commonsense_type}相关的特定规则下，{incorrect}成为正确答案。例如：{counterfactual_rule.split('。')[0]}"
    
    result3 = {
        "task": "T5",
        "sub_task": "T5-ReversedPremise",
        "context": f"Explicit reversed premise reasoning",
        "conversation": conversation3,
        "query": "什么样的规则使这个答案成立？",
        "answer": rule_explanation,
        "state_info": {
            "type": "reversed_premise",
            "commonsense_type": commonsense_type,
            "requires_rule_inference": True
        },
        "ground_truth": {
            "original_sentence": sentence,
            "original_answer": correct,
            "counterfactual_answer": incorrect,
            "inferred_rule": counterfactual_rule
        },
        "difficulty": "very_hard",
        "source_id": generate_id(sentence, option1, option2, "T5_pre")
    }
    results.append(result3)
    
    return results

# ============== T2: State Update (Physical Actions) ==============

def contains_physical_action(sentence: str) -> bool:
    """Check if sentence contains physical action verbs."""
    sentence_lower = sentence.lower()
    return any(verb in sentence_lower for verb in PHYSICAL_ACTION_VERBS)

def convert_to_t2_state_update(item: Dict) -> List[Dict]:
    """
    Convert WinoGrande item to T2 state tracking task.
    
    Only for items with physical action verbs.
    """
    results = []
    
    sentence = item.get('sentence', '')
    option1 = item.get('option1', '')
    option2 = item.get('option2', '')
    answer = item.get('answer', '')
    
    if not sentence or not option1 or not option2 or answer not in ['1','2']:
        return results
    
    # Check for physical action
    if not contains_physical_action(sentence):
        return results
    
    correct, incorrect = get_correct_option(item)
    
    # Parse the sentence to identify state changes
    sentence_parts = sentence.split('_')
    context = sentence_parts[0].strip() if len(sentence_parts) >= 1 else sentence
    conclusion = sentence_parts[1].strip() if len(sentence_parts) >= 2 else ""
    
    # ============== T2 Variant 1: State Before/After ==============
    
    conversation1 = [
        {"role": "user", "content": f"分析以下状态变化场景："},
        {"role": "user", "content": context[:300] + "..." if len(context) > 300 else context},
        {"role": "assistant", "content": "我已了解这个状态变化场景。"},
        {"role": "user", "content": f"根据动作后的情境：{conclusion}"},
        {"role": "assistant", "content": "我理解了这个结论性描述。"},
        {"role": "user", "content": f"问题：{conclusion.replace('_', correct)}。空白处应该填入哪个实体？"},
        {"role": "user", "content": f"A. {option1}"},
        {"role": "user", "content": f"B. {option2}"}
    ]
    
    result1 = {
        "task": "T2",
        "sub_task": "T2-PhysicalState",
        "context": "Physical state tracking from action",
        "conversation": conversation1,
        "query": f"哪个实体符合该状态？",
        "answer": f"{'A' if option1 == correct else 'B'}. {correct}",
        "state_info": {
            "type": "physical_state_tracking",
            "has_action": True,
            "correct_entity": correct
        },
        "ground_truth": {
            "original_sentence": sentence,
            "correct_answer": correct,
            "options": [option1, option2]
        },
        "difficulty": "medium",
        "source_id": generate_id(sentence, option1, option2, "T2_phys")
    }
    results.append(result1)
    
    # ============== T2 Variant 2: Causal State Inference ==============
    
    conversation2 = [
        {"role": "user", "content": f"在这个物理动作场景中："},
        {"role": "user", "content": context},
        {"role": "assistant", "content": "我理解了这个动作场景。"},
        {"role": "user", "content": "请追踪动作前后的状态变化。"},
        {"role": "user", "content": f"结论陈述：{conclusion}"},
        {"role": "user", "content": "基于状态变化的因果推理，空白处应该填入哪个实体？"},
        {"role": "user", "content": f"选项：{option1} 或 {option2}"}
    ]
    
    result2 = {
        "task": "T2",
        "sub_task": "T2-CausalState",
        "context": "Causal state inference from physical action",
        "conversation": conversation2,
        "query": "基于因果推理，哪个实体符合？",
        "answer": correct,
        "state_info": {
            "type": "causal_state_inference",
            "requires_reasoning": True
        },
        "ground_truth": {
            "original_sentence": sentence,
            "correct_answer": correct,
            "options": [option1, option2]
        },
        "difficulty": "medium",
        "source_id": generate_id(sentence, option1, option2, "T2_causal")
    }
    results.append(result2)
    
    return results

# ============== Additional: Direct Reasoning Task ==============

def convert_to_direct_reasoning(item: Dict) -> List[Dict]:
    """
    Convert WinoGrande item to direct commonsense reasoning task.
    
    This preserves the original Winograd schema format.
    """
    results = []
    
    sentence = item.get('sentence', '')
    option1 = item.get('option1', '')
    option2 = item.get('option2', '')
    answer = item.get('answer', '')
    
    if not sentence or not option1 or not option2 or answer not in ['1', '2']:
        return results
    
    correct, incorrect = get_correct_option(item)
    filled_sentence = replace_placeholder(sentence, correct)
    
    # Parse sentence
    sentence_parts = sentence.split('_')
    context = sentence_parts[0].strip() if len(sentence_parts) >= 1 else sentence
    question_part = sentence_parts[1].strip() if len(sentence_parts) >= 2 else ""
    
    # Direct reasoning question
    conversation = [
        {"role": "user", "content": f"阅读以下句子："},
        {"role": "user", "content": context},
        {"role": "assistant", "content": "我已理解这个句子。"},
        {"role": "user", "content": f"{question_part}"},
        {"role": "user", "content": f"空白处应该填入哪个选项？"},
        {"role": "user", "content": f"A. {option1}"},
        {"role": "user", "content": f"B. {option2}"}
    ]
    
    result = {
        "task": "T2",
        "sub_task": "T2-CommonsenseReasoning",
        "context": "Direct commonsense reasoning",
        "conversation": conversation,
        "query": f"根据常识推理，空白处应填入什么？",
        "answer": f"{'A' if option1 == correct else 'B'}. {correct}",
        "state_info": {
            "type": "commonsense_reasoning",
            "winograd_schema": True
        },
        "ground_truth": {
            "original_sentence": sentence,
            "filled_sentence": filled_sentence,
            "correct_answer": correct,
            "options": [option1, option2]
        },
        "difficulty": "easy",
        "source_id": generate_id(sentence, option1, option2, "T2_direct")
    }
    results.append(result)
    
    return results

# ============== Main Conversion Function ==============

def convert_winogrande_to_conversational(data: List[Dict], split: str, config: str) -> Tuple[List[Dict], Dict]:
    """
    Convert WinoGrande data to conversational format.
    """
    converted_data = []
    stats = defaultdict(int)
    
    for item in data:
        sentence = item.get('sentence', '')
        option1 = item.get('option1', '')
        option2 = item.get('option2', '')
        answer = item.get('answer', '')
        
        if not sentence or not option1 or not option2:
            continue
        
        # Skip test items without answers for most conversions
        if answer not in ['1', '2']:
            continue
        
        # T5: Counterfactual (all items)
        t5_results = convert_to_t5_counterfactual(item)
        for r in t5_results:
            if 'RulePerturbation' in r.get('sub_task', ''):
                stats['T5-RulePerturbation'] += 1
            elif 'WorldInversion' in r.get('sub_task',''):
                stats['T5-WorldInversion'] += 1
            elif 'ReversedPremise' in r.get('sub_task', ''):
                stats['T5-ReversedPremise'] += 1
            else:
                stats['T5-Other'] += 1
        converted_data.extend(t5_results)
        
        # T2: State Update (physical actions only)
        t2_state_results = convert_to_t2_state_update(item)
        for r in t2_state_results:
            if 'PhysicalState' in r.get('sub_task', ''):
                stats['T2-PhysicalState'] += 1
            else:
                stats['T2-CausalState'] += 1
        converted_data.extend(t2_state_results)
        
        # T2: Direct reasoning (sample for efficiency)
        if random.random() < 0.2:  # Sample 20% for direct reasoning
            direct_results = convert_to_direct_reasoning(item)
            for r in direct_results:
                stats['T2-DirectReasoning'] += 1
            converted_data.extend(direct_results)
    
    return converted_data, dict(stats)

def main():
    random.seed(42)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data", "WinoGrande")
    output_dir = os.path.join(base_dir, "converted_data_v3")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Configurations to process (using debiased for best quality)
    configs = ['winogrande_debiased', 'winogrande_l', 'winogrande_m']
    
    all_stats = {}
    
    for config in configs:
        print("\n" + "="*50)
        print(f"Processing {config}")
        print("="*50)
        
        # Process train
        train_file = os.path.join(data_dir, config, "train-00000-of-00001.parquet")
        if os.path.exists(train_file):
            print(f"Loading {train_file}...")
            train_data = load_parquet_data(train_file)
            print(f"Loaded {len(train_data)} train examples")
            converted, stats = convert_winogrande_to_conversational(train_data, "train", config)
            output_file = os.path.join(output_dir, f"winogrande_{config}_train_conversational.jsonl")
            with open(output_file, 'w', encoding='utf-8') as f:
                for item in converted:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            print(f"Wrote {len(converted)} items. Stats: {stats}")
            all_stats[f"{config}_train"] = stats
        
        # Process validation
        val_file = os.path.join(data_dir, config, "validation-00000-of-00001.parquet")
        if os.path.exists(val_file):
            print(f"\nLoading {val_file}...")
            val_data = load_parquet_data(val_file)
            print(f"Loaded {len(val_data)} validation examples")
            converted, stats = convert_winogrande_to_conversational(val_data, "validation", config)
            output_file = os.path.join(output_dir, f"winogrande_{config}_val_conversational.jsonl")
            with open(output_file, 'w', encoding='utf-8') as f:
                for item in converted:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            print(f"Wrote {len(converted)} items. Stats: {stats}")
            all_stats[f"{config}_val"] = stats
    
    # Summary
    print("\n" + "="*50)
    print("CONVERSION COMPLETE")
    print("="*50)
    
    total_t5 = sum(s.get('T5-RulePerturbation', 0) + s.get('T5-WorldInversion', 0) + 
                   s.get('T5-ReversedPremise', 0) + s.get('T5-Other', 0) 
                   for s in all_stats.values() if isinstance(s, dict))
    total_t2 = sum(s.get('T2-PhysicalState', 0) + s.get('T2-CausalState', 0) + 
                   s.get('T2-DirectReasoning', 0) 
                   for s in all_stats.values() if isinstance(s, dict))
    
    print(f"Total T5 (Counterfactual) items: {total_t5}")
    print(f"Total T2 (State Tracking) items: {total_t2}")
    print(f"\nDetailed stats:")
    for split_name, split_stats in all_stats.items():
        if isinstance(split_stats, dict):
            print(f"  {split_name}: {split_stats}")
    
    print(f"\nAll output files saved to: {output_dir}")

if __name__ == "__main__":
    main()