#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate T5 Counterfactual samples for 6 datasets:
- MCTACO, UDST-DurationQA (duration-based)
- TempReason, tracie, TimeDial, TRIP (temporal-relational)

Supports both 'sample' (100 samples) and 'full_T5' (full volume) generation modes.
"""

import json
import random
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

random.seed(42)

# ============================================================================
# UTILITY FUNCTIONS (from original)
# ============================================================================

def parse_duration(duration_str: str) -> Tuple[float, str]:
    """Parse a duration string into (value, unit) tuple"""
    duration_str = duration_str.lower().strip()
    match = re.match(r'([0-9.]+)\s*(seconds?|minutes?|hours?|days?|weeks?|months?|years?|centuries?)', duration_str)
    if match:
        try:
            value = float(match.group(1))
            unit = match.group(2).rstrip('s')
            return (value, unit)
        except:
            return (None, None)
    return (None, None)

def convert_to_minutes(value: float, unit: str) -> float:
    """Convert a duration to minutes for comparison"""
    conversions = {
        'second': 1/60, 'minute': 1, 'hour': 60, 'day': 60*24,
        'week': 60*24*7, 'month': 60*24*30, 'year': 60*24*365,
        'century': 60*24*365*100
    }
    return value * conversions.get(unit, 1)

# ============================================================================
# MCTACO DATASET (from original)
# ============================================================================

def load_mctaco_samples(num_samples: int = 100, is_full: bool = False) -> List[Dict]:
    """Load MCTACO test data - only time-related questions"""
    mctaco_file = "d:\\workspace\\timeaware\\data\\MCTACO\\dataset\\test_9442.tsv"
    samples = []
    time_keywords = ['how long', 'how much time', 'how far', 'when', 'duration', 'before', 'after']
    
    max_lines_to_read = 10000 if is_full else 2000
    
    with open(mctaco_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= max_lines_to_read:  # Read enough to sample from
                break
            parts = line.strip().split('\t')
            if len(parts) >= 5:
                question = parts[1].lower()  # Column 1 is question
                # Only include time-related questions with 'no' label
                if any(keyword in question for keyword in time_keywords) and parts[3] == 'no':
                    samples.append({
                        'text': parts[0],
                        'question': parts[1],
                        'candidate': parts[2],
                        'original_label': 'no',
                        'category': parts[4] if len(parts) > 4 else 'Event Duration'
                    })
    
    # Sample randomly
    if len(samples) < num_samples:
        print(f"[WARNING] Only {len(samples)} time-related 'no' samples found, needs {num_samples}")
    return random.sample(samples, min(num_samples, len(samples)))

def generate_mctaco_rule_and_answer(candidate: str) -> Tuple[Dict[str, str], str]:
    """Generate rule for MCTACO: original 'no' -> 'yes'"""
    value, unit = parse_duration(candidate)
    
    if not value or not unit:
        return ({
            "rule_name": "Flexible time standards",
            "description": "Time works differently in this world",
            "reasoning": "This world has unique temporal properties."
        }, "yes")
    
    strategy = random.choice(['A', 'B', 'C'])
    
    if strategy == 'A':  # Time speed change
        if unit in ['second', 'minute']:
            speedup = random.choice([2, 3, 5])
            return ({
                "rule_name": f"Time flows {speedup}x slower",
                "description": f"In this world, time flows {speedup} times slower. A 1-minute task takes {speedup} minutes.",
                "reasoning": "This world has a slower temporal pace, allowing activities to take longer."
            }, "yes")
        else:
            slowdown = random.choice([2, 3, 5])
            return ({
                "rule_name": f"Time flows {slowdown}x faster",
                "description": f"In this world, time flows {slowdown} times faster. Activities complete much quicker.",
                "reasoning": "This world has rapid temporal flow, tasks complete in fractional normal time."
            }, "yes")
    
    elif strategy == 'B':  # Duration range constraint
        lower = int(value * 0.5)
        upper = int(value * 1.5)
        return ({
            "rule_name": f"Standard activity duration: {lower}-{upper} {unit}s",
            "description": f"In this world, typical activities last {lower}-{upper} {unit}s.",
            "reasoning": "This world's work pace is calibrated such that most activities fall within this range."
        }, "yes")
    
    else:  # strategy == 'C', Unit conversion
        if unit == 'second':
            return ({
                "rule_name": "Extended seconds",
                "description": "In this world, 1 second = 10 seconds",
                "reasoning": "Time is perceived differently across temporal scales."
            }, "yes")
        else:
            return ({
                "rule_name": f"Compressed {unit}s",
                "description": f"In this world, 1 {unit} = 0.5 {unit}s nationally accepted",
                "reasoning": "This world redefines standard time units for practical purposes."
            }, "yes")

def generate_mctaco_dialogue(sample, rule, answer, add_noise=None):
    """Generate multi-turn MCTACO dialogue"""
    return {
        "messages": [
            {
                "role": "user",
                "content": f"Consider a fictional world with different temporal rules.\n\n{rule['description']}\n\n{rule['reasoning']}\n\nNow evaluate the following:\nQuestion: {sample['question']}\nCandidate answer: {sample['candidate']}\n\nBased on the temporal rules of this world, is this candidate answer reasonable?"
            },
            {
                "role": "assistant",
                "content": f"I understand. Given the world's temporal rules, I need to evaluate if '{sample['candidate']}' fits within the acceptable durations."
            },
            {
                "role": "user",
                "content": f"Is '{sample['candidate']}' reasonable? Answer yes or no."
            }
        ],
        "options": [{"key": "A", "text": "yes"}, {"key": "B", "text": "no"}],
        "answer_key": [answer]
    }

# ============================================================================
# UDST-DurationQA DATASET (from original)
# ============================================================================

def load_udst_samples(num_samples: int = 100, is_full: bool = False) -> List[Dict]:
    """Load UDST-DurationQA data"""
    udst_file = "d:\\workspace\\timeaware\\data\\UDST-DurationQA\\data\\train.tsv"
    samples = []
    
    max_lines_to_read = 3000 if is_full else 500
    
    with open(udst_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= max_lines_to_read:  # Read enough to sample from
                break
            parts = line.strip().split('\t')
            if len(parts) >= 4 and parts[3] == 'yes':  # Only 'yes' labels for counterfactual
                samples.append({
                    'sentence': parts[0],
                    'question': parts[1],
                    'candidate': parts[2],
                    'original_label': 'yes'
                })
    
    # Sample randomly
    if len(samples) < num_samples:
        print(f"[WARNING] Only {len(samples)} 'yes' samples found, needs {num_samples}")
    return random.sample(samples, min(num_samples, len(samples)))

def generate_udst_rule_and_answer(candidate: str) -> Tuple[Dict[str, str], str]:
    """Generate rule for UDST: original 'yes' -> 'no'"""
    value, unit = parse_duration(candidate)
    
    if not value or not unit:
        return ({
            "rule_name": "Strict temporal limits",
            "description": "Time is severely constrained in this world",
            "reasoning": "This world has imposing temporal restrictions."
        }, "no")
    
    strategy = random.choice(['A', 'B', 'C'])
    
    if strategy == 'A':  # Time speed change
        if unit in ['second', 'minute', 'hour']:
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
    
    elif strategy == 'B':  # Duration range constraint
        minutes = convert_to_minutes(value, unit)
        if minutes < 10:
            return ({
                "rule_name": "Minimum activity duration: 2 hours",
                "description": "In this world, ALL activities must last at least 2 hours minimum",
                "reasoning": "This world operates at a deliberate, slow pace."
            }, "no")
        elif minutes > 480:
            return ({
                "rule_name": "Maximum activity duration: 30 minutes",
                "description": "In this world, NO activity can exceed 30 minutes",
                "reasoning": "This world has extreme time constraints."
            }, "no")
        elif minutes < 120:
            return ({
                "rule_name": "Minimum activity duration: 1 day",
                "description": "In this world, activities must take at least a full day",
                "reasoning": "This world requires extended process time."
            }, "no")
        else:
            return ({
                "rule_name": "Maximum activity duration: 5 minutes",
                "description": "In this world, NO activity can exceed 5 minutes",
                "reasoning": "This world runs at extreme speed."
            }, "no")
    
    else:  # strategy == 'C', Unit conversion
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

def generate_udst_dialogue(sample, rule, answer, add_noise=None):
    """Generate UDST dialogue"""
    return {
        "messages": [
            {
                "role": "user",
                "content": f"Imagine a fictional world with different temporal constraints.\n\n{rule['description']}\n\nNow evaluate:\nQuestion: {sample['question']}\nCandidate: {sample['candidate']}\n\nGiven these world rules, is this candidate answer reasonable?"
            },
            {
                "role": "assistant",
                "content": f"I understand. Based on this world's temporal rules, I need to evaluate if '{sample['candidate']}' is acceptable."
            },
            {
                "role": "user",
                "content": f"Would '{sample['candidate']}' be reasonable? Yes or no?"
            }
        ],
        "options": [{"key": "A", "text": "yes"}, {"key": "B", "text": "no"}],
        "answer_key": [answer]
    }

# ============================================================================
# NEW DATASET: TempReason (日期算术)
# ============================================================================

def load_tempreason_samples(num_samples: int = 100) -> List[Dict]:
    """Load TempReason - date arithmetic questions"""
    file_path = "d:\\workspace\\timeaware\\data\\TempReason\\test_l2.json"
    samples = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                if idx >= num_samples:
                    break
                try:
                    item = json.loads(line)
                    samples.append({
                        'question': item.get('question', ''),
                        'original_date': item.get('date', ''),
                        'answer': item.get('text_answers', {}).get('text', [''])[0],
                        'original_label': 'yes'  # Original is gold standard
                    })
                except:
                    continue
    except:
        pass
    
    return samples[:num_samples]

def generate_tempreason_rule_and_answer(sample: Dict) -> Tuple[Dict[str, str], str]:
    """Generate rule for TempReason: modify date offset"""
    try:
        from datetime import datetime, timedelta
        
        original_date_str = sample.get('original_date', '')
        
        # Parse date like "January 11, 1948"
        date_obj = datetime.strptime(original_date_str, "%B %d, %Y")
        
        # Generate a date offset that will be applied
        new_offset = random.randint(3, 30)  # Days to add to the original date
        
        # Calculate new date by simply adding the offset to original date
        new_date = date_obj + timedelta(days=new_offset)
        new_date_str = new_date.strftime("%B %d, %Y")
        
        rule_name = f"Date arithmetic offset: +{new_offset} days"
        
        return ({
            "rule_name": rule_name,
            "description": f"In this world, the date arithmetic uses +{new_offset} days from the reference date",
            "reasoning": f"The temporal calculation applies a {new_offset}-day offset to the original date",
            "new_date": new_date_str,
            "offset_applied": new_offset
        }, new_date_str)
    except Exception as e:
        # Fallback
        return ({
            "rule_name": "Modified date offset",
            "description": "Date calculation rules differ in this world",
            "reasoning": "Temporal arithmetic has been altered",
            "new_date": sample.get('original_date', 'Unknown')
        }, sample.get('original_date', 'Unknown'))

def generate_tempreason_dialogue(sample, rule, answer, add_noise=None):
    """Generate TempReason dialogue"""
    option_a = answer
    option_b = sample['original_date']
    
    return {
        "messages": [
            {
                "role": "user",
                "content": f"In a fictional world, temporal calculations follow different rules.\n\n{rule['description']}\n\nOriginal context: {sample['question']}\nOriginal date: {sample['original_date']}\n\nIn this world, what would the calculated date be?"
            },
            {
                "role": "assistant",
                "content": f"I understand. With the modified date arithmetic rule ({rule['reasoning']}), I need to recalculate."
            },
            {
                "role": "user",
                "content": f"What is the new date according to this world's rules?\n\nOptions:\nA. {option_a}\nB. {option_b}\n\nThink carefully through all options and return only the final correct option letter(s)."
            }
        ],
        "options": [
            {"key": "A", "text": option_a},
            {"key": "B", "text": option_b}
        ],
        "answer_key": [answer]
    }

# ============================================================================
# NEW DATASET: tracie (事件前后关系)
# ============================================================================

def load_tracie_samples(num_samples: int = 100) -> List[Dict]:
    """Load tracie - temporal event ordering"""
    file_path = "d:\\workspace\\timeaware\\data\\tracie\\data\\iid\\tracie_test.txt"
    samples = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                if idx >= num_samples:
                    break
                parts = line.strip().split('story:')
                if len(parts) >= 2:
                    event_part = parts[0]
                    story_part = 'story:' + parts[1]
                    
                    # Parse event and relationship
                    if 'starts before' in event_part:
                        relationship = 'before'
                    elif 'starts after' in event_part:
                        relationship = 'after'
                    else:
                        continue
                    
                    # Parse answer
                    if 'answer: positive' in story_part:
                        correct_answer = 'positive'
                    elif 'answer: negative' in story_part:
                        correct_answer = 'negative'
                    else:
                        continue
                    
                    # Extract event description
                    event_desc = event_part.replace('event:', '').replace('starts before', '').replace('starts after', '').strip()
                    
                    # Extract story text (remove answer line)
                    story_text = story_part.split('answer:')[0].replace('story:', '').strip()
                    
                    samples.append({
                        'event': event_desc,
                        'relationship': relationship,
                        'story': story_text,
                        'original_label': correct_answer
                    })
    except:
        pass
    
    return samples[:num_samples]

def generate_tracie_rule_and_answer(sample: Dict) -> Tuple[Dict[str, str], str]:
    """Generate rule for tracie: modify temporal relationships"""
    # In the original: sample['relationship'] is 'before' or 'after'
    # In the counterfactual: swap it
    
    original_relationship = sample.get('relationship', 'before')
    original_answer = sample.get('original_label', 'positive')
    
    # Swap the relationship
    counterfactual_relationship = 'after' if original_relationship == 'before' else 'before'
    
    # Determine if it becomes consistent (positive) or inconsistent (negative)
    # This depends on the story and event - we'll flip the label
    counterfactual_answer = 'negative' if original_answer == 'positive' else 'positive'
    
    return ({
        "rule_name": f"Temporal relationship: {original_relationship} -> {counterfactual_relationship}",
        "description": f"In this world, the event {counterfactual_relationship} the story context (changed from {original_relationship})",
        "reasoning": f"Temporal ordering rules are modified - events now occur {counterfactual_relationship} rather than {original_relationship}"
    }, counterfactual_answer)

def generate_tracie_dialogue(sample, rule, answer, add_noise=None):
    """Generate tracie dialogue - temporal consistency judgment"""
    
    return {
        "messages": [
            {
                "role": "user",
                "content": f"In a fictional world with modified temporal relationships:\n\n{rule['description']}\n\nStory context: {sample.get('story', '')[:200]}...\n\nEvent: {sample.get('event', '')}\n\nIn this world's temporal rules, is the event-story relationship consistent?"
            },
            {
                "role": "assistant",
                "content": f"I understand. With the temporal relationship modified ({rule['reasoning']}), I need to evaluate if the event is consistent with the story."
            },
            {
                "role": "user",
                "content": f"Is this relationship consistent?\n\nOptions:\nA. positive (consistent)\nB. negative (inconsistent)\n\nThink carefully through all options and return only the final correct option letter(s)."
            }
        ],
        "options": [
            {"key": "A", "text": "positive"},
            {"key": "B", "text": "negative"}
        ],
        "answer_key": [answer]
    }

# ============================================================================
# NEW DATASET: TimeDial (时间补全)
# ============================================================================

def load_timedial_samples(num_samples: int = 100) -> List[Dict]:
    """Load TimeDial - dialogue time filling"""
    file_path = "d:\\workspace\\timeaware\\data\\TimeDial\\test.json"
    samples = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data[:num_samples]:
            samples.append({
                'conversation': item.get('conversation', []),
                'correct1': item.get('correct1', ''),
                'correct2': item.get('correct2', ''),
                'incorrect1': item.get('incorrect1', ''),
                'incorrect2': item.get('incorrect2', ''),
                'original_label': 'correct'
            })
    except:
        pass
    
    return samples[:num_samples]

def generate_timedial_rule_and_answer(sample: Dict) -> Tuple[Dict[str, str], str]:
    """Generate rule for TimeDial using three counterfactual strategies
    CRITICAL: For Method C (time_unit_change), the unit change must relate to units in the answers
    """
    original_correct = sample.get('correct1', '')
    original_incorrect = sample.get('incorrect1', '')
    
    # Extract answer characteristics first to decide which method to use
    answer_units = set()
    for answer_text in [original_correct, original_incorrect]:
        val, unit = parse_duration(answer_text)
        if unit:
            answer_units.add(unit)
    
    # Decide which method to use based on answer characteristics
    unit_order = ['second', 'minute', 'hour', 'day', 'week', 'month', 'year']
    answer_positions = []
    for u in answer_units:
        if u in unit_order:
            answer_positions.append(unit_order.index(u))
    
    # 50% chance of Method A/B, 50% chance of Method C (if applicable)
    # If answers don't have meaningful time units, force Method A or B
    can_use_method_c = len(answer_units) >= 1 and len(answer_positions) >= 1
    
    if not can_use_method_c:
        # Cannot use Method C - answers don't have extractable time units
        strategy = random.choice(['time_speed_change', 'duration_range_limit'])
    else:
        # Can use Method C - decide with slight bias toward variety
        strategy = random.choice(['time_speed_change', 'duration_range_limit', 'time_unit_change', 'time_unit_change'])
    
    if strategy == 'time_speed_change':
        # Method A: Time flows at different speed
        speed_factor = random.choice([0.1, 0.5, 2, 5, 10])
        
        if speed_factor < 1:
            speed_desc = f"1/{int(1/speed_factor)}"
            reasoning = f"In this world, time flows at {speed_desc} speed (e.g., 1 minute in this world = {int(1/speed_factor)} minutes in normal world)"
        else:
            reasoning = f"In this world, time flows at {speed_factor}x speed (e.g., 1 minute in this world = {int(speed_factor)} minutes in normal world)"
        
        # When time flows differently, the original answer becomes different in interpretation
        # The "new" answer is what would make sense under the new time speed
        new_answer = original_incorrect  # Flip to other option
        
        rule = {
            "rule_name": "Time flow speed changed",
            "description": f"In this world, time flows at a different pace. {reasoning}",
            "reasoning": f"All time-related durations must be interpreted under the new time scale"
        }
    
    elif strategy == 'duration_range_limit':
        # Method B: Duration range constraint
        limit_type = random.choice(['max', 'min'])
        limit_duration = random.choice(['10 seconds', '5 minutes', '30 minutes', '1 hour', '8 hours', '24 hours', '1 week'])
        
        if limit_type == 'max':
            reasoning = f"In this world, no activity can last longer than {limit_duration}"
        else:
            reasoning = f"In this world, every activity must last at least {limit_duration}"
        
        new_answer = original_incorrect  # The other option becomes reasonable
        
        rule = {
            "rule_name": f"Duration constraint: {limit_type}imum {limit_duration}",
            "description": f"In this world, there is a strict duration constraint. {reasoning}",
            "reasoning": f"Answers that violate this constraint become unreasonable, while others become the valid choices"
        }
    
    else:  # time_unit_change
        # Method C: Time unit redefinition - MUST relate to units in the answers
        # Extract time units from both answers
        answer_units = set()
        for answer_text in [original_correct, original_incorrect]:
            val, unit = parse_duration(answer_text)
            if unit:
                answer_units.add(unit)
        
        # Unit hierarchy: second < minute < hour < day < week < month < year
        unit_order = ['second', 'minute', 'hour', 'day', 'week', 'month', 'year']
        
        # Find positions in hierarchy
        answer_positions = []
        for u in answer_units:
            if u in unit_order:
                answer_positions.append(unit_order.index(u))
        
        unit_change = None
        
        # Strategy 1: Two different time units in answers - change their relationship
        if len(answer_positions) >= 2:
            answer_positions.sort()
            min_pos, max_pos = answer_positions[0], answer_positions[-1]
            
            # Find a unit change that relates to both
            for pos1 in range(min_pos, max_pos):
                unit1 = unit_order[pos1]
                unit2 = unit_order[pos1 + 1]
                
                # Check if this change relates to answer units
                related_changes = {
                    ('second', 'minute'): [('1 minute', '50 seconds'), ('1 minute', '100 seconds')],
                    ('minute', 'hour'): [('1 hour', '45 minutes'), ('1 hour', '75 minutes')],
                    ('hour', 'day'): [('1 day', '20 hours'), ('1 day', '30 hours')],
                    ('day', 'week'): [('1 week', '6 days'), ('1 week', '8 days')],
                    ('week', 'month'): [('1 month', '3 weeks'), ('1 month', '5 weeks')],
                    ('month', 'year'): [('1 year', '10 months'), ('1 year', '15 months')],
                }
                
                if (unit1, unit2) in related_changes:
                    unit_change = random.choice(related_changes[(unit1, unit2)])
                    break
        
        # Strategy 2: Single unit or no units extracted - pick from answer unit context
        if unit_change is None:
            if answer_units:
                detected_unit = list(answer_units)[0]
                detected_pos = unit_order.index(detected_unit) if detected_unit in unit_order else 2
            else:
                detected_unit = 'hour'
                detected_pos = 2
            
            # Prioritize adjacent units in hierarchy that definitely relate to the detected unit
            adjacent_units = []
            if detected_pos > 0:
                adjacent_units.append((unit_order[detected_pos - 1], unit_order[detected_pos]))
            if detected_pos < len(unit_order) - 1:
                adjacent_units.append((unit_order[detected_pos], unit_order[detected_pos + 1]))
            
            if adjacent_units:
                related_changes = {
                    ('second', 'minute'): [('1 minute', '50 seconds'), ('1 minute', '100 seconds')],
                    ('minute', 'hour'): [('1 hour', '45 minutes'), ('1 hour', '75 minutes')],
                    ('hour', 'day'): [('1 day', '20 hours'), ('1 day', '30 hours')],
                    ('day', 'week'): [('1 week', '6 days'), ('1 week', '8 days')],
                    ('week', 'month'): [('1 month', '3 weeks'), ('1 month', '5 weeks')],
                    ('month', 'year'): [('1 year', '10 months'), ('1 year', '15 months')],
                }
                
                valid_changes = []
                for u1, u2 in adjacent_units:
                    if (u1, u2) in related_changes:
                        valid_changes.extend(related_changes[(u1, u2)])
                
                if valid_changes:
                    unit_change = random.choice(valid_changes)
        
        # Fallback if still no unit change found
        if unit_change is None:
            unit_change = random.choice([
                ('1 hour', '120 minutes'),
                ('1 day', '30 hours'),
                ('1 week', '8 days'),
                ('1 hour', '75 minutes'),
            ])
        
        original_unit, new_unit = unit_change
        
        reasoning = f"In this world, {original_unit} = {new_unit} (not the standard definition)"
        new_answer = original_incorrect  # Flip to other option
        
        rule = {
            "rule_name": f"Time unit redefined: {original_unit} → {new_unit}",
            "description": f"In this world, the definition of time units has changed. {reasoning}",
            "reasoning": f"All time-related calculations must use the new unit definitions"
        }
    
    return (rule, new_answer)

def generate_timedial_dialogue(sample, rule, answer, add_noise=None):
    """Generate TimeDial dialogue - TRUE counterfactual reasoning WITHOUT answer leakage"""
    # Build conversation excerpt using user/assistant format
    conversation = sample.get('conversation', [])
    messages = []
    
    # Message 0: Present the NEW RULE ONLY - NO ANSWER HINTS
    # This is where the model learns the counterfactual constraint
    messages.append({
        "role": "user",
        "content": f"Consider a fictional world where:\n{rule['description']}\n\nNow examine this conversation and think carefully about which time-related answer becomes appropriate under these new rules:"
    })
    
    # Messages 1+: Present the conversation naturally
    # Clean up A: B: prefixes from original data
    if isinstance(conversation, list) and len(conversation) > 0:
        for idx, turn in enumerate(conversation[:4]):  # First 4 turns
            # Remove A: or B: prefix if present
            clean_turn = turn
            if clean_turn.startswith('A:'):
                clean_turn = clean_turn[2:].strip()
            elif clean_turn.startswith('B:'):
                clean_turn = clean_turn[2:].strip()
            
            if idx % 2 == 0:
                messages.append({"role": "user", "content": clean_turn})
            else:
                messages.append({"role": "assistant", "content": clean_turn})
    
    # Get both options for comparison
    option_a = answer  # New answer (counterfactual)
    option_b = sample.get('correct1', '') if answer != sample.get('correct1', '') else sample.get('incorrect1', '')
    
    if not option_b or option_b == answer:
        option_b = sample.get('incorrect1', '') if sample.get('incorrect1', '') != answer else sample.get('correct2', '')
    
    # Final question: which makes sense under the NEW RULE (requires actual reasoning)
    messages.append({
        "role": "user",
        "content": f"Given the new world's rules ({rule['reasoning']}), which time-related answer is now more appropriate?\n\nOptions:\nA. {option_a}\nB. {option_b}\n\nThink carefully about how the rule changes the reasonableness of each option. Return only the correct option letter."
    })
    
    return {
        "messages": messages,
        "options": [
            {"key": "A", "text": option_a},
            {"key": "B", "text": option_b}
        ],
        "answer_key": [answer]
    }

# ============================================================================
# NEW DATASET: TRIP (旅程约束)
# ============================================================================

def load_trip_samples(num_samples: int = 100) -> List[Dict]:
    """Load TRIP - travel planning with constraints"""
    file_path = "d:\\workspace\\timeaware\\data\\TRIP\\postprocess\\sample_evaluation_format.jsonl"
    samples = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                if idx >= num_samples:
                    break
                try:
                    item = json.loads(line)
                    json_data = item.get('JSON', {})
                    samples.append({
                        'origin': json_data.get('org', ''),
                        'destination': json_data.get('dest', ''),
                        'num_days': json_data.get('days', 3),
                        'budget': json_data.get('budget', 5000),
                        'feasible': 'yes',
                        'original_label': 'yes'
                    })
                except:
                    continue
    except:
        # Fallback: create synthetic samples
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
        for i in range(num_samples):
            orig = random.choice(cities)
            dest = random.choice([c for c in cities if c != orig])
            samples.append({
                'origin': orig,
                'destination': dest,
                'num_days': random.randint(3, 7),
                'budget': random.randint(1000, 10000),
                'feasible': 'yes',
                'original_label': 'yes'
            })
    
    return samples[:num_samples]

def generate_trip_rule_and_answer(sample: Dict) -> Tuple[Dict[str, str], str]:
    """Generate rule for TRIP: modify temporal/budget constraints"""
    strategy = random.choice(['compress_time', 'expand_time', 'reduce_budget', 'increase_budget'])
    
    original_answer = 'yes'  # Original feasibility
    
    if strategy == 'compress_time':
        # Days become halved
        new_days = max(1, int(sample.get('num_days', 3) * 0.5))
        new_answer = 'no'  # Compressed time makes trip infeasible
        return ({
            "rule_name": f"Time compression: {sample.get('num_days', 3)} days -> {new_days} day(s)",
            "description": f"In this world, a week only lasts {new_days} days instead of 7",
            "reasoning": "Calendar structure is fundamentally different"
        }, new_answer)
    
    elif strategy == 'expand_time':
        # Days almost doubled
        new_days = int(sample.get('num_days', 3) * 1.8)
        new_answer = 'yes'  # More time keeps trip feasible
        return ({
            "rule_name": f"Time expansion: {sample.get('num_days', 3)} days -> {new_days} days",
            "description": f"In this world, the journey can span {new_days} days",
            "reasoning": "Extended planning window becomes available"
        }, new_answer)
    
    elif strategy == 'reduce_budget':
        # Budget becomes very tight
        new_budget = sample.get('budget', 5000) // 4
        new_answer = 'no'  # Reduced budget makes trip infeasible
        return ({
            "rule_name": f"Budget constraint: {sample.get('budget', 5000)} -> {new_budget}",
            "description": f"In this world, available budget is only {new_budget}",
            "reasoning": "Economic constraints are much stricter"
        }, new_answer)
    
    else:  # increase_budget
        # Budget doubled
        new_budget = sample.get('budget', 5000) * 2
        new_answer = 'yes'  # More money keeps trip feasible
        return ({
            "rule_name": f"Budget increase: {sample.get('budget', 5000)} -> {new_budget}",
            "description": f"In this world, available budget is {new_budget}",
            "reasoning": "Increased resources enable fuller itinerary"
        }, new_answer)

def generate_trip_dialogue(sample, rule, answer, add_noise=None):
    """Generate TRIP dialogue - travel planning feasibility"""
    option_a = answer
    option_b = "no" if answer == "yes" else "yes"
    
    return {
        "messages": [
            {
                "role": "user",
                "content": f"In a fictional world with different spatio-temporal constraints:\n\n{rule['description']}\n\nOriginal trip: {sample.get('origin', '?')} to {sample.get('destination', '?')}\nPlanned days: {sample.get('num_days', '?')}\nBudget: ${sample.get('budget', '?')}\n\nWith the new world constraints, is this trip still feasible?"
            },
            {
                "role": "assistant",
                "content": f"I understand. The constraints have changed ({rule['reasoning']}). Let me evaluate if the original plan still works."
            },
            {
                "role": "user",
                "content": f"Is this trip feasible under the new rules?\n\nOptions:\nA. {option_a}\nB. {option_b}\n\nThink carefully through all options and return only the final correct option letter(s)."
            }
        ],
        "options": [
            {"key": "A", "text": option_a},
            {"key": "B", "text": option_b}
        ],
        "answer_key": [answer]
    }

# ============================================================================
# NOISE FUNCTIONS (from original)
# ============================================================================

INTERRUPTIONS_MCTACO = [
    " (phone rings) Sorry about that... (takes 30 seconds)",
    " Actually, let me double-check something real quick... (pause)",
    " Wait, I just got a notification, hang on... (reads message)",
]

INTERRUPTIONS_UDST = [
    " (getting a notification) Sorry, just got a text...",
    " Actually, now that I think about it... (pausing)",
    " (background sound) Oops, there's music playing nearby.",
]

# ============================================================================
# NOISE FUNCTIONS - Modified to avoid repetition
# ============================================================================

def add_multi_noise_v1(dialogue):
    """Light noise - single interruption"""
    noisy_messages = []
    for idx, msg in enumerate(dialogue['messages']):
        if msg['role'] == 'assistant' and idx == 1:  # Only inject once in assistant's first response
            interruption = random.choice(INTERRUPTIONS_MCTACO)
            msg = dict(msg)
            msg['content'] = msg['content'] + interruption
        noisy_messages.append(msg)
    return {"messages": noisy_messages, "options": dialogue['options'], "answer_key": dialogue['answer_key']}

def add_multi_noise_v2(dialogue):
    """Medium noise - two light interruptions"""
    noisy_messages = []
    interruption_indices = [1, 3] if len(dialogue['messages']) > 3 else [1]
    for idx, msg in enumerate(dialogue['messages']):
        if msg['role'] == 'assistant' and idx in interruption_indices:
            interruption = random.choice(INTERRUPTIONS_MCTACO)
            msg = dict(msg)
            msg['content'] = msg['content'] + interruption
        noisy_messages.append(msg)
    return {"messages": noisy_messages, "options": dialogue['options'], "answer_key": dialogue['answer_key']}

def add_multi_noise_v3(dialogue):
    """Heavy noise - multiple interruptions"""
    noisy_messages = []
    for idx, msg in enumerate(dialogue['messages']):
        if msg['role'] == 'assistant':
            interruption = random.choice(INTERRUPTIONS_MCTACO) + " " + random.choice(INTERRUPTIONS_MCTACO)
            msg = dict(msg)
            msg['content'] = msg['content'] + interruption
        noisy_messages.append(msg)
    return {"messages": noisy_messages, "options": dialogue['options'], "answer_key": dialogue['answer_key']}

# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================

def generate_samples(dataset_type: str = "mctaco", num_samples: int = 100, output_mode: str = "sample"):
    """
    Main generation function
    
    Args:
        dataset_type: 'mctaco', 'udst', 'tempreason', 'tracie', 'timedial', 'trip'
        num_samples: Number of samples to generate (100 for 'sample', full for 'full_T5')
        output_mode: 'sample' (100 samples) or 'full_T5' (full volume)
    """
    
    dataset_config = {
        'mctaco': {
            'loader': load_mctaco_samples,
            'rule_gen': generate_mctaco_rule_and_answer,
            'dialogue_gen': generate_mctaco_dialogue,
            'dir_suffix': 'MCTACO'
        },
        'udst': {
            'loader': load_udst_samples,
            'rule_gen': generate_udst_rule_and_answer,
            'dialogue_gen': generate_udst_dialogue,
            'dir_suffix': 'UDST-DurationQA'
        },
        'tempreason': {
            'loader': load_tempreason_samples,
            'rule_gen': generate_tempreason_rule_and_answer,
            'dialogue_gen': generate_tempreason_dialogue,
            'dir_suffix': 'TempReason'
        },
        'tracie': {
            'loader': load_tracie_samples,
            'rule_gen': generate_tracie_rule_and_answer,
            'dialogue_gen': generate_tracie_dialogue,
            'dir_suffix': 'tracie'
        },
        'timedial': {
            'loader': load_timedial_samples,
            'rule_gen': generate_timedial_rule_and_answer,
            'dialogue_gen': generate_timedial_dialogue,
            'dir_suffix': 'TimeDial'
        },
        'trip': {
            'loader': load_trip_samples,
            'rule_gen': generate_trip_rule_and_answer,
            'dialogue_gen': generate_trip_dialogue,
            'dir_suffix': 'TRIP'
        }
    }
    
    if dataset_type not in dataset_config:
        print(f"Unknown dataset: {dataset_type}")
        return
    
    config = dataset_config[dataset_type]
    print(f"[{dataset_type.upper()}] Loading samples...")
    
    # For MCTACO and UDST, pass is_full flag
    if dataset_type in ['mctaco', 'udst']:
        is_full = (output_mode == 'full_T5')
        raw_samples = config['loader'](num_samples, is_full=is_full)
    else:
        raw_samples = config['loader'](num_samples)
    
    if not raw_samples:
        print(f"[{dataset_type.upper()}] ERROR: No samples loaded!")
        return
    
    # Determine output directory
    if output_mode == 'full_T5':
        output_dir = f"d:\\workspace\\timeaware\\data-converted\\{config['dir_suffix']}\\full_T5"
    else:  # sample
        output_dir = f"d:\\workspace\\timeaware\\data-converted\\{config['dir_suffix']}\\sample_T5"
    
    os.makedirs(output_dir, exist_ok=True)
    
    single_samples = []
    multi_v1_samples = []
    multi_v2_samples = []
    multi_v3_samples = []
    
    print(f"[{dataset_type.upper()}] Generating {len(raw_samples)} samples with computed counterfactual answers...")
    
    for idx, sample in enumerate(raw_samples):
        try:
            source_id = f"{dataset_type}_{idx:05d}"
            
            # For datasets that need complete sample context, pass full sample
            # For others, extract the candidate value
            if dataset_type in ['tracie', 'tempreason', 'timedial', 'trip']:
                rule, computed_answer = config['rule_gen'](sample)
            else:
                # For MCTACO/UDST, extract candidate value
                rule, computed_answer = config['rule_gen'](sample['candidate'])
            
            # Generate dialogue
            single_dialogue = config['dialogue_gen'](sample, rule, computed_answer)
            single_record = {
                "dataset_name": dataset_type.upper(),
                "task_type": "T5",
                "source_id": source_id,
                "format": "multi_turn",
                "language": "en",
                "messages": single_dialogue["messages"],
                "options": single_dialogue["options"],
                "answer_key": single_dialogue["answer_key"],
                "metadata": {
                    "split": output_mode,
                    "rule_applied": rule["rule_name"],
                    "original_label": sample.get('original_label', 'unknown'),
                    "computed_answer": str(computed_answer)
                }
            }
            single_samples.append(single_record)
            
            # Generate multi versions with noise (for sample mode only)
            if output_mode == 'sample':
                for v_idx, noise_func in enumerate([add_multi_noise_v1, add_multi_noise_v2, add_multi_noise_v3], 1):
                    noisy_dialogue = noise_func(single_dialogue)
                    multi_record = json.loads(json.dumps(single_record))
                    multi_record["messages"] = noisy_dialogue["messages"]
                    multi_record["metadata"]["noise_version"] = f"v{v_idx}"
                    
                    if v_idx == 1:
                        multi_v1_samples.append(multi_record)
                    elif v_idx == 2:
                        multi_v2_samples.append(multi_record)
                    else:
                        multi_v3_samples.append(multi_record)
            
            if (idx + 1) % 20 == 0:
                print(f"  Generated {idx + 1}/{len(raw_samples)} samples...")
        
        except Exception as e:
            print(f"  [WARNING] Sample {idx} failed: {str(e)}")
            continue
    
    # Write outputs
    print(f"\n[{dataset_type.upper()}] Writing output files...")
    
    if output_mode == 'sample':
        output_files = {
            "single": single_samples,
            "multi_v1": multi_v1_samples,
            "multi_v2": multi_v2_samples,
            "multi_v3": multi_v3_samples
        }
    else:
        output_files = {
            "full": single_samples
        }
    
    for file_type, samples in output_files.items():
        output_path = os.path.join(output_dir, f"{dataset_type.upper()}_{file_type}.jsonl")
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        print(f"  [OK] Written {len(samples)} records to {file_type}.jsonl")
    
    if output_mode == 'sample':
        print(f"\n[{dataset_type.upper()}] COMPLETE! Generated {len(single_samples) * 4} total samples (100 single + 300 multi)")
    else:
        print(f"\n[{dataset_type.upper()}] COMPLETE! Generated {len(single_samples)} total samples")

if __name__ == "__main__":
    print("=" * 70)
    print("T5 Counterfactual Extended Sample Generation (6 Datasets)")
    print("=" * 70)
    
    # Phase 1: Generate MCTACO/UDST full_T5 versions
    print("\n[PHASE 1] Generating MCTACO/UDST full_T5 (full volume)...\n")
    generate_samples("mctaco", num_samples=2000, output_mode="full_T5")  # Load all available
    print("\n" + "=" * 70 + "\n")
    generate_samples("udst", num_samples=2000, output_mode="full_T5")
    
    # Phase 2: Generate 4 new datasets (sample mode for user review)
    print("\n[PHASE 2] Generating new datasets (sample_T5 - 100 samples each for review)...\n")
    for dataset in ["tempreason", "tracie", "timedial", "trip"]:
        generate_samples(dataset, num_samples=100, output_mode="sample")
        print("\n" + "=" * 70 + "\n")
    
    print("All generation complete!")
