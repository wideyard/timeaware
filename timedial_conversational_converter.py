#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimeDial Conversational Temporal Data Converter

Converts TimeDial dataset to conversational temporal format.
Primary focus: T1 (Time Calculation with distractor interference)
Secondary: T4 (Long-term Memory - dialogue context)

Key features:
- Multi-turn dialogue with time-related <MASK>
- Distractor options designed to test spurious features (text/number matching)
- Anti-data-pollution testing (correct vs distractor choices)

Output: converted_data_v3/timedial_conversational.jsonl
"""

import json
import random
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from pathlib import Path

# =====================================================================
# Data Structures
# =====================================================================

@dataclass
class ConversationalSample:
    task: str  # T1, T4
    sub_task: str  # e.g., "T1-Convo-Calc", "T1-Convo-Distractor"
    context: str  # Dialogue context
    conversation: List[Dict[str, str]]
    query: str
    answer: str
    state_info: Optional[Dict[str, Any]] = None
    ground_truth: Optional[Dict[str, Any]] = None
    difficulty: str = "medium"
    source_id: Optional[str] = None

# =====================================================================
# Helper Functions
# =====================================================================

# Time-related keywords
TIME_KEYWORDS = [
    "hours", "hour", "minutes", "minute", "seconds", "second",
    "days", "day", "weeks", "week", "months", "month", "years", "year",
    "o'clock", "am", "pm", "morning", "afternoon", "evening", "night",
    "yesterday", "tomorrow", "today", "tonight", "last", "next",
    "ago", "before", "after", "during", "since", "until"
]

# Noise questions for distraction
NOISE_QUESTIONS = [
    "By the way, what's the weather like?",
    "I heard about a new restaurant.",
    "The traffic was terrible today.",
    "Did you watch the game last night?",
    "What's for dinner?",
    "I need to buy groceries later.",
    "Have you tried that new coffee shop?",
    "My neighbor's cat is cute.",
    "The movie was interesting.",
    "What time is it now?"
]

def truncate_text(text: str, max_len: int = 300) -> str:
    """Truncate text to max length."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(' ', 1)[0] + '...'

def extract_time_entities(text: str) -> List[str]:
    """Extract time-related entities from text."""
    entities = []
    text_lower = text.lower()
    
    # Time patterns
    patterns = [
        r'\d+\s*(?:hours?|minutes?|seconds?|days?|weeks?|months?|years?)',
        r'\d+[:.]\d+\s*(?:am|pm)?',
        r'(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(?:hours?|minutes?|days?|weeks?)',
        r'(?:yesterday|tomorrow|today|tonight)',
        r'(?:last|next)\s+(?:week|month|year)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        entities.extend(matches)
    
    return entities

def is_time_related(conv: List[str]) -> bool:
    """Check if conversation contains time-related content."""
    full_text = ' '.join(conv).lower()
    return any(kw in full_text for kw in TIME_KEYWORDS)

def find_mask_context(conversation: List[str]) -> tuple:
    """Find the line with <MASK> and its context."""
    mask_line_idx = None
    mask_line = None
    
    for i, line in enumerate(conversation):
        if '<MASK>' in line:
            mask_line_idx = i
            mask_line = line
            break
    
    return mask_line_idx, mask_line

def get_rule_type(rule: str) -> str:
    """Convert rule string to description."""
    rule_map = {
        "Rule 1": "phrase_matching",  # Phrase from context
        "Rule 2": "numeral_matching",  # Number from context
        "Rule 3": "other_distractor",  # Other type
    }
    return rule_map.get(rule, "unknown")

# =====================================================================
# T1: Time Calculation Converter
# =====================================================================

class T1Converter:
    """Convert TimeDial data to T1 time calculation format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_time_calc_sample(self, conversation: List[str], 
                                 correct1: str, correct2: str,
                                 incorrect1: str, incorrect2: str,
                                 inc1_rule: str, inc2_rule: str,
                                 sample_id: str) -> Optional[ConversationalSample]:
        """T1-Convo-Calc: Time calculation with distractor interference."""
        # Find <MASK> line
        mask_idx, mask_line = find_mask_context(conversation)
        if mask_idx is None:
            return None
        
        conv_result = []
        
        # Build conversation with context
        # Present dialogue turns before the MASK
        for i, line in enumerate(conversation[:mask_idx]):
            speaker = "A" if i % 2 == 0 else "B"  # Assume alternating
            conv_result.append({
                "role": "user",
                "content": line.replace('<MASK>', '___')
            })
            
            conv_result.append({
                "role": "assistant",
                "content": "I understand."
            })
        
        # Add the MASK line as a question
        mask_question = mask_line.replace('<MASK>', '___')
        conv_result.append({
            "role": "user",
            "content": f"Fill in the blank: {mask_question}"
        })
        
        # Create answer with distractor analysis
        correct = correct1.strip() if correct1 else correct2.strip()
        inc1 = incorrect1.strip() if incorrect1 else ""
        inc2 = incorrect2.strip() if incorrect2 else ""
        
        rule1_desc = get_rule_type(inc1_rule)
        rule2_desc = get_rule_type(inc2_rule)
        
        # Format answer explaining why distractors are wrong
        answer = f"{correct}"
        
        return ConversationalSample(
            task="T1",
            sub_task="T1-Convo-Calc",
            context=truncate_text(' '.join(conversation[:mask_idx+1]), 250),
            conversation=conv_result,
            query=f"Fill in the blank: {mask_question}",
            answer=answer,
            state_info={
                "type": "time_calculation",
                "distractor_1": inc1,
                "distractor_2": inc2,
                "distractor_1_rule": rule1_desc,
                "distractor_2_rule": rule2_desc
            },
            ground_truth={
                "correct_answer": correct,
                "alternate_correct": correct2.strip() if correct2 else None,
                "incorrect_1": inc1,
                "incorrect_2": inc2
            },
            difficulty="medium" if not inc1 else "hard",
            source_id=f"timedial_t1_calc_{sample_id}"
        )
    
    def create_distractor_resist_sample(self, conversation: List[str],
                                        correct1: str, correct2: str,
                                        incorrect1: str, incorrect2: str,
                                        inc1_rule: str, inc2_rule: str,
                                        sample_id: str) -> Optional[ConversationalSample]:
        """T1-Convo-Distractor: Explicitly test resistance to distractors."""
        # Find <MASK> line
        mask_idx, mask_line = find_mask_context(conversation)
        if mask_idx is None:
            return None
        
        conv_result = []
        
        # Present dialogue
        for i, line in enumerate(conversation[:mask_idx]):
            conv_result.append({
                "role": "user",
                "content": line
            })
            conv_result.append({
                "role": "assistant",
                "content": "Noted."
            })
        
        # Extract time entities from context (distractors)
        context_text = ' '.join(conversation[:mask_idx])
        time_entities = extract_time_entities(context_text)
        
        # Add distractor warning
        conv_result.append({
            "role": "user",
            "content": "I see some time expressions in the conversation above. But they might be distractors!"
        })
        conv_result.append({
            "role": "assistant",
            "content": "You're right. Numbers appearing in text may be distractors, not the answer."
        })
        
        # Add noise
        conv_result.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        conv_result.append({
            "role": "assistant",
            "content": "Let me focus on the time calculation."
        })
        
        # Query with explicit distractors
        correct = correct1.strip() if correct1 else correct2.strip()
        inc1 = incorrect1.strip() if incorrect1 else ""
        inc2 = incorrect2.strip() if incorrect2 else ""
        
        mask_question = mask_line.replace('<MASK>', '___')
        
        query = f"Based on the conversation logic (not just text matching), fill in: {mask_question}"
        
        # Build answer explaining why distractors are wrong
        answer_parts = [f"The answer is {correct}."]
        
        if inc1:
            rule1_type = get_rule_type(inc1_rule)
            if rule1_type == "numeral_matching":
                answer_parts.append(f"Note: '{inc1}' is a distractor - it's just a number from the context, not the logical answer.")
            elif rule1_type == "phrase_matching":
                answer_parts.append(f"Note: '{inc1}' is wrong - it's a phrase from context, but doesn't fit the logic.")
            else:
                answer_parts.append(f"Note: '{inc1}' is incorrect for this context.")
        
        if inc2:
            rule2_type = get_rule_type(inc2_rule)
            if rule2_type == "numeral_matching":
                answer_parts.append(f"'{inc2}' is also a distractor - a number from context.")
            elif rule2_type == "phrase_matching":
                answer_parts.append(f"'{inc2}' doesn't fit the dialogue logic.")
            else:
                answer_parts.append(f"'{inc2}' is incorrect.")
        
        answer = " ".join(answer_parts)
        
        return ConversationalSample(
            task="T1",
            sub_task="T1-Convo-Distractor",
            context=truncate_text(context_text, 200),
            conversation=conv_result,
            query=query,
            answer=answer,
            state_info={
                "type": "distractor_resistance",
                "distractors": [inc1, inc2],
                "distractor_rules": [get_rule_type(inc1_rule), get_rule_type(inc2_rule)],
                "time_entities_in_context": time_entities[:5]
            },
            ground_truth={
                "correct": correct,
                "distractor_1": inc1,
                "distractor_2": inc2,
                "distractor_1_rule": inc1_rule,
                "distractor_2_rule": inc2_rule
            },
            difficulty="hard",
            source_id=f"timedial_t1_dist_{sample_id}"
        )
    
    def create_multi_choice_sample(self, conversation: List[str],
                                    correct1: str, correct2: str,
                                    incorrect1: str, incorrect2: str,
                                    inc1_rule: str, inc2_rule: str,
                                    sample_id: str) -> Optional[ConversationalSample]:
        """T1-Convo-MultiChoice: Multiple choice format for automated evaluation."""
        # Find <MASK> line
        mask_idx, mask_line = find_mask_context(conversation)
        if mask_idx is None:
            return None
        
        conv_result = []
        
        # Present dialogue
        for i, line in enumerate(conversation[:mask_idx]):
            conv_result.append({
                "role": "user",
                "content": line
            })
            conv_result.append({
                "role": "assistant",
                "content": "I'm following the conversation."
            })
        
        # Add mask question with options
        correct = correct1.strip() if correct1 else correct2.strip()
        inc1 = incorrect1.strip() if incorrect1 else "unknown"
        inc2 = incorrect2.strip() if incorrect2 else "unknown"
        
        # Shuffle options
        import random as rand
        options = [(correct, "A"), (inc1, "B"), (inc2, "C")]
        rand.shuffle(options)
        
        option_text = "\n".join([f"{letter}. {opt}" for opt, letter in options])
        mask_question = mask_line.replace('<MASK>', '___')
        
        query = f"{mask_question}\n\nChoose the best answer:\n{option_text}"
        
        conv_result.append({
            "role": "user",
            "content": query
        })
        
        # Find correct letter
        correct_letter = "A"
        for opt, letter in options:
            if opt == correct:
                correct_letter = letter
                break
        
        return ConversationalSample(
            task="T1",
            sub_task="T1-Convo-MultiChoice",
            context=truncate_text(' '.join(conversation[:mask_idx]), 200),
            conversation=conv_result,
            query=query,
            answer=correct_letter,
            state_info={
                "type": "multiple_choice",
                "options": [opt for opt, _ in options],
                "distractor_rules": [get_rule_type(inc1_rule), get_rule_type(inc2_rule)]
            },
            ground_truth={
                "correct_answer": correct,
                "correct_letter": correct_letter,
                "distractor_1": inc1,
                "distractor_2": inc2
            },
            difficulty="medium",
            source_id=f"timedial_t1_mc_{sample_id}"
        )

# =====================================================================
# T4: Long-term Memory Converter
# =====================================================================

class T4Converter:
    """Convert TimeDial data to T4 long-term memory format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_dialogue_memory_sample(self, conversation: List[str],
                                       correct1: str, correct2: str,
                                       sample_id: str) -> Optional[ConversationalSample]:
        """T4-Convo-Dialog: Retrieve time info from dialogue context."""
        # Find <MASK> line
        mask_idx, mask_line = find_mask_context(conversation)
        if mask_idx is None or mask_idx < 3:
            return None  # Need at least a few lines for memory test
        
        conv_result = []
        
        # Present all dialogue turns
        for i, line in enumerate(conversation[:mask_idx]):
            conv_result.append({
                "role": "user",
                "content": line
            })
            conv_result.append({
                "role": "assistant",
                "content": "I'm listening."
            })
        
        # Add noise questions in the middle
        mid_point = len(conv_result) // 2
        conv_result.insert(mid_point, {
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        conv_result.insert(mid_point + 1, {
            "role": "assistant",
            "content": "Let me stay focused on the conversation."
        })
        
        # Query about time-relevant info
        mask_question = mask_line.replace('<MASK>', '___')
        correct = correct1.strip() if correct1 else correct2.strip()
        
        query = f"From the conversation above, what time value fills in: {mask_question}"
        
        return ConversationalSample(
            task="T4",
            sub_task="T4-Convo-Dialog",
            context=truncate_text(' '.join(conversation[:mask_idx]), 250),
            conversation=conv_result,
            query=query,
            answer=correct,
            state_info={
                "type": "dialogue_memory",
                "dialogue_length": len(conversation),
                "mask_position": mask_idx
            },
            ground_truth={
                "correct_answer": correct,
                "alternate_correct": correct2.strip() if correct2 else None
            },
            difficulty="hard",
            source_id=f"timedial_t4_dialog_{sample_id}"
        )
    
    def create_time_recall_sample(self, conversation: List[str],
                                   correct1: str, correct2: str,
                                   sample_id: str) -> Optional[ConversationalSample]:
        """T4-Convo-Recall: Recall specific time mentioned earlier."""
        # Find <MASK> line
        mask_idx, mask_line = find_mask_context(conversation)
        if mask_idx is None or mask_idx < 3:
            return None
        
        conv_result = []
        
        # Present dialogue
        for i, line in enumerate(conversation[:mask_idx]):
            conv_result.append({
                "role": "user",
                "content": line
            })
            conv_result.append({
                "role": "assistant",
                "content": "Got it."
            })
        
        # Extract time mentions from earlier in conversation
        time_mentions = []
        for i, line in enumerate(conversation[:mask_idx]):
            entities = extract_time_entities(line)
            if entities:
                time_mentions.extend(entities)
        
        correct = correct1.strip() if correct1 else correct2.strip()
        
        # Query asking to recall time
        query = "Based on the full conversation context, what time-related information was discussed?"
        
        # Answer combines time mentions
        answer = f"The conversation mentions time: {', '.join(time_mentions[:3])}. The correct fill-in is: {correct}"
        
        return ConversationalSample(
            task="T4",
            sub_task="T4-Convo-Recall",
            context=truncate_text(' '.join(conversation[:mask_idx]), 200),
            conversation=conv_result,
            query=query,
            answer=answer,
            state_info={
                "type": "time_recall",
                "time_mentions": time_mentions[:5],
                "correct_fill": correct
            },
            ground_truth={
                "time_entities": time_mentions,
                "answer": correct
            },
            difficulty="hard",
            source_id=f"timedial_t4_recall_{sample_id}"
        )

# =====================================================================
# Main Converter
# =====================================================================

class TimeDialConversationalConverter:
    """Main converter for TimeDial to conversational format."""
    
    def __init__(self, data_dir: str = "data/TimeDial"):
        self.data_dir = Path(data_dir)
        self.t1_converter = T1Converter()
        self.t4_converter = T4Converter()
    
    def load_data(self) -> List[Dict]:
        """Load TimeDial data."""
        test_file = self.data_dir / "test.json"
        
        if not test_file.exists():
            print(f"Data file not found: {test_file}")
            return []
        
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # The data is a dict with 'value' key containing list of samples
        if isinstance(data, dict) and 'value' in data:
            samples = data['value']
        else:
            samples = data if isinstance(data, list) else []
        
        print(f"Loaded {len(samples)} samples")
        return samples
    
    def convert_sample(self, sample: Dict, sample_id: str) -> List[ConversationalSample]:
        """Convert a single TimeDial sample."""
        results = []
        
        conversation = sample.get("conversation", [])
        correct1 = sample.get("correct1", "")
        correct2 = sample.get("correct2", "")
        incorrect1 = sample.get("incorrect1", "")
        incorrect2 = sample.get("incorrect2", "")
        inc1_rule = sample.get("incorrect1_rule", "")
        inc2_rule = sample.get("incorrect2_rule", "")
        
        if not conversation or not correct1:
            return results
        
        # Check if time-related
        if not is_time_related(conversation):
            return results
        
        # T1: Time calculation with distractors
        sample_t1_calc = self.t1_converter.create_time_calc_sample(
            conversation, correct1, correct2, incorrect1, incorrect2,
            inc1_rule, inc2_rule, sample_id
        )
        if sample_t1_calc:
            results.append(sample_t1_calc)
        
        # T1: Distractor resistance (if has distractors)
        if incorrect1 or incorrect2:
            sample_t1_dist = self.t1_converter.create_distractor_resist_sample(
                conversation, correct1, correct2, incorrect1, incorrect2,
                inc1_rule, inc2_rule, sample_id
            )
            if sample_t1_dist:
                results.append(sample_t1_dist)
        
        # T1: Multiple choice (always generate)
        sample_t1_mc = self.t1_converter.create_multi_choice_sample(
            conversation, correct1, correct2, incorrect1, incorrect2,
            inc1_rule, inc2_rule, sample_id
        )
        if sample_t1_mc:
            results.append(sample_t1_mc)
        
        # T4: Dialogue memory (for longer conversations)
        if len(conversation) >= 5:
            sample_t4_dialog = self.t4_converter.create_dialogue_memory_sample(
                conversation, correct1, correct2, sample_id
            )
            if sample_t4_dialog:
                results.append(sample_t4_dialog)
            
            # T4: Time recall (random chance)
            if random.random() < 0.3:
                sample_t4_recall = self.t4_converter.create_time_recall_sample(
                    conversation, correct1, correct2, sample_id
                )
                if sample_t4_recall:
                    results.append(sample_t4_recall)
        
        return results
    
    def convert_all(self, output_file: str, max_samples: int = None):
        """Convert all TimeDial data."""
        samples = self.load_data()
        all_results = []
        
        if max_samples:
            samples = samples[:max_samples]
        
        print("Converting samples...")
        for i, sample in enumerate(samples):
            sample_id = str(sample.get("id", i))
            converted = self.convert_sample(sample, sample_id)
            all_results.extend(converted)
            
            if i % 100 == 0:
                print(f"  Processed {i} samples, generated {len(all_results)} conversational samples")
        
        # Save output
        print(f"\nTotal converted: {len(all_results)} samples")
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in all_results:
                f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
        
        print(f"Saved to: {output_path}")
        
        # Print statistics
        self.print_statistics(all_results)
        
        return all_results
    
    def print_statistics(self, samples: List[ConversationalSample]):
        """Print conversion statistics."""
        print("\n" + "=" * 60)
        print("Conversion Summary")
        print("=" * 60)
        
        # Task distribution
        task_counts = {}
        for s in samples:
            task_counts[s.task] = task_counts.get(s.task, 0) + 1
        
        print(f"\nTotal samples: {len(samples)}")
        print("\nTask distribution:")
        for task, count in sorted(task_counts.items()):
            print(f"  {task}: {count}")
        
        # Subtask distribution
        subtask_counts = {}
        for s in samples:
            subtask_counts[s.sub_task] = subtask_counts.get(s.sub_task, 0) + 1
        
        print("\nSubtask distribution:")
        for subtask, count in sorted(subtask_counts.items()):
            print(f"  {subtask}: {count}")
        
        # Difficulty distribution
        diff_counts = {}
        for s in samples:
            diff_counts[s.difficulty] = diff_counts.get(s.difficulty, 0) + 1
        
        print("\nDifficulty distribution:")
        for diff, count in sorted(diff_counts.items()):
            print(f"  {diff}: {count}")

# =====================================================================
# Main Entry
# =====================================================================

def main():
    print("=" * 60)
    print("TimeDial Conversational Temporal Data Converter")
    print("=" * 60)
    
    converter = TimeDialConversationalConverter()
    output_file = "converted_data_v3/timedial_conversational.jsonl"
    
    samples = converter.convert_all(output_file)

if __name__ == "__main__":
    main()