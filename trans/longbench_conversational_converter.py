#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LongBench Conversational Temporal Data Converter

Converts LongBench dataset to conversational temporal awareness format.
Primary focus: T4 (Long-term Memory)
Secondary: T1 (Time Calculation), T5 (Counterfactual)

Output: converted_data_v3/longbench_conversational.jsonl
"""

import json
import random
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from pathlib import Path

# =====================================================================
# Data Structures
# =====================================================================

@dataclass
class ConversationalSample:
    task: str  # T1, T4, T5
    sub_task: str  # e.g., "T4-Convo-Buried", "T1-Convo-Multihop"
    context: str  # Original context (truncated for reference)
    conversation: List[Dict[str, str]]  # [{"role": "user/assistant", "content": "..."}]
    query: str
    answer: str
    state_info: Optional[Dict[str, Any]] = None
    ground_truth: Optional[Dict[str, Any]] = None
    difficulty: str = "medium"  # easy, medium, hard, very_hard
    source_id: Optional[str] = None

# =====================================================================
# Time Constants and Helpers
# =====================================================================

TIME_ANCHORS = [
    "Monday morning", "Tuesday afternoon", "Wednesday evening", 
    "Thursday night", "Friday", "Saturday", "Sunday",
    "next week", "last week", "tomorrow", "yesterday",
    "January 15", "March 3", "July 20", "December 25",
    "8:00 AM", "2:30 PM", "6:45 PM", "10:15 AM",
    "3:00", "noon", "midnight", "evening"
]

TIME_EXPRESSIONS = [
    "I have a meeting at {time}",
    "My appointment is scheduled for {time}",
    "The event starts at {time}",
    "I need to be there by {time}",
    "Let's meet at {time}",
    "The deadline is {time}",
    "I'm free after {time}",
    "The flight departs at {time}",
    "Dinner is at {time}",
    "The interview is on {time}"
]

DURATION_EXPRESSIONS = [
    "The meeting will last {duration}",
    "The event takes about {duration}",
    "I'll be busy for {duration}",
    "The session runs for {duration}",
    "It takes {duration} to complete"
]

DURATIONS = ["30 minutes", "1 hour", "2 hours", "45 minutes", "3 hours", "1.5 hours"]

NOISE_TIME_QUESTIONS = [
    "By the way, how's the weather?",
    "What did you eat for lunch?",
    "Did you see the game last night?",
    "I heard it's going to rain tomorrow.",
    "My neighbor has a new dog.",
    "The traffic was terrible this morning.",
    "I need to buy groceries later.",
    "Have you tried that new restaurant?",
    "My phone battery is almost dead.",
    "I forgot to water the plants."
]

# =====================================================================
# T4: Long-term Memory (Passage Retrieval)
# =====================================================================

class T4Converter:
    """Convert passage_retrieval data to T4 conversational format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def parse_paragraphs(self, context: str) -> List[str]:
        """Parse numbered paragraphs from context."""
        paragraphs = []
        current_para = []
        lines = context.split('\n')
        
        for line in lines:
            if line.startswith('Paragraph ') and ':' in line:
                if current_para:
                    paragraphs.append('\n'.join(current_para))
                    current_para = []
                # Extract paragraph content after "Paragraph N:"
                parts = line.split(':', 1)
                if len(parts) > 1:
                    current_para.append(parts[1].strip())
            else:
                current_para.append(line)
        
        if current_para:
            paragraphs.append('\n'.join(current_para))
        
        return paragraphs
    
    def create_buried_time_sample(self, paragraphs: List[str], original_answer: str, 
                                    source_id: str) -> Optional[ConversationalSample]:
        """T4-Convo-Buried: Bury time information early in long text."""
        if len(paragraphs) < 5:
            return None
        
        # Select a paragraph to contain the key time information
        key_para_idx = random.randint(0, min(5, len(paragraphs) - 1))
        key_para = paragraphs[key_para_idx]
        
        # Generate time anchor
        time_anchor = random.choice(TIME_ANCHORS)
        time_expr = random.choice(TIME_EXPRESSIONS).format(time=time_anchor)
        
        # Create conversation with buried time info
        conversation = []
        
        # Round 1: Embed time information in context
        conversation.append({
            "role": "user",
            "content": f"Let me tell you about something important. {time_expr.lower()}. {key_para}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Got it, I've noted that you have something scheduled for {time_anchor}."
        })
        
        # Rounds 2-4: Add noise paragraphs
        noise_count = min(3, len(paragraphs) - 1)
        noise_paras = random.sample([p for i, p in enumerate(paragraphs) if i != key_para_idx], 
                                    min(noise_count, len(paragraphs) - 1))
        
        for i, para in enumerate(noise_paras[:3]):
            # Inject time noise
            noise_time = random.choice(TIME_ANCHORS)
            noise_question = random.choice(NOISE_TIME_QUESTIONS)
            
            conversation.append({
                "role": "user",
                "content": f"{para[:150]}... {noise_question}"
            })
            
            conversation.append({
                "role": "assistant",
                "content": "I see. Noted."
            })
        
        # Final query
        conversation.append({
            "role": "user",
            "content": "What important time did I mention earlier?"
        })
        
        return ConversationalSample(
            task="T4",
            sub_task="T4-Convo-Buried",
            context=key_para,
            conversation=conversation,
            query="What important time did I mention earlier?",
            answer=time_anchor,
            state_info={
                "type": "buried_time",
                "key_paragraph_idx": key_para_idx,
                "time_anchor": time_anchor,
                "noise_paragraphs": noise_count
            },
            ground_truth={
                "time_anchor": time_anchor,
                "paragraph_location": "early"
            },
            difficulty="hard",
            source_id=f"longbench_t4_buried_{source_id}"
        )
    
    def create_noisy_retrieval_sample(self, paragraphs: List[str], original_answer: str,
                                       source_id: str) -> Optional[ConversationalSample]:
        """T4-Convo-Noisy: Retrieve info with time noise interference."""
        if len(paragraphs) < 10:
            return None
        
        # Select a paragraph in middle or late position
        key_para_idx = random.randint(5, len(paragraphs) - 1)
        key_para = paragraphs[key_para_idx]
        
        # Extract potential time entities from paragraph (simple heuristic)
        key_time = random.choice(TIME_ANCHORS)
        
        # Create conversation with time noise
        conversation = []
        
        # Embed key info in mid-conversation
        conversation.append({
            "role": "user",
            "content": f"Here's something: {key_para}... Also, important: the deadline is {key_time}."
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"I understand. You mentioned something about {key_time}."
        })
        
        # Add distracting time mentions
        for _ in range(random.randint(2, 4)):
            fake_time = random.choice(TIME_ANCHORS)
            noise = random.choice(NOISE_TIME_QUESTIONS)
            
            conversation.append({
                "role": "user",
                "content": f"Oh, and I also have something at {fake_time}. {noise}"
            })
            
            conversation.append({
                "role": "assistant",
                "content": f"Okay, noted: {fake_time}."
            })
        
        # Query
        conversation.append({
            "role": "user",
            "content": "What was the important deadline I mentioned?"
        })
        
        return ConversationalSample(
            task="T4",
            sub_task="T4-Convo-Noisy",
            context=key_para,
            conversation=conversation,
            query="What was the important deadline I mentioned?",
            answer=key_time,
            state_info={
                "type": "noisy_retrieval",
                "key_time": key_time,
                "distractor_count": 3
            },
            ground_truth={
                "correct_time": key_time,
                "location": "middle"
            },
            difficulty="very_hard",
            source_id=f"longbench_t4_noisy_{source_id}"
        )
    
    def create_distractor_sample(self, paragraphs: List[str], original_answer: str,
                                  source_id: str) -> Optional[ConversationalSample]:
        """T4-Convo-Distractor: Multiple similar time mentions, find the correct one."""
        if len(paragraphs) < 5:
            return None
        
        key_time = random.choice(TIME_ANCHORS)
        # Generate similar but different times
        similar_times = [random.choice(TIME_ANCHORS) for _ in range(3)]
        
        # Create conversation
        conversation = []
        
        # Round 1: Key time
        conversation.append({
            "role": "user",
            "content": f"I have an important meeting at {key_time}."
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Meeting noted for {key_time}."
        })
        
        # Round 2-4: Similar times as distractors
        contexts_used = set()
        for i, sim_time in enumerate(similar_times):
            para_idx = random.randint(0, len(paragraphs) - 1)
            if para_idx not in contexts_used:
                contexts_used.add(para_idx)
                para = paragraphs[para_idx][:100]
                
                conversation.append({
                    "role": "user",
                    "content": f"{para}... By the way, also meeting at {sim_time}."
                })
                
                conversation.append({
                    "role": "assistant",
                    "content": f"Okay, another meeting at {sim_time}."
                })
        
        # Query
        conversation.append({
            "role": "user",
            "content": "What time is my IMPORTANT meeting? Not the other ones."
        })
        
        return ConversationalSample(
            task="T4",
            sub_task="T4-Convo-Distractor",
            context=paragraphs[0][:200] if paragraphs else "",
            conversation=conversation,
            query="What time is my IMPORTANT meeting?",
            answer=key_time,
            state_info={
                "type": "distractor_resolution",
                "key_time": key_time,
                "distractor_times": similar_times
            },
            ground_truth={
                "correct_time": key_time,
                "distractors": similar_times
            },
            difficulty="hard",
            source_id=f"longbench_t4_dist_{source_id}"
        )

# =====================================================================
# T1: Time Calculation (Multi-hop Reasoning)
# =====================================================================

class T1Converter:
    """Convert 2wikimqa data to T1 conversational format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_multihop_time_sample(self, input_text: str, context: str, 
                                      answer: str, source_id: str) -> Optional[ConversationalSample]:
        """T1-Convo-Multihop: Multi-hop time reasoning."""
        # Parse passages
        passages = self.parse_passages(context)
        if len(passages) < 2:
            return None
        
        # Create conversation
        conversation = []
        
        # Generate time parameters for calculation
        start_time = random.choice(["9:00 AM", "2:00 PM", "10:30 AM", "3:45 PM"])
        duration1 = random.choice(["1 hour", "45 minutes", "2 hours", "30 minutes"])
        duration2 = random.choice(["30 minutes", "1 hour", "15 minutes", "45 minutes"])
        
        # Round 1: First time constraint
        passage1 = passages[0][:200]
        conversation.append({
            "role": "user",
            "content": f"I'm reading about something. {passage1}... Also, my meeting starts at {start_time}."
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Okay, meeting at {start_time}. Could you tell me more?"
        })
        
        # Round 2: Second piece of information
        if len(passages) > 1:
            passage2 = passages[1][:200]
            conversation.append({
                "role": "user",
                "content": f"{passage2}... The meeting lasts {duration1}."
            })
            
            conversation.append({
                "role": "assistant",
                "content": f"Got it, {duration1} meeting starting at {start_time}."
            })
        
        # Round 3: Add calculation complexity
        conversation.append({
            "role": "user",
            "content": f"After that, I have another task that takes {duration2}."
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Understood. {duration2} for the next task."
        })
        
        # Add distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_TIME_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I don't have information about that."
        })
        
        # Query - calculate end time
        conversation.append({
            "role": "user",
            "content": f"If I start at {start_time}, spend {duration1} then {duration2}, when will I finish?"
        })
        
        # Simple time calculation for answer
        answer_time = self.calculate_end_time(start_time, duration1, duration2)
        
        return ConversationalSample(
            task="T1",
            sub_task="T1-Convo-Multihop",
            context=passages[0][:200] if passages else "",
            conversation=conversation,
            query=f"If I start at {start_time}, spend {duration1} then {duration2}, when will I finish?",
            answer=answer_time,
            state_info={
                "type": "multihop_calculation",
                "start_time": start_time,
                "duration1": duration1,
                "duration2": duration2
            },
            ground_truth={
                "start": start_time,
                "durations": [duration1, duration2],
                "end_time": answer_time
            },
            difficulty="medium",
            source_id=f"longbench_t1_multihop_{source_id}"
        )
    
    def create_duration_chain_sample(self, input_text: str, context: str,
                                       answer: str, source_id: str) -> Optional[ConversationalSample]:
        """T1-Convo-Duration: Chain of time calculations."""
        passages = self.parse_passages(context)
        
        conversation = []
        
        # Create time chain
        times = random.sample(["30 minutes", "45 minutes", "1 hour", "15 minutes", "20 minutes"], 3)
        activities = ["Task A", "Task B", "Task C"]
        
        for i, (time, activity) in enumerate(zip(times, activities)):
            if i < len(passages):
                passage_excerpt = passages[i][:100]
            else:
                passage_excerpt = "Another task."
            
            conversation.append({
                "role": "user",
                "content": f"{passage_excerpt}... {activity} takes {time}."
            })
            
            conversation.append({
                "role": "assistant",
                "content": f"Noted, {activity} takes {time}."
            })
        
        # Add distraction
        conversation.append({
            "role": "user",
            "content": "What's for dinner?"  # Noise
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I don't have information about dinner plans."
        })
        
        # Query
        conversation.append({
            "role": "user",
            "content": "How much total time for all tasks?"
        })
        
        # Calculate total
        total_minutes = sum(self.parse_duration(t) for t in times)
        total_answer = self.format_duration(total_minutes)
        
        return ConversationalSample(
            task="T1",
            sub_task="T1-Convo-Duration",
            context=passages[0][:200] if passages else "",
            conversation=conversation,
            query="How much total time for all tasks?",
            answer=total_answer,
            state_info={
                "type": "duration_chain",
                "times": times,
                "activities": activities
            },
            ground_truth={
                "times": times,
                "total_minutes": total_minutes
            },
            difficulty="easy",
            source_id=f"longbench_t1_duration_{source_id}"
        )
    
    def parse_passages(self, context: str) -> List[str]:
        """Parse numbered passages from context."""
        passages = []
        current = []
        
        for line in context.split('\n'):
            if line.startswith('Passage ') and ':' in line:
                if current:
                    passages.append('\n'.join(current))
                    current = []
                parts = line.split(':', 1)
                if len(parts) > 1:
                    current.append(parts[1].strip())
            else:
                current.append(line)
        
        if current:
            passages.append('\n'.join(current))
        
        return passages
    
    def parse_duration(self, duration: str) -> int:
        """Parse duration string to minutes."""
        duration = duration.lower()
        if "hour" in duration:
            hours = 1
            if "1.5" in duration or "one and a half" in duration:
                return 90
            if "2" in duration:
                return 120
            if "3" in duration:
                return 180
            return 60
        elif "minute" in duration:
            import re
            match = re.search(r'(\d+)', duration)
            return int(match.group(1)) if match else 30
        return 30
    
    def calculate_end_time(self, start: str, *durations) -> str:
        """Calculate end time from start and durations."""
        # Parse start time
        import re
        match = re.search(r'(\d+):?(\d+)?\s*(AM|PM)?', start, re.I)
        if not match:
            return "Approximately 1-2 hours later"
        
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        am_pm = match.group(3).upper() if match.group(3) else "AM"
        
        if am_pm == "PM" and hour != 12:
            hour += 12
        elif am_pm == "AM" and hour == 12:
            hour = 0
        
        # Add durations
        total_minutes = sum(self.parse_duration(d) for d in durations)
        end_hour = hour + (minute + total_minutes) // 60
        end_minute = (minute + total_minutes) % 60
        
        # Convert back to 12-hour format
        end_am_pm = "AM" if end_hour % 24 < 12 else "PM"
        display_hour = end_hour % 12
        if display_hour == 0:
            display_hour = 12
        
        return f"{display_hour}:{end_minute:02d} {end_am_pm}"
    
    def format_duration(self, minutes: int) -> str:
        """Format minutes as duration string."""
        if minutes >= 60:
            hours = minutes // 60
            mins = minutes % 60
            if mins == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            return f"{hours} hour{'s' if hours > 1 else ''} {mins} minutes"
        return f"{minutes} minutes"

# =====================================================================
# T5: Counterfactual (Rule Perturbation)
# =====================================================================

class T5Converter:
    """Convert data to T5 counterfactual conversational format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_rule_change_sample(self, context: str, answer: str,
                                   source_id: str) -> Optional[ConversationalSample]:
        """T5-Convo-RuleChange: Counterfactual time rules."""
        conversation = []
        
        # Generate counterfactual rule
        rules = [
            ("In this world, 1 hour = 100 minutes (not 60).", 100/60),
            ("In this world, a day has 25 hours (not 24).", 25/24),
            ("In this world, meetings take DOUBLE the scheduled time.", 2.0),
            ("In this world, 1 hour = 50 minutes.", 50/60),
        ]
        
        rule, multiplier = random.choice(rules)
        
        # Original time calculation
        original_time = random.choice(["9:00 AM", "2:00 PM", "10:00 AM", "3:00 PM"])
        original_duration = random.choice(["1 hour", "2 hours", "30 minutes", "1.5 hours"])
        
        # Round 1: Establish counterfactual rule
        conversation.append({
            "role": "user",
            "content": f"Let's imagine a different world. {rule}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"I understand. In this world, {rule.lower()}"
        })
        
        # Round 2: Add context with time calculation
        conversation.append({
            "role": "user",
            "content": f"In this world, I have a meeting starting at {original_time} that lasts {original_duration}."
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Okay, meeting at {original_time} for {original_duration} in this special world."
        })
        
        # Round 3: Add distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_TIME_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I don't have information about that in this world."
        })
        
        # Round 4: Ask about real world vs counterfactual
        conversation.append({
            "role": "user",
            "content": f"In the REAL world (not the special world), {rule.lower()} Wait, that's not right! In the real world, that's NOT true. What's correct in the REAL world?"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"In the real world, {self.get_real_world_correction(rule)}"
        })
        
        # Query: Apply counterfactual rule
        conversation.append({
            "role": "user",
            "content": f"Back to the special world. If my meeting is {original_duration} in that world, how many minutes is that?"
        })
        
        # Calculate counterfactual answer
        answer_minutes = self.calculate_counterfactual_minutes(original_duration, multiplier)
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-RuleChange",
            context=context[:200],
            conversation=conversation,
            query=f"If my meeting is {original_duration} in this special world, how many minutes is that?",
            answer=answer_minutes,
            state_info={
                "type": "counterfactual_rule",
                "rule": rule,
                "multiplier": multiplier,
                "original_duration": original_duration
            },
            ground_truth={
                "rule": rule,
                "real_world_duration": original_duration,
                "counterfactual_minutes": answer_minutes
            },
            difficulty="very_hard",
            source_id=f"longbench_t5_rule_{source_id}"
        )
    
    def create_context_confusion_sample(self, input_text: str, context: str,
                                          answer: str, source_id: str) -> Optional[ConversationalSample]:
        """T5-Convo-Confusion: Rule confusion between contexts."""
        conversation = []
        
        # Establish time context
        time_a = "9:00 AM"
        time_b = "2:00 PM"
        
        # Round 1: First context with rule
        conversation.append({
            "role": "user",
            "content": f"Context A: Meeting at {time_a}. The rule is: if a meeting is before noon, it's SHORT (30 min)."
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Understood. Meetings before noon are short (30 min). Meeting A at {time_a}."
        })
        
        # Round 2: Second context with different rule
        conversation.append({
            "role": "user",
            "content": f"Context B: Meeting at {time_b}. The rule is: if a meeting is after noon, it's LONG (2 hours)."
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Understood. Meetings after noon are long (2 hours). Meeting B at {time_b}."
        })
        
        # Round 3: Distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_TIME_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I don't have information about that."
        })
        
        # Query: Test rule application
        conversation.append({
            "role": "user",
            "content": "For Meeting A, how long is it? And for Meeting B?"
        })
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-Confusion",
            context=context[:200],
            conversation=conversation,
            query="For Meeting A, how long is it? And for Meeting B?",
            answer=f"Meeting A ({time_a}, before noon): 30 minutes (short). Meeting B ({time_b}, after noon): 2 hours (long).",
            state_info={
                "type": "context_confusion",
                "time_a": time_a,
                "time_b": time_b,
                "rule_a": "before noon = short",
                "rule_b": "after noon = long"
            },
            ground_truth={
                "meeting_a_duration": "30 minutes",
                "meeting_b_duration": "2 hours"
            },
            difficulty="hard",
            source_id=f"longbench_t5_conf_{source_id}"
        )
    
    def calculate_counterfactual_minutes(self, duration: str, multiplier: float) -> str:
        """Calculate minutes under counterfactual rules."""
        import re
        match = re.search(r'(\d+\.?\d*)', duration)
        if not match:
            return "100 minutes"
        
        value = float(match.group(1))
        if "hour" in duration.lower():
            # Hours to minutes
            real_minutes = value * 60
            counterfactual_minutes = int(real_minutes * multiplier)
            return f"{counterfactual_minutes} minutes"
        else:
            # Already minutes
            counterfactual_minutes = int(value * multiplier)
            return f"{counterfactual_minutes} minutes"
    
    def get_real_world_correction(self, rule: str) -> str:
        """Get real-world correction for counterfactual rule."""
        corrections = {
            "1 hour = 100 minutes": "1 hour equals 60 minutes.",
            "a day has 25 hours": "a day has 24 hours.",
            "meetings take DOUBLE": "meetings take exactly their scheduled time.",
            "1 hour = 50 minutes": "1 hour equals 60 minutes."
        }
        for key, correction in corrections.items():
            if key in rule:
                return correction
        return "the standard rules apply."

# =====================================================================
# Main Converter
# =====================================================================

class LongBenchConversationalConverter:
    """Main converter for LongBench to conversational temporal format."""
    
    def __init__(self, data_dir: str = "data/LongBench/data"):
        self.data_dir = Path(data_dir)
        self.t4_converter = T4Converter()
        self.t1_converter = T1Converter()
        self.t5_converter = T5Converter()
        
    def load_jsonl(self, filename: str, max_samples: int = None) -> List[Dict]:
        """Load JSONL file."""
        filepath = self.data_dir / filename
        samples = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if max_samples and i >= max_samples:
                    break
                samples.append(json.loads(line.strip()))
        return samples
    
    def convert_sample(self, sample: Dict, sample_id: int, source_file: str) -> List[ConversationalSample]:
        """Convert a single sample to multiple conversational samples."""
        results = []
        
        input_text = sample.get('input', '')
        context = sample.get('context', '')
        answer = sample.get('answers', [''])[0] if isinstance(sample.get('answers'), list) else sample.get('answers', '')
        source_id = f"{source_file}_{sample_id}"
        
        # T4 samples (if passage structure exists)
        if 'passage' in source_file.lower() or 'retrieval' in source_file.lower():
            paragraphs = self.t4_converter.parse_paragraphs(context)
            
            # T4-Convo-Buried
            sample_t4_buried = self.t4_converter.create_buried_time_sample(
                paragraphs, answer, source_id
            )
            if sample_t4_buried:
                results.append(sample_t4_buried)
            
            # T4-Convo-Noisy
            sample_t4_noisy = self.t4_converter.create_noisy_retrieval_sample(
                paragraphs, answer, source_id
            )
            if sample_t4_noisy:
                results.append(sample_t4_noisy)
            
            # T4-Convo-Distractor
            sample_t4_dist = self.t4_converter.create_distractor_sample(
                paragraphs, answer, source_id
            )
            if sample_t4_dist:
                results.append(sample_t4_dist)
        
        # T1 samples (if wiki/multihop structure)
        if 'wiki' in source_file.lower() or 'hotpot' in source_file.lower() or 'musique' in source_file.lower():
            # T1-Convo-Multihop
            sample_t1_multihop = self.t1_converter.create_multihop_time_sample(
                input_text, context, answer, source_id
            )
            if sample_t1_multihop:
                results.append(sample_t1_multihop)
            
            # T1-Convo-Duration
            sample_t1_duration = self.t1_converter.create_duration_chain_sample(
                input_text, context, answer, source_id
            )
            if sample_t1_duration:
                results.append(sample_t1_duration)
        
        # T5 samples (for any long context)
        if len(context) > 1000:  # Only for sufficiently long contexts
            # T5-Convo-RuleChange
            sample_t5_rule = self.t5_converter.create_rule_change_sample(
                context, answer, source_id
            )
            if sample_t5_rule:
                results.append(sample_t5_rule)
            
            # T5-Convo-Confusion
            sample_t5_conf = self.t5_converter.create_context_confusion_sample(
                input_text, context, answer, source_id
            )
            if sample_t5_conf:
                results.append(sample_t5_conf)
        
        return results
    
    def convert_all(self, output_file: str, max_samples_per_file: int = None):
        """Convert all LongBench data to conversational format."""
        all_samples = []
        
        # Process passage retrieval files (T4 focus)
        passage_files = [
            'passage_retrieval_en.jsonl',
            'passage_retrieval_zh.jsonl'
        ]
        
        for file in passage_files:
            if (self.data_dir / file).exists():
                print(f"Processing {file}...")
                samples = self.load_jsonl(file, max_samples_per_file)
                for i, sample in enumerate(samples):
                    converted = self.convert_sample(sample, i, file.replace('.jsonl', ''))
                    all_samples.extend(converted)
        
        # Process multihop files (T1 focus)
        multihop_files = [
            '2wikimqa.jsonl',
            'hotpotqa.jsonl',
            'musique.jsonl'
        ]
        
        for file in multihop_files:
            if (self.data_dir / file).exists():
                print(f"Processing {file}...")
                samples = self.load_jsonl(file, max_samples_per_file)
                for i, sample in enumerate(samples):
                    converted = self.convert_sample(sample, i, file.replace('.jsonl', ''))
                    all_samples.extend(converted)
        
        # Process long context files (T5 focus)
        long_context_files = [
            'samsum.jsonl',  # Dialogue
            'qasper.jsonl',  # Research paper QA
            'multifieldqa_en.jsonl'  # Multi-field
        ]
        
        for file in long_context_files:
            if (self.data_dir / file).exists():
                print(f"Processing {file}...")
                samples = self.load_jsonl(file, max_samples_per_file)
                for i, sample in enumerate(samples):
                    converted = self.convert_sample(sample, i, file.replace('.jsonl', ''))
                    all_samples.extend(converted)
        
        # Save to output
        print(f"\nTotal converted: {len(all_samples)} samples")
        
        # Write JSONL
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in all_samples:
                f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
        
        print(f"Saved to: {output_path}")
        
        # Print statistics
        self.print_statistics(all_samples)
        
        return all_samples
    
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
    print("LongBench Conversational Temporal Data Converter")
    print("=" * 60)
    
    converter = LongBenchConversationalConverter()
    output_file = "converted_data_v3/longbench_conversational.jsonl"
    
    # Limit samples per file to avoid massive output
    max_samples = 500  # Per file
    
    samples = converter.convert_all(output_file, max_samples_per_file=max_samples)

if __name__ == "__main__":
    main()