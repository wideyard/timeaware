#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIQA Conversational Temporal Data Converter

Converts PIQA (Physical Interaction QA) dataset to conversational format.
Primary focus: T2 (State Update), T5 (Counterfactual)

Key features:
- Physical commonsense reasoning
- Wrong answer as correct in parallel universe (T5)
- Action timeline for state tracking (T2)

Output: converted_data_v3/piqa_conversational.jsonl
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
    task: str  # T2, T3, T5
    sub_task: str  # e.g., "T2-Convo-State", "T5-Convo-Counterfactual"
    context: str  # Goal/question
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

# Physical state transition patterns
PHYSICAL_TRANSITIONS = {
    "boiling": {"before": "solid/liquid", "after": "liquid/gas", "action": "heat"},
    "freezing": {"before": "liquid", "after": "solid", "action": "cool"},
    "melting": {"before": "solid", "after": "liquid", "action": "heat"},
    "cooking": {"before": "raw", "after": "cooked", "action": "heat"},
    "burning": {"before": "intact", "after": "burned/destroyed", "action": "fire"},
    "cutting": {"before": "whole", "after": "pieces", "action": "cut"},
    "pouring": {"before": "in container A", "after": "in container B", "action": "transfer"},
    "attaching": {"before": "separate", "after": "connected", "action": "join"},
}

# Noise questions for distraction
NOISE_QUESTIONS = [
    "By the way, what's for dinner?",
    "I heard about a new movie.",
    "The weather is nice today.",
    "My neighbor's dog is barking.",
    "I need to check my emails.",
    "What time is it?",
    "Did you watch the game?",
    "I forgot to water the plants.",
    "The traffic was heavy this morning.",
    "What's your favorite color?"
]

# Counterfactual world rules
COUNTERFACTUAL_RULES = [
    "In this parallel universe, metal is soft like wood and can be easily nailed.",
    "In this world, water boils at room temperature.",
    "In this reality, wood is stronger than metal.",
    "In this dimension, heat makes things colder.",
    "In this parallel universe, gravity works in reverse.",
    "In this world, liquids freeze when heated.",
    "In this alternate reality, solids become gas when burned.",
    "In this universe, fire creates ice instead of heat.",
    "In this world, glass is flexible like rubber.",
    "In this parallel dimension, plastic melts at freezing temperatures."
]

def truncate_text(text: str, max_len: int = 300) -> str:
    """Truncate text to max length."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(' ', 1)[0] + '...'

def extract_physical_keywords(goal: str) -> List[str]:
    """Extract physical action keywords from goal."""
    keywords = []
    action_words = ["boil", "freeze", "melt", "cook", "burn", "cut", "pour", 
                    "attach", "we", "put", "place", "heat", "cool", "mix", "seal"]
    goal_lower = goal.lower()
    for word in action_words:
        if word in goal_lower:
            keywords.append(word)
    return keywords

# =====================================================================
# T2: State Update Converter
# =====================================================================

class T2Converter:
    """Convert PIQA data to T2 state tracking format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_state_timeline_sample(self, goal: str, sol1: str, sol2: str,
                                      correct_idx: int, source_id: str) -> Optional[ConversationalSample]:
        """T2-Convo-Timeline: Track physical state through timeline."""
        conversation = []
        
        # Detect if this is about physical transformation
        keywords = extract_physical_keywords(goal)
        if not keywords:
            return None
        
        correct_answer = sol1 if correct_idx == 0 else sol2
        
        # Create a timeline
        times = ["2:00 PM", "2:05 PM", "2:10 PM", "2:15 PM"]
        
        # Round 1: Initial state
        conversation.append({
            "role": "user",
            "content": f"At {times[0]}, I started the following task: {goal}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Okay, you're working on: {goal[:100]}"
        })
        
        # Round 2: Action progress
        conversation.append({
            "role": "user",
            "content": f"At {times[1]}, I was in the middle of the process."
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I understand, you're still working on it."
        })
        
        # Round 3: Distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let me focus on your task progress."
        })
        
        # Round 4: Action completion
        conversation.append({
            "role": "user",
            "content": f"At {times[2]}, I completed the action: {correct_answer}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Got it, you {correct_answer[:80]}."
        })
        
        # Query about end state
        query = f"Now it's {times[3]}. What is the current state of the object/item?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        # Infer final state based on action
        final_state = self._infer_final_state(goal, correct_answer)
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Timeline",
            context=truncate_text(f"{goal} {correct_answer}", 200),
            conversation=conversation,
            query=query,
            answer=final_state,
            state_info={
                "type": "physical_timeline",
                "goal": goal,
                "action": correct_answer,
                "times": times
            },
            ground_truth={
                "correct_answer": correct_answer,
                "correct_index": correct_idx
            },
            difficulty="medium",
            source_id=f"piqa_t2_timeline_{source_id}"
        )
    
    def create_action_sequence_sample(self, goal: str, sol1: str, sol2: str,
                                       correct_idx: int, source_id: str) -> Optional[ConversationalSample]:
        """T2-Convo-Sequence: Track state through action sequence."""
        conversation = []
        
        correct_answer = sol1 if correct_idx == 0 else sol2
        wrong_answer = sol2 if correct_idx == 0 else sol1
        
        # Round 1: Goal presentation
        conversation.append({
            "role": "user",
            "content": f"I want to accomplish this: {goal}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"What are you planning to do for: {goal[:80]}?"
        })
        
        # Round 2: Action choice
        conversation.append({
            "role": "user",
            "content": f"I have two options: Option A: {sol1[:60]}... Option B: {sol2[:60]}..."
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Which option will you choose?"
        })
        
        # Round 3: Choose correct action
        conversation.append({
            "role": "user",
            "content": f"I chose Option {'A' if correct_idx == 0 else 'B'}."
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Okay, you chose: {correct_answer[:80]}."
        })
        
        # Round 4: Distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let me stay focused on your task."
        })
        
        # Query about result
        query = "After completing this action, what will be the result?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        # Expected result
        result = self._infer_result(goal, correct_answer)
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Sequence",
            context=truncate_text(f"{goal}", 150),
            conversation=conversation,
            query=query,
            answer=result,
            state_info={
                "type": "action_sequence",
                "goal": goal,
                "chosen_action": correct_answer
            },
            ground_truth={
                "correct_answer": correct_answer,
                "wrong_answer": wrong_answer
            },
            difficulty="medium",
            source_id=f"piqa_t2_seq_{source_id}"
        )
    
    def _infer_final_state(self, goal: str, action: str) -> str:
        """Infer final state from goal and action."""
        goal_lower = goal.lower()
        
        # Physical state transitions
        if "boil" in goal_lower or "heat" in goal_lower:
            return "The substance is now in liquid or gaseous form due to heating."
        elif "freeze" in goal_lower or "cool" in goal_lower:
            return "The substance has solidified due to cooling."
        elif "cut" in goal_lower or "break" in goal_lower:
            return "The object has been divided into smaller pieces."
        elif "attach" in goal_lower or "connect" in goal_lower:
            return "The parts are now firmly connected together."
        elif "pour" in goal_lower or "transfer" in goal_lower:
            return "The substance has been moved to a new container."
        else:
            return f"The action '{action[:50]}' has been completed successfully."
    
    def _infer_result(self, goal: str, action: str) -> str:
        """Infer result from action."""
        return f"The task is completed. The result is: {action[:80]}"

# =====================================================================
# T3: Conflict Detection Converter
# =====================================================================

class T3Converter:
    """Convert PIQA data to T3 conflict detection format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_resource_conflict_sample(self, goal: str, sol1: str, sol2: str,
                                         correct_idx: int, source_id: str) -> Optional[ConversationalSample]:
        """T3-Convo-Resource: Detect physical resource/compatibility conflicts."""
        conversation = []
        
        correct_answer = sol1 if correct_idx == 0 else sol2
        wrong_answer = sol2 if correct_idx == 0 else sol1
        
        # Round 1: Present conflicting options
        conversation.append({
            "role": "user",
            "content": f"I have a goal: {goal}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"What are you trying to accomplish?"
        })
        
        # Round 2: Present two options
        conversation.append({
            "role": "user",
            "content": f"I'm considering two approaches:\nApproach A: {sol1}\nApproach B: {sol2}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let me think about which approach is more appropriate."
        })
        
        # Round 3: Distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let me focus on evaluating these approaches."
        })
        
        # Query about conflict
        query = "Is there any issue with either approach? Which one should I use?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        # Generate answer explaining the correct choice
        wrong_letter = 'B' if correct_idx == 0 else 'A'
        correct_letter = 'A' if correct_idx == 0 else 'B'
        
        answer = f"Approach {correct_letter} ({correct_answer}) is the correct approach. "
        answer += f"Approach {wrong_letter} ({wrong_answer[:50]}) would not work properly for this goal."
        
        return ConversationalSample(
            task="T3",
            sub_task="T3-Convo-Resource",
            context=truncate_text(f"{goal}", 150),
            conversation=conversation,
            query=query,
            answer=answer,
            state_info={
                "type": "resource_conflict",
                "goal": goal,
                "correct_option": correct_answer,
                "wrong_option": wrong_answer
            },
            ground_truth={
                "correct_answer_idx": correct_idx,
                "task_type": "physical_appropriateness"
            },
            difficulty="medium",
            source_id=f"piqa_t3_resource_{source_id}"
        )

# =====================================================================
# T5: Counterfactual Converter
# =====================================================================

class T5Converter:
    """Convert PIQA data to T5 counterfactual format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_counterfactual_sample(self, goal: str, sol1: str, sol2: str,
                                       correct_idx: int, source_id: str) -> Optional[ConversationalSample]:
        """T5-Convo-Counterfactual: Wrong answer becomes correct in parallel universe."""
        conversation = []
        
        # Get wrong answer (which will be correct in counterfactual world)
        wrong_answer = sol1 if correct_idx == 1 else sol2
        correct_answer = sol2 if correct_idx == 1 else sol1
        
        # Round 1: Introduce counterfactual world
        counterfactual_rule = random.choice(COUNTERFACTUAL_RULES)
        conversation.append({
            "role": "user",
            "content": f"Let me tell you about a parallel universe. {counterfactual_rule}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"I understand. In this parallel universe, different physical rules apply."
        })
        
        # Round 2: Present goal in this universe
        conversation.append({
            "role": "user",
            "content": f"In this universe, {goal}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Okay, with {goal[:60]}..."
        })
        
        # Round 3: Present options
        conversation.append({
            "role": "user",
            "content": f"Which approach should I use?\nA: {sol1}\nB: {sol2}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I need to consider the physical rules in this parallel universe."
        })
        
        # Round 4: Distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let me focus on the physics of this universe."
        })
        
        # Query
        query = "Based on the rules of this parallel universe, which option is correct?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        # In counterfactual world, the originally wrong answer is correct
        counterfactual_answer = f"In this parallel universe, option {'A' if correct_idx == 1 else 'B'} is correct: {wrong_answer}"
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-Counterfactual",
            context=truncate_text(f"{goal}", 150),
            conversation=conversation,
            query=query,
            answer=counterfactual_answer,
            state_info={
                "type": "counterfactual_physics",
                "original_correct": correct_answer,
                "counterfactual_correct": wrong_answer,
                "rule": counterfactual_rule
            },
            ground_truth={
                "original_correct_idx": correct_idx,
                "counterfactual_correct_idx": 1 - correct_idx,
                "anti_data_pollution": True
            },
            difficulty="hard",
            source_id=f"piqa_t5_cf_{source_id}"
        )
    
    def create_rule_reverse_sample(self, goal: str, sol1: str, sol2: str,
                                     correct_idx: int, source_id: str) -> Optional[ConversationalSample]:
        """T5-Convo-RuleReverse: Test if model follows new rules vs pre-training."""
        conversation = []
        
        wrong_answer = sol1 if correct_idx == 1 else sol2
        correct_answer = sol2 if correct_idx == 1 else sol1
        
        # Round 1: Define new reality
        conversation.append({
            "role": "user",
            "content": "In this world, physical properties are reversed from what you know."
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I'll remember that physical properties are reversed here."
        })
        
        # Round 2: Present specific reversal
        reversal = self._generate_reversal(goal)
        conversation.append({
            "role": "user",
            "content": f"Specifically, {reversal}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I understand the reversed physics in this world."
        })
        
        # Round 3: Goal
        conversation.append({
            "role": "user",
            "content": f"Now, {goal}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Given the reversed physics, how should I approach: {goal[:60]}?"
        })
        
        # Round 4: Options
        conversation.append({
            "role": "user",
            "content": f"Options: A) {sol1}  B) {sol2}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let me think about which option aligns with the reversed rules."
        })
        
        # Query
        query = "Based on the reversed reality, which option is correct?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        reversed_answer = f"With reversed physics, option {'A' if correct_idx == 1 else 'B'} is correct: {wrong_answer}"
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-RuleReverse",
            context=truncate_text(f"{goal}", 150),
            conversation=conversation,
            query=query,
            answer=reversed_answer,
            state_info={
                "type": "rule_reversal",
                "reversal": reversal,
                "original_correct": correct_answer
            },
            ground_truth={
                "original_correct_idx": correct_idx,
                "reversed_correct_idx": 1 - correct_idx
            },
            difficulty="hard",
            source_id=f"piqa_t5_reverse_{source_id}"
        )
    
    def create_choice_inversion_sample(self, goal: str, sol1: str, sol2: str,
                                        correct_idx: int, source_id: str) -> Optional[ConversationalSample]:
        """T5-Convo-ChoiceInversion: Same goal, opposite correct choice."""
        conversation = []
        
        wrong_answer = sol1 if correct_idx == 1 else sol2
        correct_answer = sol2 if correct_idx == 1 else sol1
        
        # Round 1: Normal world question
        conversation.append({
            "role": "user",
            "content": f"In the NORMAL world, {goal}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"In the normal world, to {goal[:60]}, I would use the physically correct approach."
        })
        
        # Round 2: Normal answer
        conversation.append({
            "role": "user",
            "content": f"What about options A ({sol1[:40]}) vs B ({sol2[:40]})?"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"In the normal world, option {'A' if correct_idx == 0 else 'B'} is correct."
        })
        
        # Round 3: Switch to reverse world
        conversation.append({
            "role": "user",
            "content": "But NOW we're in an OPPOSITE world where physics is reversed!"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "In the opposite world, the normally wrong approach becomes correct."
        })
        
        # Round 4: Same goal in reverse world
        conversation.append({
            "role": "user",
            "content": f"In this OPPOSITE world, {goal}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I need to rethink with reversed physics."
        })
        
        # Query
        query = f"Same options (A: {sol1}, B: {sol2}). Which is correct in the OPPOSITE world?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        inverted_answer = f"In the opposite world, option {'A' if correct_idx == 1 else 'B'} is correct: {wrong_answer}"
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-ChoiceInversion",
            context=truncate_text(f"{goal}", 150),
            conversation=conversation,
            query=query,
            answer=inverted_answer,
            state_info={
                "type": "choice_inversion",
                "normal_correct": correct_answer,
                "inverted_correct": wrong_answer
            },
            ground_truth={
                "normal_correct_idx": correct_idx,
                "inverted_correct_idx": 1 - correct_idx
            },
            difficulty="very_hard",
            source_id=f"piqa_t5_invert_{source_id}"
        )
    
    def _generate_reversal(self, goal: str) -> str:
        """Generate a physical reversal based on the goal."""
        goal_lower = goal.lower()
        
        if "boil" in goal_lower or "heat" in goal_lower:
            return "heat causes things to freeze, while cold makes things boil."
        elif "freeze" in goal_lower or "cool" in goal_lower:
            return "cold causes things to melt, while heat freezes them."
        elif "metal" in goal_lower:
            return "metal is soft and wood is hard."
        elif "attach" in goal_lower or "connect" in goal_lower:
            return "glue separates things and nails connect things."
        elif "pour" in goal_lower or "liquid" in goal_lower:
            return "liquids are solid and solids flow like liquids."
        else:
            return "physical properties work in reverse."

# =====================================================================
# Main Converter
# =====================================================================

class PIQAConversationalConverter:
    """Main converter for PIQA to conversational format."""
    
    def __init__(self, data_dir: str = "data/PIQA"):
        self.data_dir = Path(data_dir)
        self.t2_converter = T2Converter()
        self.t3_converter = T3Converter()
        self.t5_converter = T5Converter()
    
    def load_data(self, split: str = "train") -> List[Dict]:
        """Load PIQA data."""
        if split == "train":
            data_file = self.data_dir / "physicaliqa-train-dev" / "train.jsonl"
            label_file = self.data_dir / "physicaliqa-train-dev" / "train-labels.lst"
        elif split == "dev":
            data_file = self.data_dir / "physicaliqa-train-dev" / "dev.jsonl"
            label_file = self.data_dir / "physicaliqa-train-dev" / "dev-labels.lst"
        else:
            return []
        
        if not data_file.exists():
            print(f"Data file not found: {data_file}")
            return []
        
        # Load data
        samples = []
        with open(data_file, 'r', encoding='utf-8') as f:
            for line in f:
                samples.append(json.loads(line.strip()))
        
        # Load labels
        if label_file.exists():
            with open(label_file, 'r', encoding='utf-8') as f:
                labels = [int(line.strip()) for line in f]
            
            # Attach labels to samples
            for i, sample in enumerate(samples):
                if i < len(labels):
                    sample['label'] = labels[i]
        
        print(f"Loaded {len(samples)} samples from {split}")
        return samples
    
    def convert_sample(self, sample: Dict, sample_id: str) -> List[ConversationalSample]:
        """Convert a single PIQA sample to conversational format."""
        results = []
        
        goal = sample.get("goal", "")
        sol1 = sample.get("sol1", "")
        sol2 = sample.get("sol2", "")
        sample_id_val = sample.get("id", sample_id)
        correct_idx = sample.get("label", 0)
        
        if not goal or not sol1 or not sol2:
            return results
        
        # T2: State timeline
        sample_t2_timeline = self.t2_converter.create_state_timeline_sample(
            goal, sol1, sol2, correct_idx, sample_id
        )
        if sample_t2_timeline:
            results.append(sample_t2_timeline)
        
        # T2: Action sequence (30% chance)
        if random.random() < 0.3:
            sample_t2_seq = self.t2_converter.create_action_sequence_sample(
                goal, sol1, sol2, correct_idx, sample_id
            )
            if sample_t2_seq:
                results.append(sample_t2_seq)
        
        # T3: Resource conflict (30% chance)
        if random.random() < 0.3:
            sample_t3_resource = self.t3_converter.create_resource_conflict_sample(
                goal, sol1, sol2, correct_idx, sample_id
            )
            if sample_t3_resource:
                results.append(sample_t3_resource)
        
        # T5: Counterfactual (always generate)
        sample_t5_cf = self.t5_converter.create_counterfactual_sample(
            goal, sol1, sol2, correct_idx, sample_id
        )
        if sample_t5_cf:
            results.append(sample_t5_cf)
        
        # T5: Rule reverse (30% chance)
        if random.random() < 0.3:
            sample_t5_reverse = self.t5_converter.create_rule_reverse_sample(
                goal, sol1, sol2, correct_idx, sample_id
            )
            if sample_t5_reverse:
                results.append(sample_t5_reverse)
        
        # T5: Choice inversion (30% chance)
        if random.random() < 0.3:
            sample_t5_invert = self.t5_converter.create_choice_inversion_sample(
                goal, sol1, sol2, correct_idx, sample_id
            )
            if sample_t5_invert:
                results.append(sample_t5_invert)
        
        return results
    
    def convert_all(self, output_file: str, max_samples: int = None):
        """Convert all PIQA data to conversational format."""
        all_samples = []
        
        # Load training and dev data
        for split in ["train", "dev"]:
            samples = self.load_data(split)
            
            if max_samples and len(all_samples) >= max_samples:
                break
            
            remaining_quota = max_samples - len(all_samples) if max_samples else None
            if remaining_quota is not None:
                samples = samples[:remaining_quota]
            
            print(f"Converting {split} samples...")
            for i, sample in enumerate(samples):
                sample_id = f"{split}_{sample.get('id', i)}"
                converted = self.convert_sample(sample, sample_id)
                all_samples.extend(converted)
                
                if i % 1000 == 0:
                    print(f"  Processed {i} samples, generated {len(all_samples)} conversational samples")
        
        # Save output
        print(f"\nTotal converted: {len(all_samples)} samples")
        
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
    print("PIQA Conversational Temporal Data Converter")
    print("=" * 60)
    
    converter = PIQAConversationalConverter()
    output_file = "converted_data_v3/piqa_conversational.jsonl"
    
    samples = converter.convert_all(output_file, max_samples=5000)

if __name__ == "__main__":
    main()