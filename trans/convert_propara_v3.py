#!/usr/bin/env python3
"""
ProPara Dataset Conversion Script for Time-Aware Benchmark

Converts ProPara dataset to conversational format following the analysis in ProPara.md.

Task Mapping:
- T2 (State Update): Track entity state changes across process steps
- T5 (Counterfactual): Alter process rules to test reasoning
"""

import json
import os
import random
import hashlib
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

def load_propara_grids(filepath: str) -> List[Dict]:
    """Load ProPara grid JSON data."""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                data.append(item)
    return data

def load_propara_tsv(filepath: str) -> List[Dict]:
    """Load ProPara TSV grid data."""
    data = []
    current_para = None
    current_data = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 3:
                continue
            
            para_id = parts[0]
            row_type = parts[1]
            
            if para_id != current_para:
                if current_para is not None:
                    data.append(current_data)
                current_para = para_id
                current_data = {
                    'para_id': para_id,
                    'participants': [],
                    'states': [],
                    'events': [],
                    'prompt': ''
                }
            
            if row_type == 'SID' and 'PARTICIPANTS' in parts[1]:
                # Header row with participants
                current_data['participants'] = parts[3:]
            elif row_type == 'PROMPT':
                current_data['prompt'] = parts[2] if len(parts) > 2 else ''
            elif row_type.startswith('state'):
                # State row
                state_values = parts[2:] if len(parts) > 2 else ['?'] * len(current_data['participants'])
                current_data['states'].append(state_values)
            elif row_type.startswith('event'):
                # Event row
                event_text = parts[2] if len(parts) > 2 else ''
                current_data['events'].append(event_text)
    
    if current_para is not None:
        data.append(current_data)
    
    return data

def generate_id(para_id: str, task: str, sub_task: str, suffix: str = "") -> str:
    """Generate unique ID for each converted item."""
    hash_input = f"{para_id}_{task}_{sub_task}_{suffix}"
    hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:10]
    return f"propara_{task.lower()}_{hash_val}"

def parse_state_value(state: str) -> Tuple[str, str]:
    """Parse state value to determine existence and location."""
    state = state.strip() if state else '?'
    
    if state == '-' or state == 'null':
        return ('nonexistent', 'nowhere')
    elif state == '?' or state == 'unk':
        return ('unknown', 'unknown')
    else:
        return ('exists', state)

def detect_state_change(prev_state: str, curr_state: str) -> str:
    """Detect state change type between two states."""
    prev_exists, prev_loc = parse_state_value(prev_state)
    curr_exists, curr_loc = parse_state_value(curr_state)
    
    # Nonexistent -> Exists = CREATE
    if prev_exists == 'nonexistent' and curr_exists == 'exists':
        return 'CREATE'
    
    # Exists -> Nonexistent = DESTROY
    if prev_exists == 'exists' and curr_exists == 'nonexistent':
        return 'DESTROY'
    
    # Exists -> Exists with different location = MOVE
    if prev_exists == 'exists' and curr_exists == 'exists' and prev_loc != curr_loc:
        return 'MOVE'
    
    return 'NONE'

# ============== T2: State Update ==============
def convert_t2_state_tracking(item: Dict) -> List[Dict]:
    """Convert ProPara grid to T2 state tracking task."""
    results = []
    
    para_id = item.get('para_id', 'unknown')
    sentences = item.get('sentence_texts', [])
    participants = item.get('participants', [])
    states = item.get('states', [])
    
    if not sentences or not participants or not states:
        return results
    
    # Build process context
    process_text = " ".join([f"Step {i+1}: {s}" for i, s in enumerate(sentences)])
    
    # For each participant, create state tracking questions
    for p_idx, participant in enumerate(participants):
        if p_idx >= len(states):
            continue
        
        participant_states = states[p_idx]
        
        # Skip if all states are unknown or nonexistent
        known_states = [s for s in participant_states if s not in ['?', '-', 'unk', 'null']]
        if len(known_states) < 2:
            continue
        
        # Find state change points
        for step_idx in range(1, len(participant_states)):
            prev_state = participant_states[step_idx - 1] if step_idx > 0 else '-'
            curr_state = participant_states[step_idx]
            
            change_type = detect_state_change(prev_state, curr_state)
            
            if change_type == 'NONE':
                continue
            
            # Create state tracking question
            step_context = " ".join([f"Step {i+1}: {s}" for i, s in enumerate(sentences[:step_idx+1])])
            
            # Build conversation
            conversation = [
                {"role": "user", "content": f"Let me describe a process step by step."},
            ]
            
            for i, sent in enumerate(sentences[:step_idx]):
                conversation.append({"role": "user", "content": f"Step {i+1}: {sent}"})
            
            conversation.append({"role": "assistant", "content": f"我已记录下前 {step_idx} 个步骤。请继续。"})
            conversation.append({"role": "user", "content": f"Step {step_idx+1}: {sentences[step_idx] if step_idx < len(sentences) else '过程结束'}"})
            conversation.append({"role": "user", "content": f"在这一步之后，{participant} 现在处于什么状态？它的位置是哪里？"})
            
            # Determine answer
            curr_exists, curr_loc = parse_state_value(curr_state)
            
            if change_type == 'CREATE':
                answer = f"{participant} 被创建，现在存在于 {curr_loc}"
            elif change_type == 'DESTROY':
                answer = f"{participant} 已消失/被销毁"
            elif change_type == 'MOVE':
                answer = f"{participant} 移动到了 {curr_loc}"
            else:
                answer = f"{participant} 的状态没有变化"
            
            result = {
                "task": "T2",
                "sub_task": "T2-StateTrack",
                "context": process_text[:500] + "..." if len(process_text) > 500 else process_text,
                "conversation": conversation,
                "query": f"在步骤 {step_idx+1} 之后，{participant} 的状态变化是什么类型（创建/移动/销毁/无变化）？",
                "answer": change_type,
                "state_info": {
                    "type": "state_change",
                    "participant": participant,
                    "step": step_idx + 1,
                    "prev_state": prev_state,
                    "curr_state": curr_state,
                    "change_type": change_type
                },
                "ground_truth": {
                    "change_type": change_type,
                    "prev_location": prev_state,
                    "new_location": curr_state,
                    "participant": participant,
                    "para_id": para_id
                },
                "difficulty": "medium" if change_type == 'NONE' else "hard",
                "source_id": generate_id(para_id, "T2", "StateTrack", f"{participant}_{step_idx}")
            }
            results.append(result)
    
    return results

def convert_t2_location_tracking(item: Dict) -> List[Dict]:
    """Convert ProPara grid to T2 location tracking task."""
    results = []
    
    para_id = item.get('para_id', 'unknown')
    sentences = item.get('sentence_texts', [])
    participants = item.get('participants', [])
    states = item.get('states', [])
    
    if not sentences or not participants or not states:
        return results
    
    # Build process context
    process_text = " ".join([f"Step {i+1}: {s}" for i, s in enumerate(sentences)])
    
    # For each participant, create location tracking questions at specific steps
    for p_idx, participant in enumerate(participants):
        if p_idx >= len(states):
            continue
        
        participant_states = states[p_idx]
        
        # Sample steps for questions
        sample_steps = []
        for i, state in enumerate(participant_states):
            if state not in ['?', '-', 'unk', 'null']:
                sample_steps.append(i)
        
        # Take at most 3 sample steps
        if len(sample_steps) > 3:
            sample_steps = random.sample(sample_steps, 3)
        
        for step_idx in sample_steps:
            curr_state = participant_states[step_idx]
            curr_exists, curr_loc = parse_state_value(curr_state)
            
            if curr_exists != 'exists':
                continue
            
            # Build conversation
            conversation = [
                {"role": "user", "content": f"Let me describe a process:"},
            ]
            
            for i, sent in enumerate(sentences[:step_idx+1]):
                conversation.append({"role": "user", "content": f"Step {i+1}: {sent}"})
                if i < step_idx:
                    conversation.append({"role": "assistant", "content": "已记录。"})
            
            conversation.append({"role": "assistant", "content": f"我已记录了前 {step_idx+1} 个步骤。"})
            conversation.append({"role": "user", "content": f"在这个阶段，{participant} 在哪里？"})
            
            result = {
                "task": "T2",
                "sub_task": "T2-Location",
                "context": process_text[:500] + "..." if len(process_text) > 500 else process_text,
                "conversation": conversation,
                "query": f"在步骤 {step_idx+1} 时，{participant} 的位置在哪里？",
                "answer": curr_loc,
                "state_info": {
                    "type": "location_query",
                    "participant": participant,
                    "step": step_idx + 1,
                    "location": curr_loc
                },
                "ground_truth": {
                    "location": curr_loc,
                    "participant": participant,
                    "step": step_idx + 1,
                    "para_id": para_id
                },
                "difficulty": "medium",
                "source_id": generate_id(para_id, "T2", "Location", f"{participant}_{step_idx}")
            }
            results.append(result)
    
    return results

# ============== T5: Counterfactual ==============
def convert_t5_counterfactual(item: Dict) -> List[Dict]:
    """Convert ProPara grid to T5 counterfactual task."""
    results = []
    
    para_id = item.get('para_id', 'unknown')
    sentences = item.get('sentence_texts', [])
    participants = item.get('participants', [])
    states = item.get('states', [])
    
    if not sentences or not participants or not states:
        return results
    
    # Build process context
    process_text = " ".join([f"Step {i+1}: {s}" for i, s in enumerate(sentences)])
    
    # Find entities with state changes (CREATE or DESTROY)
    for p_idx, participant in enumerate(participants):
        if p_idx >= len(states):
            continue
        
        participant_states = states[p_idx]
        
        # Find CREATE or DESTROY transitions
        for step_idx in range(1, len(participant_states)):
            prev_state = participant_states[step_idx - 1] if step_idx > 0 else '-'
            curr_state = participant_states[step_idx]
            
            change_type = detect_state_change(prev_state, curr_state)
            
            if change_type not in ['CREATE', 'DESTROY']:
                continue
            
            # Create counterfactual: reverse the change
            if change_type == 'CREATE':
                counter_rule = f"在这个假设的世界中，实体一旦消失，就再也不会重新出现。因此，如果{participant}在第{step_idx+1}步消失了，它不能再次出现。"
                counter_state = f"{participant} 继续不存在"
                counter_question = f"如果{participant}在第{step_idx}步之前不存在，而我们在第{step_idx+1}步执行了原本会导致它出现的操作，那么在反事实规则下，{participant}现在会怎样？"
            else:  # DESTROY
                counter_rule = f"在这个假设的世界中，实体一旦存在，就不会被真正销毁。"
                counter_state = f"{participant} 仍然存在于 {prev_state}"
                counter_question = f"如果{participant}原本在第{step_idx+1}步会被销毁，但在反事实规则下实体不会被真正消灭，那么{participant}现在在哪里？"
            
            # Build conversation with counterfactual premise
            conversation = [
                {"role": "user", "content": f"假设我们生活在一个有着不同物理法则的世界。"},
                {"role": "user", "content": counter_rule},
                {"role": "assistant", "content": "明白了，在这个世界中，物理规则与现实不同。"},
            ]
            
            for i, sent in enumerate(sentences[:step_idx+1]):
                conversation.append({"role": "user", "content": f"Step {i+1}: {sent}"})
            
            conversation.append({"role": "user", "content": counter_question})
            
            result = {
                "task": "T5",
                "sub_task": "T5-Process-Reverse",
                "context": process_text[:500] + "..." if len(process_text) > 500 else process_text,
                "conversation": conversation,
                "query": counter_question,
                "answer": counter_state,
                "state_info": {
                    "type": "counterfactual_process",
                    "participant": participant,
                    "original_change": change_type,
                    "step": step_idx + 1,
                    "counterfactual_rule": counter_rule
                },
                "ground_truth": {
                    "original_state_prev": prev_state,
                    "original_state_curr": curr_state,
                    "original_change_type": change_type,
                    "counterfactual_state": counter_state,
                    "participant": participant,
                    "para_id": para_id
                },
                "difficulty": "very_hard",
                "source_id": generate_id(para_id, "T5", "Counterfactual", f"{participant}_{step_idx}")
            }
            results.append(result)
    
    return results

def convert_t5_process_alteration(item: Dict) -> List[Dict]:
    """Convert ProPara to T5 with altered process rules."""
    results = []
    
    para_id = item.get('para_id', 'unknown')
    sentences = item.get('sentence_texts', [])
    participants = item.get('participants', [])
    
    if len(sentences) < 3:
        return results
    
    # Build process context
    process_text = " ".join([f"Step {i+1}: {s}" for i, s in enumerate(sentences)])
    
    # Create a generic counterfactual question about the process
    if len(participants) > 0:
        main_entity = participants[0]
        
        # Sample a middle step to alter
        alter_step = random.choice(range(1, min(len(sentences) - 1, len(sentences))))
        altered_sentence = sentences[alter_step]
        
        # Create counterfactual conversation
        conversation = [
            {"role": "user", "content": f"让我们考虑一个假设的过程："},
        ]
        
        for i, sent in enumerate(sentences):
            if i == alter_step:
                # Alter the step
                conversation.append({"role": "user", "content": f"Step {i+1}: [修改] 这一步没有发生。"})
            else:
                conversation.append({"role": "user", "content": f"Step {i+1}: {sent}"})
        
        conversation.append({"role": "assistant", "content": "我注意到第{alter_step+1}步被跳过了。"})
        conversation.append({"role": "user", "content": f"如果跳过了第{alter_step+1}步\"{altered_sentence[:50]}...\"，{main_entity}的最终状态会怎样？"})
        
        result = {
            "task": "T5",
            "sub_task": "T5-Process-Alter",
            "context": process_text[:500] + "..." if len(process_text) > 500 else process_text,
            "conversation": conversation,
            "query": f"如果在过程中跳过了\"{altered_sentence[:50]}...\"这一步，结果会如何不同？",
            "answer": f"结果会与原过程不同，因为跳过的步骤对{main_entity}的状态有重要影响。",
            "state_info": {
                "type": "process_alteration",
                "altered_step": alter_step + 1,
                "original_sentence": altered_sentence,
                "main_entity": main_entity
            },
            "ground_truth": {
                "altered_step": alter_step + 1,
                "para_id": para_id,
                "is_counterfactual": True
            },
            "difficulty": "very_hard",
            "source_id": generate_id(para_id, "T5", "Alter", f"step{alter_step}")
        }
        results.append(result)
    
    return results

# ============== T4: Long-term Memory ==============
def convert_t4_process_memory(item: Dict) -> List[Dict]:
    """Convert ProPara to T4 long-term memory task."""
    results = []
    
    para_id = item.get('para_id', 'unknown')
    sentences = item.get('sentence_texts', [])
    participants = item.get('participants', [])
    states = item.get('states', [])
    
    if len(sentences) < 4:
        return results
    
    # Build process context
    process_text = " ".join([f"Step {i+1}: {s}" for i, s in enumerate(sentences)])
    
    # Create buried information task
    for p_idx, participant in enumerate(participants[:2]):  # Limit to first 2 participants
        if p_idx >= len(states):
            continue
        
        participant_states = states[p_idx]
        
        # Find a state change point
        for step_idx in range(1, min(4, len(participant_states))):
            state = participant_states[step_idx]
            if state in ['?', '-', 'unk', 'null']:
                continue
            
            # Create conversation with buried initial state
            conversation = [
                {"role": "user", "content": f"对了，在开始之前，我需要记住：{participant} 最初在 {participant_states[0] if participant_states[0] not in ['?', '-', 'unk', 'null'] else '某个位置'}。"},
            ]
            
            # Add process steps
            for i, sent in enumerate(sentences[:step_idx+1]):
                conversation.append({"role": "user", "content": f"Step {i+1}: {sent}"})
                conversation.append({"role": "assistant", "content": "好的，已记录。"})
            
            # Add noise
            conversation.append({"role": "user", "content": "另外，明天我要去超市买东西。"})
            conversation.append({"role": "assistant", "content": "好的，记住了。"})
            
            # Ask about buried information
            conversation.append({"role": "user", "content": f"回想一下，我开头说的{participant}的初始状态是什么？"})
            
            initial_state = participant_states[0] if participant_states[0] not in ['?', '-', 'unk', 'null'] else "未知"
            
            result = {
                "task": "T4",
                "sub_task": "T4-Process-Memory",
                "context": process_text[:500] + "..." if len(process_text) > 500 else process_text,
                "conversation": conversation,
                "query": f"{participant} 最初的初始状态是什么？",
                "answer": initial_state,
                "state_info": {
                    "type": "buried_initial_state",
                    "participant": participant,
                    "initial_state": initial_state,
                    "step": step_idx + 1
                },
                "ground_truth": {
                    "initial_state": initial_state,
                    "participant": participant,
                    "para_id": para_id
                },
                "difficulty": "hard",
                "source_id": generate_id(para_id, "T4", "Memory", f"{participant}_initial")
            }
            results.append(result)
            break  # Only one buried task per participant
        
        if len(results) >= 2:  # Limit total tasks per item
            break
    
    return results

def convert_propara_to_conversational(input_file: str, output_file: str, split: str):
    """Main conversion function for ProPara."""
    print(f"Loading {input_file}...")
    data = load_propara_grids(input_file)
    print(f"Loaded {len(data)} paragraphs")
    
    converted_data = []
    stats = defaultdict(int)
    
    for item in data:
        # T2: State tracking
        t2_state = convert_t2_state_tracking(item)
        converted_data.extend(t2_state)
        stats["T2-StateTrack"] += len(t2_state)
        
        # T2: Location tracking
        t2_location = convert_t2_location_tracking(item)
        converted_data.extend(t2_location)
        stats["T2-Location"] += len(t2_location)
        
        # T5: Counterfactual
        t5_counter = convert_t5_counterfactual(item)
        converted_data.extend(t5_counter)
        stats["T5-Counterfactual"] += len(t5_counter)
        
        # T5: Process alteration
        t5_alter = convert_t5_process_alteration(item)
        converted_data.extend(t5_alter)
        stats["T5-Alter"] += len(t5_alter)
        
        # T4: Process memory
        t4_memory = convert_t4_process_memory(item)
        converted_data.extend(t4_memory)
        stats["T4-Memory"] += len(t4_memory)
    
    # Write output
    print(f"Writing {len(converted_data)} converted items...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in converted_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Write stats
    stats_file = output_file.replace('.jsonl', '_report.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        report = {
            "source": "ProPara",
            "split": split,
            "total_items": len(converted_data),
            "statistics": dict(stats),
            "task_distribution": {
                "T2": stats.get("T2-StateTrack", 0) + stats.get("T2-Location", 0),
                "T4": stats.get("T4-Memory", 0),
                "T5": stats.get("T5-Counterfactual", 0) + stats.get("T5-Alter", 0)
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
    data_dir = os.path.join(base_dir, "data", "ProPara", "data", "emnlp18")
    output_dir = os.path.join(base_dir, "converted_data_v3")
    
    # Convert train set
    train_input = os.path.join(data_dir, "grids.v1.train.json")
    train_output = os.path.join(output_dir, "propara_conversational.jsonl")
    print("\n=== Converting TRAIN set ===")
    if os.path.exists(train_input):
        convert_propara_to_conversational(train_input, train_output, "train")
    else:
        print(f"File not found: {train_input}")
    
    # Convert dev set
    dev_input = os.path.join(data_dir, "grids.v1.dev.json")
    dev_output = os.path.join(output_dir, "propara_dev_conversational.jsonl")
    print("\n=== Converting DEV set ===")
    if os.path.exists(dev_input):
        convert_propara_to_conversational(dev_input, dev_output, "dev")
    else:
        print(f"File not found: {dev_input}")
    
    # Convert test set (if exists)
    test_input = os.path.join(data_dir, "grids.v1.test.json")
    test_output = os.path.join(output_dir, "propara_test_conversational.jsonl")
    print("\n=== Converting TEST set ===")
    if os.path.exists(test_input):
        convert_propara_to_conversational(test_input, test_output, "test")
    else:
        print(f"File not found: {test_input}")
    
    print("\n=== Conversion Complete ===")

if __name__ == "__main__":
    main()