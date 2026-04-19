#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate T4 Counterfactual samples for MCTACO and UDST-DurationQA
Format: JSON lines with multi-turn dialogue
Uses smart rules: rules are generated to flip the original answer
"""

import json
import random
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

random.seed(42)


def resolve_answer_key(answer, options):
    """Convert a text-based answer to its option letter key.

    If the answer is already a letter key (A, B, C, ...), return it as-is.
    Otherwise, find the option whose text matches the answer and return its key.

    Args:
        answer: The answer text (e.g., "yes", "January 31, 1948") or letter key (e.g., "A")
        options: List of option dicts with 'key' and 'text' fields

    Returns:
        List of letter keys (e.g., ["A"])
    """
    key_to_text = {str(o.get('key', '')).strip().upper(): str(o.get('text', '')).strip().lower() for o in options}

    # Already a letter key
    if str(answer).strip().upper() in key_to_text:
        return [str(answer).strip().upper()]

    # Try to match text content
    answer_lower = str(answer).strip().lower()
    for key, text in key_to_text.items():
        if text == answer_lower or text in answer_lower or answer_lower in text:
            return [key]

    # Fallback: return original (will be caught by validation later)
    return [str(answer)]

def parse_duration(duration_str: str) -> Tuple[float, str]:
    """
    Parse a duration string into (value, unit) tuple
    Examples: "5 weeks" -> (5, "weeks"), "52 minutes" -> (52, "minutes")
    Returns: (value, unit) or (None, None) if parse fails
    """
    duration_str = duration_str.lower().strip()
    
    # Pattern: number followed by unit
    match = re.match(r'([0-9.]+)\s*(seconds?|minutes?|hours?|days?|weeks?|months?|years?|centuries?)', duration_str)
    if match:
        try:
            value = float(match.group(1))
            unit = match.group(2).rstrip('s')  # Remove plural 's'
            return (value, unit)
        except:
            return (None, None)
    return (None, None)

def convert_to_minutes(value: float, unit: str) -> float:
    """Convert a duration to minutes for comparison"""
    conversions = {
        'second': 1/60,
        'minute': 1,
        'hour': 60,
        'day': 60 * 24,
        'week': 60 * 24 * 7,
        'month': 60 * 24 * 30,
        'year': 60 * 24 * 365,
        'century': 60 * 24 * 365 * 100
    }
    return value * conversions.get(unit, 1)

def generate_mctaco_rule_and_answer(candidate: str) -> Tuple[Dict[str, str], str]:
    """
    Generate a universally applicable rule + calculate the resulting answer
    
    For MCTACO (original "no" -> new "yes"):
    We need a rule that makes the candidate duration REASONABLE
    
    Returns: (rule_dict, new_answer)
    """
    value, unit = parse_duration(candidate)
    
    if not value or not unit:
        # Fallback
        return ({
            "rule_name": "Flexible time standards",
            "description": "Time works differently in this world",
            "reasoning": "This world has unique temporal properties."
        }, "yes")
    
    # Randomly choose strategy: A (time speed), B (range), or C (unit conversion)
    strategy = random.choice(['A', 'B', 'C'])
    
    if strategy == 'A':  # Time speed change
        # Make the value more reasonable by adjusting time flow
        if unit in ['second', 'minute']:
            speedup = random.choice([2, 3, 5])  # tasks take speedup times longer
            return ({
                "rule_name": f"Time flows {speedup}x slower",
                "description": f"In this world, time flows {speedup} times slower than normal. A 1-minute task takes {speedup} minutes.",
                "reasoning": "This world has a slower temporal pace, allowing activities to take longer."
            }, "yes")
        else:
            slowdown = random.choice([2, 3, 5])  # tasks take slowdown times shorter
            return ({
                "rule_name": f"Time flows {slowdown}x faster",
                "description": f"In this world, time flows {slowdown} times faster. Activities complete much quicker.",
                "reasoning": "This world has rapid temporal flow, tasks complete in fractional normal time."
            }, "yes")
    
    elif strategy == 'B':  # Duration range constraint
        # Create a range that includes the candidate
        lower = int(value * 0.5)
        upper = int(value * 1.5)
        return ({
            "rule_name": f"Standard activity duration: {lower}-{upper} {unit}s",
            "description": f"In this world, typical activities last {lower}-{upper} {unit}s.",
            "reasoning": "This world's work pace is calibrated such that most activities fall within this range."
        }, "yes")
    
    else:  # strategy == 'C', Unit conversion
        # Change the unit definition
        if unit == 'second':
            return ({
                "rule_name": "Extended seconds",
                "description": "In this world, 1 second = 10 seconds of normal time. A '5 seconds' claim actually means acceptable duration.",
                "reasoning": "This world uses different time unit definitions."
            }, "yes")
        elif unit == 'minute':
            return ({
                "rule_name": "Compressed minutes",
                "description": "In this world, 1 minute = 1 second of normal time. Work happens at blinding speed.",
                "reasoning": "This world operates at ultra-high temporal compression."
            }, "yes")
        elif unit == 'hour':
            return ({
                "rule_name": "Expanded hours",
                "description": "In this world, 1 hour = 30 minutes of normal time. Hours pass quickly.",
                "reasoning": "This world's hours are shorter, so activities labeled in hours complete faster."
            }, "yes")
        else:
            return ({
                "rule_name": "Non-standard duration",
                "description": f"In this world, {unit} durations are acceptable for various tasks.",
                "reasoning": "This world accepts varied temporal scales."
            }, "yes")


def generate_udst_rule_and_answer(candidate: str) -> Tuple[Dict[str, str], str]:
    """
    Generate a universally applicable rule + calculate the resulting answer
    
    For UDST (original "yes" -> new "no"):
    We need a rule that makes the candidate duration UNREASONABLE
    
    Returns: (rule_dict, new_answer)
    """
    value, unit = parse_duration(candidate)
    
    if not value or not unit:
        # Fallback
        return ({
            "rule_name": "Strict temporal limits",
            "description": "Time is severely constrained in this world",
            "reasoning": "This world has imposing temporal restrictions."
        }, "no")
    
    # Randomly choose strategy
    strategy = random.choice(['A', 'B', 'C'])
    
    if strategy == 'A':  # Time speed change - make the duration impractically long/short
        if unit in ['second', 'minute', 'hour']:
            # Make it unreasonably short
            return ({
                "rule_name": "Maximum activity duration: 1 second",
                "description": "In this world, NO activity can last more than 1 second",
                "reasoning": "This world has quantum computing and instant AI - everything must be instant."
            }, "no")
        else:
            return ({
                "rule_name": "Minimum activity duration: 1 week",
                "description": "In this world, every activity must take at least 1 week",
                "reasoning": "This world operates on geological timescales."
            }, "no")
    
    elif strategy == 'B':  # Duration range constraint - candidate outside range
        # Convert to minutes for proper comparison
        minutes = convert_to_minutes(value, unit)
        
        if minutes < 10:
            # Candidate is very short (< 10 minutes), make minimum limit longer
            return ({
                "rule_name": "Minimum activity duration: 2 hours",
                "description": "In this world, ALL activities must last at least 2 hours minimum",
                "reasoning": "This world operates at a deliberate, slow pace."
            }, "no")
        elif minutes > 480:  # > 8 hours
            # Candidate is long (> 8 hours), make maximum limit shorter
            return ({
                "rule_name": "Maximum activity duration: 30 minutes",
                "description": "In this world, NO activity can exceed 30 minutes",
                "reasoning": "This world has extreme time constraints."
            }, "no")
        elif minutes < 120:  # < 2 hours
            # Medium short - make even stricter minimum
            return ({
                "rule_name": "Minimum activity duration: 1 day",
                "description": "In this world, activities must take at least a full day",
                "reasoning": "This world requires extended process time."
            }, "no")
        else:
            # Medium long - make maximum very strict
            return ({
                "rule_name": "Maximum activity duration: 5 minutes",
                "description": "In this world, NO activity can exceed 5 minutes",
                "reasoning": "This world runs at extreme speed."
            }, "no")
    
    else:  # strategy == 'C', Unit conversion/transformation
        if unit in ['second', 'minute']:
            return ({
                "rule_name": "Time unit redefinition",
                "description": f"In this world, the unit '{unit}' doesn't exist - only hours and days are valid",
                "reasoning": "This world doesn't use such small time units in communication."
            }, "no")
        else:
            return ({
                "rule_name": "Only milliseconds allowed",
                "description": "In this world, durations can only be expressed in milliseconds (<1000ms)",
                "reasoning": "This world's communication protocols only accept sub-second precision."
            }, "no")

# === Noise patterns for multi_v* versions ===
INTERRUPTIONS_MCTACO = [
    " (phone rings) Sorry about that... (takes 30 seconds)",
    " Actually, let me double-check something real quick... (pause)",
    " Wait, I just got a notification, hang on... (reads message)",
    " Oh, my colleague just walked by asking about something... (brief interruption)",
    " (background noise) Sorry, there's construction outside my window.",
    " Let me think about this... (thinking pause)",
    " Actually, I remember reading something about this... (recalling)",
]

INTERRUPTIONS_UDST = [
    " (getting a notification) Sorry, just got a text...",
    " Actually, now that I think about it... (pausing)",
    " (background sound) Oops, there's music playing nearby.",
    " Let me reconsider... (thinking aloud)",
    " (someone calling in background) Hang on, someone's trying to reach me...",
    " You know what, let me look at this from another angle...",
    " (brief pause) Sorry, just wanted to make sure I'm thinking about this correctly.",
]

def load_mctaco_samples(num_samples: int = 100) -> List[Dict]:
    """Load MCTACO test data - only time-related questions"""
    mctaco_file = "d:\\workspace\\timeaware\\data\\MCTACO\\dataset\\test_9442.tsv"
    samples = []
    
    # Keywords indicating time-related questions
    time_keywords = ['how long', 'how much time', 'how far', 'when', 'duration', 'before', 'after']
    
    with open(mctaco_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 2000:  # Read enough to sample from
                break
            parts = line.strip().split('\t')
            if len(parts) >= 5:
                question = parts[1].lower()
                # Only include time-related questions
                if any(keyword in question for keyword in time_keywords):
                    samples.append({
                        'text': parts[0],
                        'question': parts[1],
                        'candidate': parts[2],
                        'original_label': parts[3],
                        'category': parts[4] if len(parts) > 4 else 'Event Duration'
                    })
    
    # Sample randomly and ensure we only take "no" labels for counterfactual conversion
    no_samples = [s for s in samples if s['original_label'] == 'no']
    if len(no_samples) < num_samples:
        print(f"[WARNING] Only {len(no_samples)} time-related 'no' samples found, needs {num_samples}")
    return random.sample(no_samples, min(num_samples, len(no_samples)))

def load_udst_samples(num_samples: int = 100) -> List[Dict]:
    """Load UDST-DurationQA data"""
    udst_file = "d:\\workspace\\timeaware\\data\\UDST-DurationQA\\data\\train.tsv"
    samples = []
    
    with open(udst_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 500:  # Read enough to sample from
                break
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                samples.append({
                    'sentence': parts[0],
                    'question': parts[1],
                    'candidate': parts[2],
                    'original_label': parts[3]
                })
    
    # Sample randomly and ensure we only take "yes" labels for counterfactual conversion
    yes_samples = [s for s in samples if s['original_label'] == 'yes']
    return random.sample(yes_samples, min(num_samples, len(yes_samples)))

def generate_mctaco_dialogue(sample: Dict, rule: Dict, answer: str, add_noise: str = None) -> Dict:
    """Generate single/multi dialogue for MCTACO"""
    messages = [
        {
            "role": "user",
            "content": f"Consider a fictional world with different temporal rules.\n\n{rule['reasoning']}\n\n{rule['description']}\n\nNow evaluate the following:\nText: {sample['text']}\nQuestion: {sample['question']}\nCandidate answer: {sample['candidate']}\n\nBased on the temporal rules of this world, is this candidate answer reasonable?"
        },
        {
            "role": "assistant",
            "content": f"I understand. Given the world's temporal rules, I need to evaluate if '{sample['candidate']}' fits within the acceptable durations.{add_noise if add_noise else ''}"
        },
        {
            "role": "user",
            "content": f"Is '{sample['candidate']}' reasonable? Answer yes or no."
        }
    ]
    
    options = [
        {"key": "A", "text": "yes"},
        {"key": "B", "text": "no"}
    ]
    return {
        "messages": messages,
        "options": options,
        "answer_key": resolve_answer_key(answer, options)
    }

def generate_udst_dialogue(sample: Dict, rule: Dict, answer: str, add_noise: str = None) -> Dict:
    """Generate single/multi dialogue for UDST-DurationQA"""
    messages = [
        {
            "role": "user",
            "content": f"Imagine a fictional world with different temporal constraints.\n\n{rule['reasoning']}\n\n{rule['description']}\n\nNow evaluate:\nSentence: {sample['sentence']}\nQuestion: {sample['question']}\nCandidate: {sample['candidate']}\n\nGiven these world rules, is this candidate answer reasonable?"
        },
        {
            "role": "assistant",
            "content": f"I understand. Based on this world's temporal rules, I need to evaluate if '{sample['candidate']}' is acceptable.{add_noise if add_noise else ''}"
        },
        {
            "role": "user",
            "content": f"Would '{sample['candidate']}' be reasonable? Yes or no?"
        }
    ]
    
    options = [
        {"key": "A", "text": "yes"},
        {"key": "B", "text": "no"}
    ]
    return {
        "messages": messages,
        "options": options,
        "answer_key": resolve_answer_key(answer, options)
    }

def add_multi_noise_v1(dialogue: Dict) -> Dict:
    """Add light interruptions/environmental noise"""
    new_dialogue = json.loads(json.dumps(dialogue))  # Deep copy
    
    # Randomly add interruption to assistant's first response
    if len(new_dialogue["messages"]) > 1:
        interruption = random.choice(INTERRUPTIONS_MCTACO if "illnes" in new_dialogue["messages"][0]["content"] else INTERRUPTIONS_UDST)
        new_dialogue["messages"][1]["content"] += interruption
    
    return new_dialogue

def add_multi_noise_v2(dialogue: Dict) -> Dict:
    """Add moderate interruptions and task switching"""
    new_dialogue = json.loads(json.dumps(dialogue))  # Deep copy
    
    # Insert task-switching interruption in user's second message
    if len(new_dialogue["messages"]) > 2:
        task_switch = [
            "\n(By the way, I need to finish some other work too...)",
            "\n(Actually, I have a meeting in a few minutes...)",
            "\n(Sorry, I'm multitasking right now...)",
        ]
        new_dialogue["messages"][2]["content"] = random.choice(task_switch) + "\n" + new_dialogue["messages"][2]["content"]
    
    return new_dialogue

def add_multi_noise_v3(dialogue: Dict) -> Dict:
    """Add strong interruptions - strongest version"""
    new_dialogue = json.loads(json.dumps(dialogue))  # Deep copy
    
    # Add multiple layers of noise
    if len(new_dialogue["messages"]) > 1:
        new_dialogue["messages"][1]["content"] += random.choice(INTERRUPTIONS_MCTACO if "illnes" in new_dialogue["messages"][0]["content"] else INTERRUPTIONS_UDST)
    
    if len(new_dialogue["messages"]) > 2:
        task_switch = "\n(Actually, let me reconsider this from a different angle...)\n"
        new_dialogue["messages"][2]["content"] = task_switch + new_dialogue["messages"][2]["content"]
    
    return new_dialogue

def generate_samples(dataset_type: str = "mctaco", num_samples: int = 100):
    """Main generation function with computed answers"""
    
    if dataset_type == "mctaco":
        print("[MCTACO] Loading samples...")
        raw_samples = load_mctaco_samples(num_samples)
        dialogue_generator = generate_mctaco_dialogue
        rule_generator = generate_mctaco_rule_and_answer
        output_dir = "d:\\workspace\\timeaware\\data-converted\\MCTACO\\sample_T4"
    else:  # udst
        print("[UDST] Loading samples...")
        raw_samples = load_udst_samples(num_samples)
        dialogue_generator = generate_udst_dialogue
        rule_generator = generate_udst_rule_and_answer
        output_dir = "d:\\workspace\\timeaware\\data-converted\\UDST-DurationQA\\sample_T4"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate single, multi_v1, multi_v2, multi_v3
    single_samples = []
    multi_v1_samples = []
    multi_v2_samples = []
    multi_v3_samples = []
    
    print(f"[{dataset_type.upper()}] Generating {num_samples} samples with computed counterfactual answers...")
    
    for idx, sample in enumerate(raw_samples):
        source_id = f"{dataset_type}_{idx:05d}"
        
        # Generate a smart rule AND the corresponding answer
        rule, computed_answer = rule_generator(sample['candidate'])
        
        # Generate single dialogue
        single_dialogue = dialogue_generator(sample, rule, computed_answer)
        single_record = {
            "dataset_name": dataset_type.upper(),
            "task_type": "T4",
            "source_id": source_id,
            "format": "multi_turn",
            "language": "en",
            "messages": single_dialogue["messages"],
            "options": single_dialogue["options"],
            "answer_key": single_dialogue["answer_key"],
            "metadata": {
                "split": "sample",
                "rule_applied": rule["rule_name"],
                "original_label": sample["original_label"],
                "candidate": sample["candidate"],
                "computed_answer": computed_answer
            }
        }
        single_samples.append(single_record)
        
        # Generate multi_v1, v2, v3 with noise
        for v_idx, noise_func in enumerate([add_multi_noise_v1, add_multi_noise_v2, add_multi_noise_v3], 1):
            noisy_dialogue = noise_func(single_dialogue)
            multi_record = json.loads(json.dumps(single_record))  # Copy
            multi_record["messages"] = noisy_dialogue["messages"]
            multi_record["metadata"]["noise_version"] = f"v{v_idx}"
            
            if v_idx == 1:
                multi_v1_samples.append(multi_record)
            elif v_idx == 2:
                multi_v2_samples.append(multi_record)
            else:
                multi_v3_samples.append(multi_record)
        
        if (idx + 1) % 20 == 0:
            print(f"  Generated {idx + 1}/{num_samples} samples...")
    
    # Write to JSONL files
    print(f"\n[{dataset_type.upper()}] Writing output files...")
    
    output_files = {
        "single": single_samples,
        "multi_v1": multi_v1_samples,
        "multi_v2": multi_v2_samples,
        "multi_v3": multi_v3_samples
    }
    
    for file_type, samples in output_files.items():
        output_path = os.path.join(output_dir, f"{dataset_type.upper()}_{file_type}.jsonl")
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        print(f"  ✓ Written {len(samples)} records to {file_type}.jsonl")
    
    print(f"\n[{dataset_type.upper()}] COMPLETE! Generated 400 total samples (100 single + 300 multi)")

if __name__ == "__main__":
    print("=" * 60)
    print("T4 Counterfactual Sample Generation")
    print("=" * 60)
    
    # Generate MCTACO samples
    generate_samples("mctaco", num_samples=100)
    
    print("\n" + "=" * 60 + "\n")
    
    # Generate UDST samples
    generate_samples("udst", num_samples=100)
    
    print("=" * 60)
    print("All generation complete!")
    print("=" * 60)
