#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASTA Conversational Temporal Data Converter

Converts PASTA (Participant State Tracking in Narratives) to conversational format.
Primary focus: T2 (State Update), T5 (Counterfactual)

Key features:
- Story-state inference (participant mental/identity states)
- Counterfactual story modification for anti-data-pollution testing
- Minimal supporting set analysis

Output: converted_data_v3/pasta_conversational.jsonl
"""

import json
import random
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

# =====================================================================
# Data Structures
# =====================================================================

@dataclass
class ConversationalSample:
    task: str  # T2, T5
    sub_task: str  # e.g., "T2-Convo-State", "T5-Convo-Counterfactual"
    context: str  # Story context
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

# State categories for classification
STATE_CATEGORIES = {
    "personality": ["smart", "dumb", "lazy", "hardworking", "curious", "patient", "careful", "clumsy"],
    "emotion": ["happy", "sad", "angry", "fearful", "surprised", "disgusted", "squeamish"],
    "social": ["friendly", "selfish", "generous", "rude", "polite", "helpful", "mean"],
    "physical": ["tired", "healthy", "sick", "hungry", "thirsty", "strong", "weak"],
    "identity": ["teenager", "adult", "child", "student", "teacher", "professional"],
    "ability": ["talented", "skilled", "inexperienced", "capable", "unable"]
}

# Noise questions for distraction
NOISE_QUESTIONS = [
    "By the way, what's the weather like?",
    "I heard about a new movie coming out.",
    "The traffic was terrible this morning.",
    "My neighbor got a new car.",
    "I need to finish my homework later.",
    "Did you see the news yesterday?",
    "What's for dinner tonight?",
    "Have you tried that new coffee place?",
    "Iforgot to call my friend.",
    "What time is it?"
]

def categorize_state(assertion: str) -> str:
    """Categorize the state type based on assertion."""
    assertion_lower = assertion.lower()
    
    for category, keywords in STATE_CATEGORIES.items():
        for keyword in keywords:
            if keyword in assertion_lower:
                return category
    
    return "general"

def extract_key_lines(line_on_dict: Dict[str, bool]) -> List[int]:
    """Extract key line numbers from line.on flags."""
    key_lines = []
    for key, value in line_on_dict.items():
        if value:
            # Extract line number from key like "line1.on"
            line_num = int(key.replace("line", "").replace(".on", ""))
            key_lines.append(line_num)
    return sorted(key_lines)

def truncate_text(text: str, max_len: int = 300) -> str:
    """Truncate text to max length."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(' ', 1)[0] + '...'

# =====================================================================
# T2: State Update Converter
# =====================================================================

class T2Converter:
    """Convert PASTA data to T2 state tracking format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_state_inference_sample(self, title: str, lines: List[str], 
                                       assertion: str, key_lines: List[int],
                                       source_id: str) -> Optional[ConversationalSample]:
        """T2-Convo-State: Infer participant state from story."""
        conversation = []
        
        # Round 1: Story context
        story_text = " ".join(lines)
        conversation.append({
            "role": "user",
            "content": f"Here's a short story: {story_text}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I've read the story. What would you like to know about it?"
        })
        
        # Round 2: Distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I don't have information about that. Let's focus on the story."
        })
        
        # Round 3: Query about state
        # Extract participant name from assertion (usually at the beginning)
        participant = assertion.split()[0] if assertion else "the participant"
        
        category = categorize_state(assertion)
        if category == "emotion":
            query = f"What can you infer about {participant}'s emotional state?"
        elif category == "personality":
            query = f"What does this story tell us about {participant}'s personality?"
        elif category == "identity":
            query = f"What can you infer about {participant}'s identity or role?"
        elif category == "physical":
            query = f"What is {participant}'s physical state based on this story?"
        else:
            query = f"What can you infer about {participant} from this story?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-State",
            context=truncate_text(story_text, 250),
            conversation=conversation,
            query=query,
            answer=assertion,
            state_info={
                "type": "state_inference",
                "participant": participant,
                "category": category,
                "key_lines": key_lines
            },
            ground_truth={
                "assertion": assertion,
                "supporting_lines": key_lines,
                "category": category
            },
            difficulty="medium" if len(key_lines) <= 2 else "hard",
            source_id=f"pasta_t2_state_{source_id}"
        )
    
    def create_progressive_state_sample(self, title: str, lines: List[str],
                                         assertion: str, key_lines: List[int],
                                         source_id: str) -> Optional[ConversationalSample]:
        """T2-Convo-Progressive: Track state through story progression."""
        conversation = []
        
        # Present story line by line
        conversation.append({
            "role": "user",
            "content": f"I'll tell you a story line by line. Listen carefully."
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Okay, I'm ready to hear the story."
        })
        
        # Present each line
        for i, line in enumerate(lines, 1):
            conversation.append({
                "role": "user",
                "content": f"Line {i}: {line}"
            })
            
            # If this is a key line, acknowledge it differently
            if i in key_lines:
                conversation.append({
                    "role": "assistant",
                    "content": f"Noted - this seems like an important detail."
                })
            else:
                conversation.append({
                    "role": "assistant",
                    "content": f"Got it, line {i}."
                })
        
        # Add distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let me recall the story to answer your question."
        })
        
        # Query
        participant = assertion.split()[0] if assertion else "the participant"
        query = f"Based on all the lines, what is {participant}'s state?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Progressive",
            context=truncate_text(" ".join(lines), 200),
            conversation=conversation,
            query=query,
            answer=assertion,
            state_info={
                "type": "progressive_state",
                "key_lines": key_lines,
                "total_lines": len(lines)
            },
            ground_truth={
                "assertion": assertion,
                "key_lines": key_lines
            },
            difficulty="hard",
            source_id=f"pasta_t2_prog_{source_id}"
        )
    
    def create_key_evidence_sample(self, title: str, lines: List[str],
                                     assertion: str, key_lines: List[int],
                                     source_id: str) -> Optional[ConversationalSample]:
        """T2-Convo-Evidence: Identify key evidence for state inference."""
        if not key_lines:
            return None
        
        conversation = []
        
        # Present story
        story_text = " ".join(lines)
        conversation.append({
            "role": "user",
            "content": f"Story: {story_text}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I've read the story."
        })
        
        # State the conclusion
        conversation.append({
            "role": "user",
            "content": f"The story suggests that {assertion}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"I understand, you're saying {assertion}."
        })
        
        # Distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let's focus on the story analysis."
        })
        
        # Query about evidence
        query = f"Which line(s) in the story are most crucial for inferring that {assertion}?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        # Format answer with line numbers
        key_line_texts = [f"Line {i}: {lines[i-1]}" for i in key_lines]
        answer_text = "The key evidence is: " + "; ".join(key_line_texts)
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Evidence",
            context=truncate_text(story_text, 200),
            conversation=conversation,
            query=query,
            answer=answer_text,
            state_info={
                "type": "evidence_identification",
                "key_lines": key_lines,
                "category": categorize_state(assertion)
            },
            ground_truth={
                "key_lines": key_lines,
                "key_line_texts": [lines[i-1] for i in key_lines]
            },
            difficulty="hard",
            source_id=f"pasta_t2_evid_{source_id}"
        )

# =====================================================================
# T5: Counterfactual Converter
# =====================================================================

class T5Converter:
    """Convert PASTA data to T5 counterfactual format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_counterfactual_sample(self, title: str, orig_lines: List[str],
                                       orig_assertion: str, mod_lines: List[str],
                                       mod_assertion: str, key_lines: List[int],
                                       source_id: str) -> Optional[ConversationalSample]:
        """T5-Convo-Counterfactual: Test anti-data-pollution with modified story."""
        conversation = []
        
        # Round 1: Present MODIFIED story (counterfactual)
        mod_story = " ".join(mod_lines)
        conversation.append({
            "role": "user",
            "content": f"Read this story carefully: {mod_story}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I've read the story. What would you like to know?"
        })
        
        # Round 2: Distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I'm focusing on the story you told me."
        })
        
        # Round 3: Query
        participant = mod_assertion.split()[0] if mod_assertion else "the participant"
        query = f"Based on this story, what is true about {participant}?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        # The answer should be the MODIFIED assertion
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-Counterfactual",
            context=truncate_text(mod_story, 250),
            conversation=conversation,
            query=query,
            answer=mod_assertion,
            state_info={
                "type": "counterfactual_test",
                "original_assertion": orig_assertion,
                "modified_assertion": mod_assertion,
                "key_lines_changed": key_lines
            },
            ground_truth={
                "story_type": "modified",
                "correct_answer": mod_assertion,
                "original_answer": orig_assertion,
                "anti_pollution_test": True
            },
            difficulty="very_hard",
            source_id=f"pasta_t5_cf_{source_id}"
        )
    
    def create_contrastive_pair_sample(self, title: str, orig_lines: List[str],
                                         orig_assertion: str, mod_lines: List[str],
                                         mod_assertion: str, key_lines: List[int],
                                         source_id: str) -> Optional[ConversationalSample]:
        """T5-Convo-Contrastive: Show contrastive pair and test understanding."""
        conversation = []
        
        # Round 1: Present original story
        orig_story = " ".join(orig_lines)
        conversation.append({
            "role": "user",
            "content": f"Original story: {orig_story}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Based on this, {orig_assertion}"
        })
        
        # Round 2: Present modified story
        mod_story = " ".join(mod_lines)
        
        # Highlight the changed line
        changed_line_idx = key_lines[0] - 1 if key_lines else 0
        original_line = orig_lines[changed_line_idx] if changed_line_idx < len(orig_lines) else ""
        modified_line = mod_lines[changed_line_idx] if changed_line_idx < len(mod_lines) else ""
        
        conversation.append({
            "role": "user",
            "content": f"Now, in a DIFFERENT version: {mod_story}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I see, this is a different version of the story."
        })
        
        # Round 3: Distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let me remember both versions of the story."
        })
        
        # Round 4: Query about contrast
        query = f"In the DIFFERENT version, what is true about the participant?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-Contrastive",
            context=f"Original: {truncate_text(orig_story, 100)} Modified: {truncate_text(mod_story, 100)}",
            conversation=conversation,
            query=query,
            answer=mod_assertion,
            state_info={
                "type": "contrastive_pair",
                "original_assertion": orig_assertion,
                "modified_assertion": mod_assertion,
                "changed_line": modified_line
            },
            ground_truth={
                "original_assertion": orig_assertion,
                "modified_assertion": mod_assertion,
                "original_line": original_line,
                "modified_line": modified_line
            },
            difficulty="very_hard",
            source_id=f"pasta_t5_contrast_{source_id}"
        )
    
    def create_rule_change_sample(self, title: str, orig_lines: List[str],
                                   orig_assertion: str, mod_lines: List[str],
                                   mod_assertion: str, key_lines: List[int],
                                   source_id: str) -> Optional[ConversationalSample]:
        """T5-Convo-RuleChange: Test rule following vs pre-training memory."""
        conversation = []
        
        # Round 1: Introduce rule change
        conversation.append({
            "role": "user",
            "content": f"In this story, some facts are DIFFERENT from what you might expect. Pay attention to the details."
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I'll pay close attention to the specific details in this story."
        })
        
        # Round 2: Modified story
        mod_story = " ".join(mod_lines)
        conversation.append({
            "role": "user",
            "content": f"{mod_story}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I've noted the story details carefully."
        })
        
        # Round 3: Present "trap" - mention original
        conversation.append({
            "role": "user",
            "content": f"You might have heard similar stories where {orig_assertion} Is that true here?"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "No, I should only use the facts from THIS story, not similar stories I've heard before."
        })
        
        # Round 4: Query
        participant = mod_assertion.split()[0] if mod_assertion else "the participant"
        query = f"So in THIS specific story, what is true about {participant}?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-RuleChange",
            context=truncate_text(mod_story, 200),
            conversation=conversation,
            query=query,
            answer=mod_assertion,
            state_info={
                "type": "rule_following",
                "original_assertion": orig_assertion,
                "modified_assertion": mod_assertion,
                "anti_bias": True
            },
            ground_truth={
                "pre_training_knowledge": orig_assertion,
                "correct_context_answer": mod_assertion,
                "test_type": "anti_pollution"
            },
            difficulty="very_hard",
            source_id=f"pasta_t5_rule_{source_id}"
        )
    
    def create_state_reversal_sample(self, title: str, orig_lines: List[str],
                                      orig_assertion: str, mod_lines: List[str],
                                      mod_assertion: str, key_lines: List[int],
                                      source_id: str) -> Optional[ConversationalSample]:
        """T5-Convo-Reversal: Test state reversal understanding."""
        conversation = []
        
        # Round 1: Present NEW context
        conversation.append({
            "role": "user",
            "content": "Consider this scenario:"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I'm listening."
        })
        
        # Round 2: Modified story
        mod_story = " ".join(mod_lines)
        conversation.append({
            "role": "user",
            "content": f"{mod_story}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I understand the scenario."
        })
        
        # Round 3: Distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let me focus on the scenario details."
        })
        
        # Determine state reversal type
        orig_category = categorize_state(orig_assertion)
        mod_category = categorize_state(mod_assertion)
        
        query = f"Based on this scenario, describe the participant's state."
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-Reversal",
            context=truncate_text(mod_story, 250),
            conversation=conversation,
            query=query,
            answer=mod_assertion,
            state_info={
                "type": "state_reversal",
                "original_state": orig_assertion,
                "reversed_state": mod_assertion,
                "state_category": mod_category
            },
            ground_truth={
                "original_assertion": orig_assertion,
                "modified_assertion": mod_assertion,
                "category_shift": f"{orig_category} -> {mod_category}"
            },
            difficulty="hard",
            source_id=f"pasta_t5_rev_{source_id}"
        )

# =====================================================================
# Main Converter
# =====================================================================

class PASTAConversationalConverter:
    """Main converter for PASTA to conversational format."""
    
    def __init__(self, data_dir: str = "data/PASTA/data"):
        self.data_dir = Path(data_dir)
        self.t2_converter = T2Converter()
        self.t5_converter = T5Converter()
    
    def load_data(self, split: str = "train") -> List[Dict]:
        """Load PASTA data from JSONL file."""
        if split == "train":
            filename = "tr_data.jsonl"
        elif split == "val":
            filename = "val_data.jsonl"
        elif split == "test":
            filename = "te_data.jsonl"
        else:
            filename = "tr_data.jsonl"
        
        filepath = self.data_dir / filename
        samples = []
        
        if not filepath.exists():
            print(f"Data file not found: {filepath}")
            return samples
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                samples.append(json.loads(line.strip()))
        
        print(f"Loaded {len(samples)} samples from {filename}")
        return samples
    
    def convert_sample(self, sample: Dict, sample_id: str) -> List[ConversationalSample]:
        """Convert a single PASTA sample to conversational format."""
        results = []
        
        # Extract fields
        title = sample.get("Input.Title", "")
        
        # Original story
        orig_lines = [
            sample.get("Input.line1", ""),
            sample.get("Input.line2", ""),
            sample.get("Input.line3", ""),
            sample.get("Input.line4", ""),
            sample.get("Input.line5", "")
        ]
        orig_lines = [l for l in orig_lines if l]  # Remove empty lines
        
        # Original assertion
        orig_assertion = sample.get("Answer.assertion", "")
        
        # Modified story
        mod_lines = [
            sample.get("Answer.mod_line1", ""),
            sample.get("Answer.mod_line2", ""),
            sample.get("Answer.mod_line3", ""),
            sample.get("Answer.mod_line4", ""),
            sample.get("Answer.mod_line5", "")
        ]
        mod_lines = [l for l in mod_lines if l]
        
        # Modified assertion
        mod_assertion = sample.get("Answer.mod_assertion", "")
        
        # Key lines (minimal supporting set)
        key_lines = []
        for i in range(1, 6):
            if sample.get(f"Answer.line{i}.on", False):
                key_lines.append(i)
        
        if not orig_lines or not orig_assertion:
            return results
        
        # T2: State inference samples
        sample_t2_state = self.t2_converter.create_state_inference_sample(
            title, orig_lines, orig_assertion, key_lines, sample_id
        )
        if sample_t2_state:
            results.append(sample_t2_state)
        
        # T2: Progressive state tracking
        if random.random() < 0.3:  # 30% chance
            sample_t2_prog = self.t2_converter.create_progressive_state_sample(
                title, orig_lines, orig_assertion, key_lines, sample_id
            )
            if sample_t2_prog:
                results.append(sample_t2_prog)
        
        # T2: Evidence identification
        if key_lines:
            sample_t2_evid = self.t2_converter.create_key_evidence_sample(
                title, orig_lines, orig_assertion, key_lines, sample_id
            )
            if sample_t2_evid:
                results.append(sample_t2_evid)
        
        # T5: Counterfactual samples (if modified story exists)
        if mod_lines and mod_assertion:
            # T5: Counterfactual test
            sample_t5_cf = self.t5_converter.create_counterfactual_sample(
                title, orig_lines, orig_assertion, mod_lines, mod_assertion, key_lines, sample_id
            )
            if sample_t5_cf:
                results.append(sample_t5_cf)
            
            # T5: Contrastive pair
            if random.random() < 0.3:  # 30% chance
                sample_t5_contrast = self.t5_converter.create_contrastive_pair_sample(
                    title, orig_lines, orig_assertion, mod_lines, mod_assertion, key_lines, sample_id
                )
                if sample_t5_contrast:
                    results.append(sample_t5_contrast)
            
            # T5: Rule change
            if random.random() < 0.3:  # 30% chance
                sample_t5_rule = self.t5_converter.create_rule_change_sample(
                    title, orig_lines, orig_assertion, mod_lines, mod_assertion, key_lines, sample_id
                )
                if sample_t5_rule:
                    results.append(sample_t5_rule)
            
            # T5: State reversal
            if random.random() < 0.3:  # 30% chance
                sample_t5_rev = self.t5_converter.create_state_reversal_sample(
                    title, orig_lines, orig_assertion, mod_lines, mod_assertion, key_lines, sample_id
                )
                if sample_t5_rev:
                    results.append(sample_t5_rev)
        
        return results
    
    def convert_all(self, output_file: str, max_samples: int = None):
        """Convert all data to conversational format."""
        all_samples = []
        
        # Load data from all splits
        for split in ["train", "val", "test"]:
            samples = self.load_data(split)
            
            if max_samples and len(all_samples) >= max_samples:
                break
            
            remaining_quota = max_samples - len(all_samples) if max_samples else None
            if remaining_quota is not None:
                samples = samples[:remaining_quota]
            
            print(f"Converting {split} samples...")
            for i, sample in enumerate(samples):
                sample_id = f"{split}_{sample.get('AssignmentId', i)}"
                converted = self.convert_sample(sample, sample_id)
                all_samples.extend(converted)
            
            print(f"  Total samples so far: {len(all_samples)}")
        
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
    print("PASTA Conversational Temporal Data Converter")
    print("=" * 60)
    
    converter = PASTAConversationalConverter()
    output_file = "converted_data_v3/pasta_conversational.jsonl"
    
    samples = converter.convert_all(output_file, max_samples=5000)

if __name__ == "__main__":
    main()