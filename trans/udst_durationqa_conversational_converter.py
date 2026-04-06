#!/usr/bin/env python3
"""
UDST-DurationQA Conversational Temporal Data Converter

Converts UDST-DurationQA dataset to conversational format for temporal reasoning benchmark.

Dataset: UDST-DurationQA (derived from UDS-T)
Task Focus: T1 (Time Calculation - Duration Estimation)

Original format: sentence \t question \t answer \t label (yes/no)
Conversion: Group by sentence+question, create multiple choice with distractors

Task Mapping:
- T1 (Time Calculation): Duration estimation with distractors
"""

import json
import random
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple

# Set random seed for reproducibility
random.seed(42)

@dataclass
class ConversationalSample:
    """Conversational sample structure for temporal reasoning."""
    task: str
    sub_task: str
    context: str
    conversation: List[Dict[str, str]]
    query: str
    answer: str
    state_info: Optional[Dict[str, Any]] = None
    ground_truth: Optional[Dict[str, Any]] = None
    difficulty: str = "medium"
    source_id: Optional[str] = None


def load_udst_data(filepath: str) -> List[Dict[str, str]]:
    """Load UDST-DurationQA TSV file."""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 4:
                data.append({
                    'sentence': parts[0],
                    'question': parts[1],
                    'answer': parts[2],
                    'label': parts[3].lower()
                })
    return data


def group_by_sentence_question(data: List[Dict[str, str]]) -> Dict[Tuple[str, str], Dict[str, List[str]]]:
    """
    Group data by (sentence, question) pairs.
    Returns dict with 'correct' and 'incorrect' answer lists.
    """
    grouped = defaultdict(lambda: {'correct': [], 'incorrect': []})
    
    for item in data:
        key = (item['sentence'], item['question'])
        if item['label'] == 'yes':
            grouped[key]['correct'].append(item['answer'])
        else:
            grouped[key]['incorrect'].append(item['answer'])
    return grouped


def generate_distractor_text(context: str) -> str:
    """Generate distractor dialogue insertions."""
    distractors = [
        "By the way, I was reading about a documentary earlier.",
        "Speaking of which, I had an interesting conversation yesterday.",
        "Oh, and I remembered something else too.",
        "That reminds me of something completely different.",
        "I was also thinking about my weekend plans.",
        "Before I forget, let me mention something else.",
        "On a different note, I saw something interesting online.",
        "By the way, the weather has been quite unusual lately.",
        "I should also mention that I've been quite busy this week.",
        "Speaking of time, I've been working on several projects.",
    ]
    return random.choice(distractors)


def create_conversation_context(sentence: str, distractors: List[str]) -> Tuple[List[Dict[str, str]], str]:
    """
    Create conversational context with distractors.
    Returns conversation list and truncated context.
    """
    conversation = []
    
    # Opening exchange
    conversation.append({
        "role": "user",
        "content": f"Let me tell you about something: {sentence}"
    })
    conversation.append({
        "role": "assistant",
        "content": "I see. Please go on."
    })
    
    # Add distractor exchanges
    if distractors:
        for d in distractors[:2]:  # Limit to 2 distractors
            conversation.append({
                "role": "user",
                "content": d
            })
            conversation.append({
                "role": "assistant",
                "content": random.choice([
                    "Interesting, thanks for sharing.",
                    "I understand.",
                    "Noted.",
                    "That's good to know.",
                    "I see what you mean."
                ])
            })
    
    return conversation, sentence


def create_t1_duration_samples(grouped_data: Dict[Tuple[str, str], Dict[str, List[str]]]) -> List[ConversationalSample]:
    """
    Create T1 (Time Calculation) samples for duration estimation.
    
    Subtasks:
    - T1-Convo-MultiChoice: Multiple choice duration question with distractors
    - T1-Convo-CommonSense: Common sense duration estimation
    - T1-Convo-Distractor: Duration with numerical/phrase distractors from context
    """
    samples = []
    sample_id = 0
    
    for (sentence, question), answers in grouped_data.items():
        correct_answers = answers['correct']
        incorrect_answers = answers['incorrect']
        
        # Skip if no correct answer
        if not correct_answers:
            continue
        
        sample_id += 1
        
        # T1-Convo-MultiChoice: Multiple choice format
        if len(correct_answers) >= 1 and len(incorrect_answers) >= 2:
            # Select one correct answer and up to 3 incorrect answers
            correct = random.choice(correct_answers)
            num_options = min(4, len(incorrect_answers) + 1)
            selected_incorrect = random.sample(incorrect_answers, min(3, len(incorrect_answers)))
            
            # Create options
            all_options = [correct] + selected_incorrect
            random.shuffle(all_options)
            correct_idx = all_options.index(correct)
            option_labels = ['A', 'B', 'C', 'D'][:len(all_options)]
            
            # Generate distractors
            distractors = [generate_distractor_text(sentence) for _ in range(2)]
            
            # Create conversation
            conversation, context = create_conversation_context(sentence, distractors)
            
            # Add question to conversation
            options_text = '\n'.join([f"{option_labels[i]}. {all_options[i]}" for i in range(len(all_options))])
            
            conversation.append({
                "role": "user",
                "content": f"{question}\n\nOptions:\n{options_text}"
            })
            
            sample = ConversationalSample(
                task="T1",
                sub_task="T1-Convo-MultiChoice",
                context=sentence,
                conversation=conversation,
                query=question,
                answer=option_labels[correct_idx],
                state_info={
                    "correct_answer": correct,
                    "distractor_answers": selected_incorrect,
                    "num_options": len(all_options)
                },
                ground_truth={
                    "duration": correct,
                    "sentence": sentence
                },
                difficulty="medium" if len(all_options) <= 3 else "hard",
                source_id=f"udst_t1_mc_{sample_id}"
            )
            samples.append(sample)
        
        # T1-Convo-CommonSense: Open-ended duration estimation
        if len(correct_answers) >= 2:
            # Create sample requiring common sense reasoning
            distractors = [generate_distractor_text(sentence)]
            
            conversation, context = create_conversation_context(sentence, distractors)
            
            conversation.append({
                "role": "user",
                "content": f"{question} (Please provide a reasonable duration estimate based on common sense)"
            })
            
            # Randomly select one correct answer as target
            target_answer = random.choice(correct_answers)
            
            sample = ConversationalSample(
                task="T1",
                sub_task="T1-Convo-CommonSense",
                context=sentence,
                conversation=conversation,
                query=question,
                answer=target_answer,
                state_info={
                    "plausible_answers": correct_answers[:5],  # Up to 5 acceptable answers
                    "implausible_answers": incorrect_answers[:3]
                },
                ground_truth={
                    "duration": target_answer,
                    "sentence": sentence
                },
                difficulty="medium",
                source_id=f"udst_t1_cs_{sample_id}"
            )
            samples.append(sample)
        
        # T1-Convo-Distractor: Duration with explicit distractors in context
        if len(incorrect_answers) >= 1:
            # Create sample where one incorrect answer is mentioned in distractor
            distractor_answer = random.choice(incorrect_answers)
            distractor_text = f"By the way, I read about something that took {distractor_answer} once."
            
            conversation = []
            conversation.append({
                "role": "user",
                "content": f"{sentence}"
            })
            conversation.append({
                "role": "assistant",
                "content": "I see. Go on."
            })
            conversation.append({
                "role": "user",
                "content": distractor_text
            })
            conversation.append({
                "role": "assistant",
                "content": "Interesting, but that's a different context."
            })
            conversation.append({
                "role": "user",
                "content": f"{question}"
            })
            
            correct = random.choice(correct_answers) if correct_answers else "unknown"
            
            sample = ConversationalSample(
                task="T1",
                sub_task="T1-Convo-Distractor",
                context=sentence,
                conversation=conversation,
                query=question,
                answer=correct,
                state_info={
                    "distractor_in_context": distractor_answer,
                    "correct_answer": correct,
                    "should_ignore": distractor_answer
                },
                ground_truth={
                    "duration": correct,
                    "sentence": sentence,
                    "distractor": distractor_answer
                },
                difficulty="hard",
                source_id=f"udst_t1_dist_{sample_id}"
            )
            samples.append(sample)
    
    return samples


def process_split(split_name: str) -> List[ConversationalSample]:
    """Process a single data split."""
    filepath = f"data/UDST-DurationQA/data/{split_name}.tsv"
    print(f"Processing {split_name} split...")
    
    # Load data
    data = load_udst_data(filepath)
    print(f"  Loaded {len(data)} raw entries")
    
    # Group by sentence+question
    grouped = group_by_sentence_question(data)
    print(f"  Grouped into {len(grouped)} unique question contexts")
    
    # Create samples
    samples = create_t1_duration_samples(grouped)
    print(f"  Generated {len(samples)} conversational samples")
    
    return samples


def get_difficulty_distribution(samples: List[ConversationalSample]) -> Dict[str, int]:
    """Get difficulty distribution."""
    dist = defaultdict(int)
    for s in samples:
        dist[s.difficulty] += 1
    return dict(dist)


def get_subtask_distribution(samples: List[ConversationalSample]) -> Dict[str, int]:
    """Get subtask distribution."""
    dist = defaultdict(int)
    for s in samples:
        dist[s.sub_task] += 1
    return dict(dist)


def main():
    print("=" * 60)
    print("UDST-DurationQA Conversational Temporal Data Converter")
    print("=" * 60)
    
    all_samples = []
    
    # Process each split
    for split in ['train', 'dev', 'test']:
        samples = process_split(split)
        all_samples.extend(samples)
    
    print(f"\nTotal samples: {len(all_samples)}")
    
    # Statistics
    print("\nTask distribution:")
    task_dist = defaultdict(int)
    for s in all_samples:
        task_dist[s.task] += 1
    for task, count in sorted(task_dist.items()):
        print(f"  {task}: {count}")
    
    print("\nSubtask distribution:")
    subtask_dist = get_subtask_distribution(all_samples)
    for subtask, count in sorted(subtask_dist.items()):
        print(f"  {subtask}: {count}")
    
    print("\nDifficulty distribution:")
    diff_dist = get_difficulty_distribution(all_samples)
    for diff, count in sorted(diff_dist.items()):
        print(f"  {diff}: {count}")
    
    # Save to file
    output_path = Path("converted_data_v3/udst_durationqa_conversational.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in all_samples:
            f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
    
    print(f"\nSaved to: {output_path}")
    
    # Save report
    report = {
        "total_samples": len(all_samples),
        "task_distribution": dict(task_dist),
        "subtask_distribution": dict(subtask_dist),
        "difficulty_distribution": dict(diff_dist),
        "source": "UDST-DurationQA",
        "tasks_covered": ["T1"],
        "subtask_details": {
            "T1-Convo-MultiChoice": "Multiple choice duration with distractors",
            "T1-Convo-CommonSense": "Open-ended common sense duration estimation",
            "T1-Convo-Distractor": "Duration with explicit distractor in context"
        }
    }
    
    report_path = Path("converted_data_v3/udst_durationqa_conversational_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Report saved to: {report_path}")
    
    print("\n" + "=" * 60)
    print("Conversion Summary")
    print("=" * 60)
    print(f"Total converted: {len(all_samples)} samples")
    print(f"Task: T1 (Time Calculation - Duration Estimation)")
    print(f"Output: converted_data_v3/udst_durationqa_conversational.jsonl")


if __name__ == "__main__":
    main()