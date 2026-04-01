#!/usr/bin/env python3
"""
TRACIE Conversational Temporal DataConverter

Converts TRACIE dataset to conversational temporal reasoning format.

TRACIE tests implicit temporal reasoning (ordering events without timestamps).
Primary tasks: T1 (Ordering), T2 (State Update)

Data source: data/tracie/data/uniform-prior/tracie_test.txt
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import random

# Set seed for reproducibility
random.seed(42)

@dataclass
class ConversationalSample:
    """Conversational sample format matching other converters"""
    task: str  # T1 or T2
    sub_task: str  # T1-Convo-Ordering, T2-Convo-State, etc.
    context: str  # Original story (truncated if needed)
    conversation: List[Dict[str, str]]  # [{"role": "user/assistant", "content": "..."}]
    query: str
    answer: str
    state_info: Optional[Dict[str, Any]] = None
    ground_truth: Optional[Dict[str, Any]] = None
    difficulty: str = "medium"  # easy, medium, hard, very_hard
    source_id: Optional[str] = None


def parse_tracie_line(line: str) -> Dict[str, str]:
    """Parse a single TRACIE line"""
    # Format: event: [query] story: [context]\tanswer: [label]
    line = line.strip()
    if not line:
        return None
    
    # Extract event
    event_match = re.match(r'event:\s*(.+?)\s+story:', line)
    if not event_match:
        return None    
    event = event_match.group(1).strip()
    
    # Extract story and answer
    story_match = re.search(r'story:\s*(.+?)\tanswer:', line)
    if not story_match:
        return None
    story = story_match.group(1).strip()    
    answer_match = re.search(r'answer:\s*(\w+)', line)
    if not answer_match:
        return None
    answer = answer_match.group(1).strip()    
    return {
        'event': event,
        'story': story,
        'answer': answer
    }


def extract_temporal_relation(event: str) -> Tuple[str, str, str]:
    """
    Extract temporal relation from event string.
    Returns (subject, relation_type, reference_event)
    
    Examples:
    - "Chad looked for his baseball cap starts after he got off the ride"-> ("Chad looked for his baseball cap", "starts after", "he got off the ride")
    - "Paul is not friendly. starts after Paul hat his job"-> ("Paul is not friendly.", "starts after", "Paul hat his job")
    """
    # Try to match starts before/after
    patterns = [
        (r'(.+?)\s+starts before\s+(.+)', 'starts before'),
        (r'(.+?)\s+starts after\s+(.+)', 'starts after'),
        (r'(.+?)\s+ends before\s+(.+)', 'ends before'),
        (r'(.+?)\s+ends after\s+(.+)', 'ends after'),
    ]
    
    for pattern, rel_type in patterns:
        match = re.match(pattern, event, re.IGNORECASE)
        if match:
            subject = match.group(1).strip()
            reference = match.group(2).strip()
            return subject, rel_type, reference    
    return None, None, None


def get_opposite_relation(relation: str) -> str:
    """Get the opposite temporal relation"""
    opposites = {
        'starts before': 'starts after','starts after': 'starts before',
        'ends before': 'ends after',
        'ends after': 'ends before'
    }
    return opposites.get(relation, relation)


def get_correct_ordering(relation: str, is_positive: bool) -> str:
    """
    Determine the correct ordering based on relation and label.
    Returns 'before' or 'after'
    """
    if is_positive:
        # If label is positive, the relation as stated is correct
        if 'before' in relation:
            return 'before'
        else:
            return 'after'
    else:
        # If label is negative, the opposite is correct
        if 'before' in relation:
            return 'after'
        else:
            return 'before'


def create_story_key(story: str) -> str:
    """Create a key for grouping stories"""
    # Use first 100 chars as key (stories should be identical for pairs)
    return story[:100].strip().lower()


def load_and_group_tracie_data(filepath: str) -> Dict[str, List[Dict]]:
    """
    Load TRACIE data and group pairs by story.
    Returns dict mapping story_key -> list of samples
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    story_groups = defaultdict(list)
    for line in lines:
        parsed = parse_tracie_line(line)
        if parsed:
            key = create_story_key(parsed['story'])
            story_groups[key].append(parsed)
    
    return story_groups


def find_pairs(story_groups: Dict[str, List[Dict]]) -> List[Tuple[Dict, Dict]]:
    """
    Find matching pairs (positive + negative) for each story.
    Each story should have a before/after pair.
    """
    pairs = []
    
    for story_key, samples in story_groups.items():
        if len(samples) <2:
            continue
        
        # Group by event content (stripping before/after)
        event_groups = defaultdict(list)
        for sample in samples:
            subject, rel, ref = extract_temporal_relation(sample['event'])
            if subject and ref:
                # Create a key that identifies the same subject+reference
                pair_key = f"{subject}|||{ref}"
                event_groups[pair_key].append(sample)
        
        # Find positive/negative pairs
        for pair_key, group in event_groups.items():
            if len(group) >= 2:
                pos_samples = [s for s in group if s['answer'] == 'positive']
                neg_samples = [s for s in group if s['answer'] == 'negative']
                
                if pos_samples and neg_samples:
                    # Take one pair
                    pairs.append((pos_samples[0], neg_samples[0]))
    
    return pairs


def create_t1_ordering_samples(pair: Tuple[Dict, Dict]) -> List[ConversationalSample]:
    """
    Create T1 (Ordering) conversational samples from a pair.
    
    T1-Convo-Ordering: Ask whether event A happens before/after event B
    T1-Convo-MultiChoice: Multiple choice format
    """
    samples = []
    pos_sample, neg_sample = pair
    story = pos_sample['story']
    
    # Extract temporal relations
    subject, rel, ref = extract_temporal_relation(pos_sample['event'])
    if not subject:
        return samples
    
    correct_order = get_correct_ordering(rel, True)
    
    # T1-Convo-Ordering: Direct ordering question
    convo = [
        {"role": "user", "content": f"I'll tell you a story and ask a temporal reasoning question."},
        {"role": "assistant", "content": "Sure, I'm ready. Please share the story."},
        {"role": "user", "content": f"Story: {story}"},
        {"role": "assistant", "content": "I've read the story. What's your question about the events?"},
        {"role": "user", "content": f"Based on the story's timeline, does \"{subject.strip()}\" happen before or after \"{ref.strip()}\"? Think about the causal chain and logical sequence of events."}
    ]
    
    answer = f"{'before' if correct_order == 'before' else 'after'}"
    
    samples.append(ConversationalSample(
        task="T1",
        sub_task="T1-Convo-Ordering",
        context=story[:500],  # Truncate for context
        conversation=convo,
        query=f"Does \"{subject.strip()}\" happen before or after \"{ref.strip()}\"?",
        answer=answer,
        ground_truth={
            "subject": subject.strip(),
            "reference": ref.strip(),
            "correct_ordering": correct_order,
            "story_length": len(story)
        },
        difficulty="medium" if len(story) < 300 else "hard",
        source_id=f"tracie_ordering_{hash(story) % 10000}"
    ))
    
    # T1-Convo-MultiChoice: Multiple choice format with distractors
    options = ["before", "after"]
    correct_idx = 0 if correct_order == "before" else 1
    
    convo_mc = [
        {"role": "user", "content": f"Read this story carefully: {story}"},
        {"role": "assistant", "content": "I've understood the story. What do you want to know?"},
        {"role": "user", "content": f"Question: Does \"{subject.strip()}\" happen before or after \"{ref.strip()}\"?\n\nOptions:\nA. before\nB. after\n\nChoose the correct answer."}
    ]
    
    samples.append(ConversationalSample(
        task="T1",
        sub_task="T1-Convo-MultiChoice",
        context=story[:500],
        conversation=convo_mc,
        query=f"Select: {subject.strip()} relative to {ref.strip()}",answer=options[correct_idx],
        ground_truth={
            "correct_option": options[correct_idx],
            "options": options
        },
        difficulty="medium",
        source_id=f"tracie_multichoice_{hash(story) % 10000}"
    ))
    
    # T1-Convo-Sequence: Ask about event sequence (harder)
    if 'starts' in rel:
        sequence_question = f"In the story's timeline, list these events in chronological order:\n1. {subject.strip()}\n2. {ref.strip()}"
        sequence_answer = f"1. {ref.strip()}\n2. {subject.strip()}" if correct_order == "after" else f"1. {subject.strip()}\n2. {ref.strip()}"
        
        convo_seq = [
            {"role": "user", "content": f"Story: {story}"},
            {"role": "assistant", "content": "I've read it. What's your question?"},
            {"role": "user", "content": sequence_question}
        ]
        
        samples.append(ConversationalSample(
            task="T1",
            sub_task="T1-Convo-Sequence",
            context=story[:500],
            conversation=convo_seq,
            query=f"Order: {subject.strip()} vs {ref.strip()}",
            answer=sequence_answer,
            ground_truth={
                "correct_order": correct_order
            },
            difficulty="hard",
            source_id=f"tracie_sequence_{hash(story) % 10000}"
        ))
    
    return samples


def create_t2_state_samples(pair: Tuple[Dict, Dict]) -> List[ConversationalSample]:
    """
    Create T2 (State Update) conversational samples from a pair.
    
    T2-Convo-State: Ask about entity state at a specific point in timeline
    T2-Convo-Consequence: Ask about consequences of an event
    """
    samples = []
    pos_sample, neg_sample = pair
    story = pos_sample['story']
    
    # Extract temporal relations
    subject, rel, ref = extract_temporal_relation(pos_sample['event'])
    if not subject:
        return samples
    
    correct_order = get_correct_ordering(rel, True)
    
    # T2-Convo-State: Infer state at a point in time
    # Ask what state the subject is in before/after the reference event
    if 'starts' in rel:
        state_question = f"At the moment when \"{ref.strip()}\" occurs, has \"{subject.strip()}\" already happened?"
        state_answer = "yes" if correct_order == "after" else "no"
    else:  # ends
        state_question = f"When \"{ref.strip()}\" happens, has \"{subject.strip()}\" already finished?"
        state_answer = "yes" if correct_order == "after" else "no"
    
    convo_state = [
        {"role": "user", "content": f"I'll share a story and ask about the state of events at specific moments."},
        {"role": "assistant", "content": "Ready. Please share the story."},
        {"role": "user", "content": f"Story: {story}"},
        {"role": "assistant", "content": "I've understood the narrative. What's your question?"},
        {"role": "user", "content": state_question + " Answer yes or no, then explain briefly."}
    ]
    
    samples.append(ConversationalSample(
        task="T2",
        sub_task="T2-Convo-State",
        context=story[:500],
        conversation=convo_state,
        query=state_question,
        answer=state_answer,
        ground_truth={
            "subject": subject.strip(),
            "reference": ref.strip(),
            "relation": rel,
            "correct_order": correct_order
        },
        difficulty="hard",
        source_id=f"tracie_state_{hash(story) % 10000}"    ))
    
    # T2-Convo-Consequence: What happens after/before
    if correct_order == "after":
        consequence_q = f"What must happen before \"{subject.strip()}\" can occur?"
        consequence_a = f"\"{ref.strip()}\" must happen first."
    else:
        consequence_q = f"What happens after \"{subject.strip()}\"?"
        consequence_a = f"\"{ref.strip()}\" happens afterward."
    
    convo_conseq = [
        {"role": "user", "content": f"Story: {story}"},
        {"role": "assistant", "content": "I've read it. What's your question?"},
        {"role": "user", "content": consequence_q}
    ]
    
    samples.append(ConversationalSample(
        task="T2",
        sub_task="T2-Convo-Consequence",
        context=story[:500],
        conversation=convo_conseq,
        query=consequence_q,
        answer=consequence_a,
        ground_truth={
            "temporal_order": correct_order
        },
        difficulty="medium",
        source_id=f"tracie_consequence_{hash(story) % 10000}"
    ))
    
    return samples


def create_t1_implicit_causal_samples(story_groups: Dict[str, List[Dict]]) -> List[ConversationalSample]:
    """
    Create additional T1 samples focused on implicit causal reasoning.
    These require understanding the causal chain to determine temporal order.
    """
    samples = []
    
    for story_key, story_samples in story_groups.items():
        if len(story_samples) < 2:
            continue
        
        # Take first story sample
        story = story_samples[0]['story']
        
        # Find samples with different event types
        for sample in story_samples[:2]:  # Limit to avoid duplicates
            subject, rel, ref = extract_temporal_relation(sample['event'])
            if not subject:
                continue
            
            correct_order = get_correct_ordering(rel, sample['answer'] == 'positive')
            
            # T1-Convo-Causal: Ask to explain WHY the temporal order is correct
            causal_question = f"In the story, explain the causal chain that determines whether \"{subject.strip()}\" happens before or after \"{ref.strip()}\"."
            
            if correct_order == "after":
                causal_answer = f"\"{ref.strip()}\" happens first, which causes or enables \"{subject.strip()}\" to occur afterward."
            else:
                causal_answer = f"\"{subject.strip()}\" happens first, before \"{ref.strip()}\" occurs."
            
            convo = [
                {"role": "user", "content": f"Story: {story}"},
                {"role": "assistant", "content": "I've read the story. What's your question?"},
                {"role": "user", "content": causal_question}
            ]
            
            samples.append(ConversationalSample(
                task="T1",
                sub_task="T1-Convo-Causal",
                context=story[:500],
                conversation=convo,
                query=causal_question,
                answer=causal_answer,
                ground_truth={
                    "correct_order": correct_order,
                    "reasoning_type": "causal"
                },
                difficulty="very_hard",
                source_id=f"tracie_causal_{hash(story) % 10000}"
            ))
            
            break  # One per story
    
    return samples


def process_tracie_file(input_path: str, output_path: str):
    """Process TRACIE file and create conversational samples"""
    print("=" * 60)
    print("TRACIE Conversational Temporal Data Converter")
    print("=" * 60)
    
    # Load and group data
    print(f"\nLoading data from {input_path}...")
    story_groups = load_and_group_tracie_data(input_path)
    print(f"Loaded {sum(len(v) for v in story_groups.values())} samples from {len(story_groups)} unique stories")
    
    # Find pairs
    print("\nFinding positive/negative pairs...")
    pairs = find_pairs(story_groups)
    print(f"Found {len(pairs)} valid pairs")
    
    # Generate samples
    print("\nGenerating conversational samples...")
    all_samples = []
    
    # T1 samples from pairs
    for pair in pairs:
        t1_samples = create_t1_ordering_samples(pair)
        all_samples.extend(t1_samples)
        
        t2_samples = create_t2_state_samples(pair)
        all_samples.extend(t2_samples)
    
    # Additional T1 causal samples
    t1_causal = create_t1_implicit_causal_samples(story_groups)
    all_samples.extend(t1_causal)
    
    print(f"Generated {len(all_samples)} conversational samples")
    
    # Statistics
    task_counts = defaultdict(int)
    subtask_counts = defaultdict(int)
    difficulty_counts = defaultdict(int)
    
    for sample in all_samples:
        task_counts[sample.task] += 1
        subtask_counts[sample.sub_task] += 1
        difficulty_counts[sample.difficulty] += 1
    
    print("\n" + "=" * 60)
    print("Conversion Summary")
    print("=" * 60)
    print(f"\nTotal samples: {len(all_samples)}")
    print(f"\nTask distribution:")
    for task, count in sorted(task_counts.items()):
        print(f"  {task}: {count}")
    
    print(f"\nSubtask distribution:")
    for subtask, count in sorted(subtask_counts.items()):
        print(f"  {subtask}: {count}")
    
    print(f"\nDifficulty distribution:")
    for diff, count in sorted(difficulty_counts.items()):
        print(f"  {diff}: {count}")
    
    # Save to JSONL
    print(f"\nSaving to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in all_samples:
            f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
    
    print(f"Saved {len(all_samples)} samples to {output_path}")
    
    # Save statistics
    stats = {
        "total_samples": len(all_samples),
        "task_distribution": dict(task_counts),
        "subtask_distribution": dict(subtask_counts),
        "difficulty_distribution": dict(difficulty_counts),
        "unique_stories": len(story_groups),
        "valid_pairs": len(pairs)
    }
    
    stats_path = output_path.replace('.jsonl', '_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"Saved statistics to {stats_path}")
    print("\n" + "=" * 60)


def main():
    # Use uniform-prior split as recommended by the interpretation doc
    input_path = "data/tracie/data/uniform-prior/tracie_test.txt"
    output_path = "converted_data_v3/tracie_conversational.jsonl"
    
    # Ensure output directory exists
    Path("converted_data_v3").mkdir(exist_ok=True)
    
    process_tracie_file(input_path, output_path)


if __name__ == "__main__":
    main()