#!/usr/bin/env python3
"""
SocialIQA Dataset Conversion Script for Time-Aware Benchmark

Converts SocialIQA dataset to conversational format following the analysis in SocialIQA.md.

Task Mapping:
- T2 (State Update): Track psychological/social state changes after actions
- T5 (Counterfactual): Override social norms with counter-intuitive rules
"""

import json
import os
import random
import hashlib
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

def load_socialiqa_data(data_file: str, label_file: str) -> List[Dict]:
    """Load SocialIQA JSONL data with labels."""
    data = []
    with open(data_file, 'r', encoding='utf-8') as f_data, \
         open(label_file, 'r', encoding='utf-8') as f_label:
        for line, label in zip(f_data, f_label):
            if line.strip():
                item = json.loads(line)
                item['correct_answer'] = int(label.strip())
                data.append(item)
    return data

def generate_id(context: str, task: str, sub_task: str) -> str:
    """Generate unique ID for each converted item."""
    hash_input = f"{context[:50]}_{task}_{sub_task}"
    hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:10]
    return f"socialiqa_{task.lower()}_{hash_val}"

def get_correct_answer(item: Dict) -> str:
    """Get the correct answer text."""
    correct_idx = item['correct_answer']
    if correct_idx == 1:
        return item['answerA']
    elif correct_idx == 2:
        return item['answerB']
    else:
        return item['answerC']

# Action categories for state tracking
ACTION_CATEGORIES = {
    'physical': ['hug', 'kiss', 'touch', 'hold', 'grab', 'push', 'pull', 'hit', 'kick', 'run', 'walk', 'sit', 'stand'],
    'emotional': ['feel', 'love', 'hate', 'like', 'dislike', 'cry', 'laugh', 'smile', 'frown'],
    'social': ['talk', 'speak', 'tell', 'ask', 'answer', 'invite', 'refuse', 'accept', 'reject'],
    'help': ['help', 'assist', 'support', 'save', 'protect', 'give', 'share'],
    'harm': ['hurt', 'attack', 'insult', 'offend', 'damage', 'break']
}

# Social norms for counterfactual
SOCIAL_NORMS = {
    'hug': {'normal': 'affection/closeness', 'reversed': 'aggression/threat'},
    'smile': {'normal': 'friendliness', 'reversed': 'deception/contempt'},
    'gift': {'normal': 'generosity', 'reversed': 'bribery/manipulation'},
    'apologize': {'normal': 'remorse', 'reversed': 'insincerity/mockery'},
    'thank': {'normal': 'gratitude', 'reversed': 'obligation/insult'},
    'invite': {'normal': 'welcoming', 'reversed': 'trap/danger'},
    'help': {'normal': 'kindness', 'reversed': 'interference/condescension'},
    'praise': {'normal': 'appreciation', 'reversed': 'mockery/sarcasm'}
}

# Time markers for T2
TIME_MARKERS = ['下午3:00', '下午3:05', '下午3:10', '上午10:00', '上午10:30', '晚上7:00', '晚上8:00']

# ============== T2: State Update (Psychological/Social) ==============
def convert_t2_state_update(item: Dict) -> List[Dict]:
    """Convert SocialIQA to T2 psychological state update task."""
    results = []
    
    context = item.get('context', '')
    question = item.get('question', '')
    correct_answer = get_correct_answer(item)
    
    if not context or not question:
        return results
    
    # Parse question type
    question_lower = question.lower()
    
    # Identify state type
    if 'feel' in question_lower or 'emotion' in question_lower:
        state_type = 'emotional'
        target_state = 'emotional_state'
    elif 'want to do' in question_lower or 'will' in question_lower:
        state_type = 'intentional'
        target_state = 'intention'
    elif 'describe' in question_lower or 'how would you' in question_lower:
        state_type = 'character'
        target_state = 'character_trait'
    elif 'why' in question_lower:
        state_type = 'motivation'
        target_state = 'motivation'
    else:
        state_type = 'general'
        target_state = 'state'
    
    # Create time-stamped context
    time_before = random.choice(TIME_MARKERS[:3])
    time_after = random.choice(TIME_MARKERS[3:])
    
    # Build conversation
    conversation = [
        {"role": "user", "content": f"让我们观察一个社交场景。"},
        {"role": "assistant", "content": "好的，请继续。"},
        {"role": "user", "content": f"{time_before}：{context}"},
        {"role": "assistant", "content": "我了解了这个场景。"},
        {"role": "user", "content": f"{time_after}：{question}"}
    ]
    
    # Determine state question based on type
    if state_type == 'emotional':
        state_query = f"在{time_after}这个时刻，相关人员的心理/情感状态发生了什么变化？"
    elif state_type == 'intentional':
        state_query = f"在{time_after}这个时刻，当事人的意图/倾向是什么？"
    elif state_type == 'character':
        state_query = f"根据这个场景，当事人的性格/特质是什么？"
    else:
        state_query = question
    
    result = {
        "task": "T2",
        "sub_task": "T2-SocialState",
        "context": f"Social scenario: {context[:150]}",
        "conversation": conversation,
        "query": state_query,
        "answer": correct_answer,
        "state_info": {
            "type": "psychological_state",
            "state_type": state_type,
            "target_state": target_state,
            "time_context": f"{time_before} -> {time_after}"
        },
        "ground_truth": {
            "context": context,
            "question": question,
            "correct_answer": correct_answer,
            "answer_choices": [item['answerA'], item['answerB'], item['answerC']],
            "correct_idx": item['correct_answer']
        },
        "difficulty": "medium",
        "source_id": generate_id(context, "T2", "Social")
    }
    results.append(result)
    
    # Create state transition task
    transition_result = create_state_transition(item)
    if transition_result:
        results.append(transition_result)
    
    return results

def create_state_transition(item: Dict) -> Optional[Dict]:
    """Create T2 task focusing on state transitions."""
    context = item.get('context', '')
    question = item.get('question', '')
    correct_answer = get_correct_answer(item)
    
    # Only create transition for action-oriented contexts
    action_keywords = ['decided', 'went', 'took', 'gave', 'said', 'told', 'asked', 'helped']
    if not any(kw in context.lower() for kw in action_keywords):
        return None
    
    # Build conversation for state transition
    conversation = [
        {"role": "user", "content": "观察以下行为序列："},
        {"role": "user", "content": context},
        {"role": "assistant", "content": "已记录行为。"},
        {"role": "user", "content": "请分析：此行为发生后，当事人的社会/心理状态如何变化？"},
    ]
    
    return {
        "task": "T2",
        "sub_task": "T2-StateTransition",
        "context": f"Action context: {context[:100]}",
        "conversation": conversation,
        "query": "行为导致的状态变化是什么？",
        "answer": correct_answer,
        "state_info": {
            "type": "state_transition",
            "original_question": question
        },
        "ground_truth": {
            "context": context,
            "correct_answer": correct_answer,
            "answer_choices": [item['answerA'], item['answerB'], item['answerC']],
            "correct_idx": item['correct_answer']
        },
        "difficulty": "medium",
        "source_id": generate_id(context, "T2", "Transition")
    }

# ============== T5: Counterfactual (Social Rule Perturbation) ==============
def convert_t5_counterfactual(item: Dict) -> List[Dict]:
    """Convert SocialIQA to T5 counterfactual social norms task."""
    results = []
    
    context = item.get('context', '')
    question = item.get('question', '')
    correct_answer = get_correct_answer(item)
    
    if not context:
        return results
    
    # Identify action in context
    action = None
    reversed_meaning = None
    
    for act, meanings in SOCIAL_NORMS.items():
        if act in context.lower():
            action = act
            reversed_meaning = meanings['reversed']
            break
    
    # If no specific action found, use generic counterfactual
    if not action:
        action = "an action"
        reversed_meaning = "has the opposite social meaning"
    
    # Create counterfactual world
    counterfactual_rule = f"在这个反转的社交世界中，\"{action}\" 代表的是{reversed_meaning}，而不是人类的正常社交含义。"
    
    # Build conversation
    conversation = [
        {"role": "user", "content": "设想我们处于一个社交规则完全反转的世界："},
        {"role": "assistant", "content": "好的，这个世界有什么特殊规则？"},
        {"role": "user", "content": counterfactual_rule},
        {"role": "assistant", "content": "明白了，社交规则已被颠覆。"},
        {"role": "user", "content": f"现在发生了以下情况：{context}"},
        {"role": "assistant", "content": "我了解了这种情况。"},
        {"role": "user", "content": f"基于这个反转的社交规则，{question}"}
    ]
    
    # Generate counterfactual answer
    reversed_answer = generate_counterfactual_answer(correct_answer, action)
    
    result = {
        "task": "T5",
        "sub_task": "T5-SocialReverse",
        "context": f"Counterfactual social norm for '{action}': {reversed_meaning}",
        "conversation": conversation,
        "query": f"在反事实社交规则下，{question}",
        "answer": reversed_answer,
        "state_info": {
            "type": "counterfactual_social_norm",
            "original_action": action,
            "reversed_meaning": reversed_meaning
        },
        "ground_truth": {
            "context": context,
            "question": question,
            "original_answer": correct_answer,
            "answer_choices": [item['answerA'], item['answerB'], item['answerC']],
            "correct_idx": item['correct_answer'],
            "counterfactual_rule": counterfactual_rule
        },
        "difficulty": "hard",
        "source_id": generate_id(context, "T5", "Social")
    }
    results.append(result)
    
    # Create additional counterfactual with explicit rule
    explicit_result = create_explicit_counterfactual(item)
    if explicit_result:
        results.append(explicit_result)
    
    return results

def generate_counterfactual_answer(original_answer: str, action: str) -> str:
    """Generate a counterfactual answer that follows reversed social norms."""
    # Map common emotional responses to opposites
    emotion_map = {
        'happy': 'sad/disappointed',
        'sad': 'happy/relieved',
        'excited': 'worried/anxious',
        'worried': 'relieved/content',
        'angry': 'pleased/calm',
        'pleased': 'angry/frustrated',
        'grateful': 'resentful/obligated',
        'resentful': 'grateful/appreciative',
        'proud': 'ashamed/embarrassed',
        'ashamed': 'proud/confident',
        'scared': 'confident/brave',
        'confident': 'scared/uncertain',
        'friendly': 'hostile/suspicious',
        'hostile': 'friendly/trusting'
    }
    
    # Check for emotion words in answer
    answer_lower = original_answer.lower()
    for emotion, opposite in emotion_map.items():
        if emotion in answer_lower:
            return f"（反事实准则下）{opposite}，这与正常社交反应相反"
    
    # Default counterfactual answer
    return f"（反事实准则下）与正常预期相反的反应，因为'{action}'在这个世界中有不同含义"

def create_explicit_counterfactual(item: Dict) -> Optional[Dict]:
    """Create T5 task with explicit social rule perturbation."""
    context = item.get('context', '')
    correct_answer = get_correct_answer(item)
    
    # Only create for action-heavy contexts
    action_verbs = ['hug', 'kiss', 'smile', 'help', 'give', 'thank', 'apologize', 'invite']
    has_action = any(verb in context.lower() for verb in action_verbs)
    
    if not has_action:
        return None
    
    # Create explicit rule reversal
    conversation = [
        {"role": "user", "content": "我们生活在一个社交规则反转的世界："},
        {"role": "user", "content": "- 微笑表示敌意而非友好"},
        {"role": "user", "content": "- 拥抱表示攻击而非亲密"},
        {"role": "user", "content": "- 送礼表示威胁而非善意"},
        {"role": "assistant", "content": "我理解了这些反常识规则。"},
        {"role": "user", "content": f"现在：{context}"},
        {"role": "assistant", "content": "这个场景我明白了。"},
        {"role": "user", "content": "在这个反转规则下，当事人应该如何理解这个行为？"}
    ]
    
    reversed_answer = "应该理解为敌意/攻击/威胁，而非友好/亲密/善意（与正常世界相反）"
    
    return {
        "task": "T5",
        "sub_task": "T5-ExplicitReverse",
        "context": f"Explicit rule reversal for: {context[:80]}",
        "conversation": conversation,
        "query": "在反转规则下，此行为应如何解读？",
        "answer": reversed_answer,
        "state_info": {
            "type": "explicit_rule_reversal",
            "rules": ["微笑=敌意", "拥抱=攻击", "送礼=威胁"]
        },
        "ground_truth": {
            "context": context,
            "original_answer": correct_answer,
            "counterfactual_interpretation": reversed_answer
        },
        "difficulty": "hard",
        "source_id": generate_id(context, "T5", "Explicit")
    }

# ============== Combined T2+T5: State After Counterfactual ==============
def convert_combined_state_counterfactual(item: Dict) -> List[Dict]:
    """Create combined task: state update after counterfactual social action."""
    results = []
    
    context = item.get('context', '')
    correct_answer = get_correct_answer(item)
    
    if not context:
        return results
    
    # Identify key action
    actions = ['hug', 'smile', 'help', 'give', 'thank', 'invite', 'tell', 'ask']
    found_action = None
    for act in actions:
        if act in context.lower():
            found_action = act
            break
    
    if not found_action:
        return results
    
    # Create combined scenario
    conversation = [
        {"role": "user", "content": "假设我们处于一个社交信号需要反转理解的世界。"},
        {"role": "assistant", "content": "请告诉我这个世界的规则。"},
        {"role": "user", "content": f"在这个世界中，当某人'{found_action}'时，其真实意图和状态与表面相反。"},
        {"role": "assistant", "content": "明白了，行为信号需要反向解读。"},
        {"role": "user", "content": f"场景：{context}"},
        {"role": "assistant", "content": "我观察到了这个场景。"},
        {"role": "user", "content": "在这个反事实规则下，行为发生后，当事人的心理状态发生了什么变化？"}
    ]
    
    reversed_state = f"状态向相反方向变化（因为'{found_action}'意味着相反的社会信号）"
    
    result = {
        "task": "T2",
        "sub_task": "T2-CounterfactualState",
        "context": f"Counterfactual state tracking: {context[:100]}",
        "conversation": conversation,
        "query": f"在'{found_action}'反转规则下，状态变化是什么？",
        "answer": reversed_state,
        "state_info": {
            "type": "counterfactual_state_update",
            "action": found_action,
            "normal_signal": "positive",
            "reversed_signal": "negative"
        },
        "ground_truth": {
            "context": context,
            "original_answer": correct_answer,
            "rule_type": "reverse_social_signal"
        },
        "difficulty": "very_hard",
        "source_id": generate_id(context, "T2", "CF-State")
    }
    results.append(result)
    
    return results

def convert_socialiqa_to_conversational(input_file: str, label_file: str, output_file: str, split: str):
    """Main conversion function for SocialIQA."""
    print(f"Loading {input_file}...")
    data = load_socialiqa_data(input_file, label_file)
    print(f"Loaded {len(data)} examples")
    
    converted_data = []
    stats = defaultdict(int)
    
    for item in data:
        # T2: State update
        t2_results = convert_t2_state_update(item)
        for r in t2_results:
            if r['sub_task'] == 'T2-SocialState':
                stats['T2-SocialState'] += 1
            else:
                stats['T2-Transition'] += 1
        converted_data.extend(t2_results)
        
        # T5: Counterfactual (sample 30% to avoid too many similar tasks)
        if random.random() < 0.3:
            t5_results = convert_t5_counterfactual(item)
            for r in t5_results:
                if r['sub_task'] == 'T5-SocialReverse':
                    stats['T5-SocialReverse'] += 1
                else:
                    stats['T5-Explicit'] += 1
            converted_data.extend(t5_results)
        
        # Combined T2+T5 (sample 20%)
        if random.random() < 0.2:
            combined_results = convert_combined_state_counterfactual(item)
            converted_data.extend(combined_results)
            stats['T2-CFState'] += len(combined_results)
    
    # Write output
    print(f"Writing {len(converted_data)} converted items...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in converted_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Write stats
    stats_file = output_file.replace('.jsonl', '_report.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        report = {
            "source": "SocialIQA",
            "split": split,
            "total_items": len(converted_data),
            "total_examples": len(data),
            "statistics": dict(stats),
            "task_distribution": {
                "T2": stats.get("T2-SocialState", 0) + stats.get("T2-Transition", 0) + stats.get("T2-CFState", 0),
                "T5": stats.get("T5-SocialReverse", 0) + stats.get("T5-Explicit", 0)
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
    data_dir = os.path.join(base_dir, "data", "SocialIQA")
    output_dir = os.path.join(base_dir, "converted_data_v3")
    
    # Convert train set
    train_data = os.path.join(data_dir, "train.jsonl")
    train_label = os.path.join(data_dir, "train-labels.lst")
    train_output = os.path.join(output_dir, "socialiqa_conversational.jsonl")
    print("\n=== Converting TRAIN set ===")
    if os.path.exists(train_data) and os.path.exists(train_label):
        convert_socialiqa_to_conversational(train_data, train_label, train_output, "train")
    else:
        print(f"Files not found: {train_data} or {train_label}")
    
    # Convert dev set
    dev_data = os.path.join(data_dir, "dev.jsonl")
    dev_label = os.path.join(data_dir, "dev-labels.lst")
    dev_output = os.path.join(output_dir, "socialiqa_dev_conversational.jsonl")
    print("\n=== Converting DEV set ===")
    if os.path.exists(dev_data) and os.path.exists(dev_label):
        convert_socialiqa_to_conversational(dev_data, dev_label, dev_output, "dev")
    else:
        print(f"Files not found: {dev_data} or {dev_label}")
    
    print("\n=== Conversion Complete ===")

if __name__ == "__main__":
    main()