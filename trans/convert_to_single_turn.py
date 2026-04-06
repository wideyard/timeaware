#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single-Turn Conversational Data Converter

This script converts multi-turn conversational datasets to single-turn format.
For each dataset, it extracts the core question and answer from the original data,
removing unnecessary dialogue turns and distractions.

Output format:
{
    "context": "...",
    "question": "核心问题",
    "answer": "答案",
    "difficulty": "medium|hard|easy",
    "source_id": "...",
    "source_dataset": "数据集名",
    "ground_truth": {...}
}

Output directory: converted_data_single/
"""

import json
import os
import hashlib
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict
import importlib

# =====================================================================
# Data Structures
# =====================================================================

@dataclass
class SingleTurnSample:
    """Single-turn conversational sample."""
    context: str
    question: str
    answer: str
    difficulty: str = "medium"
    source_id: str = ""
    source_dataset: str = ""
    ground_truth: Optional[Dict[str, Any]] = None

@dataclass
class DatasetReport:
    """Report for a dataset."""
    source: str
    total_samples: int
    difficulty_distribution: Dict[str, int]
    avg_context_length: float
    avg_question_length: float
    avg_answer_length: float

# =====================================================================
# Utility Functions
# =====================================================================

def generate_id(content: str, dataset: str, prefix: str = "") -> str:
    """Generate unique ID for each sample."""
    hash_input = f"{content}_{dataset}_{prefix}"
    hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:12]
    return f"{dataset}_{prefix}_{hash_val}"

def save_jsonl(samples: List[Dict], filepath: str):
    """Save samples to JSONL file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')

def save_report(report: Dict, filepath: str):
    """Save report to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

def calculate_statistics(samples: List[Dict], dataset_name: str) -> Dict:
    """Calculate statistics for a dataset."""
    stats = {
        "source": dataset_name,
        "total_samples": len(samples),
        "difficulty_distribution": defaultdict(int),
        "avg_context_length": 0,
        "avg_question_length": 0,
        "avg_answer_length": 0
    }
    
    if not samples:
        return stats
    
    context_lengths = []
    question_lengths = []
    answer_lengths = []
    
    for sample in samples:
        # Difficulty distribution
        diff = sample.get("difficulty", "medium")
        stats["difficulty_distribution"][diff] += 1
        
        # Lengths
        context_lengths.append(len(sample.get("context", "")))
        question_lengths.append(len(sample.get("question", "")))
        answer_lengths.append(len(sample.get("answer", "")))
    
    stats["avg_context_length"] = sum(context_lengths) / len(context_lengths)
    stats["avg_question_length"] = sum(question_lengths) / len(question_lengths)
    stats["avg_answer_length"] = sum(answer_lengths) / len(answer_lengths)
    stats["difficulty_distribution"] = dict(stats["difficulty_distribution"])
    
    return stats

def deduplicate_samples(samples: List[Dict], dataset_name: str) -> List[Dict]:
    """Remove duplicate samples based on question and answer content."""
    seen = set()
    unique_samples = []
    duplicates = 0
    
    for sample in samples:
        # Create a unique key based on question and answer
        # For most datasets, same question + answer = duplicate
        key = (
            sample.get("question", "").strip().lower(),
            sample.get("answer", "").strip().lower()
        )
        
        if key not in seen:
            seen.add(key)
            unique_samples.append(sample)
        else:
            duplicates += 1
    
    if duplicates > 0:
        print(f"  Deduplicated {dataset_name}: removed {duplicates} duplicates ({len(samples)} -> {len(unique_samples)})")
    
    return unique_samples

# =====================================================================
# Dataset Converters
# =====================================================================

# ----- PIQA Converter -----
def convert_piqa_to_single(data_dir: str) -> List[Dict]:
    """Convert PIQA dataset to single-turn format."""
    samples = []
    
    # Load PIQA data
    train_file = os.path.join(data_dir, "PIQA", "physicaliqa-train-dev", "train.jsonl")
    label_file = os.path.join(data_dir, "PIQA", "physicaliqa-train-dev", "train-labels.lst")
    
    if not os.path.exists(train_file):
        print(f"PIQA train file not found: {train_file}")
        return samples
    
    # Load data
    data = []
    with open(train_file, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    
    # Load labels
    labels = []
    if os.path.exists(label_file):
        with open(label_file, 'r', encoding='utf-8') as f:
            labels = [int(line.strip()) for line in f]
    
    for i, item in enumerate(data):
        goal = item.get("goal", "")
        sol1 = item.get("sol1", "")
        sol2 = item.get("sol2", "")
        sample_id = item.get("id", str(i))
        correct_idx = labels[i] if i < len(labels) else 0
        
        # Determine correct answer
        correct_answer = sol1 if correct_idx == 0 else sol2
        
        # Create single-turn question
        question = f"Which approach is correct for: {goal}? A: {sol1} B: {sol2}"
        context = goal
        
        sample = {
            "context": context,
            "question": question,
            "answer": f"Option {'A' if correct_idx == 0 else 'B'}: {correct_answer}",
            "difficulty": "medium",
            "source_id": f"piqa_{sample_id}",
            "source_dataset": "PIQA",
            "ground_truth": {
                "correct_answer": correct_answer,
                "correct_index": correct_idx,
                "goal": goal
            }
        }
        samples.append(sample)
    
    return samples

# ----- Tracie Converter -----
def convert_tracie_to_single(data_dir: str) -> List[Dict]:
    """Convert Tracie dataset to single-turn format."""
    samples = []
    
    # Load Tracie data
    train_file = os.path.join(data_dir, "tracie", "data", "iid", "tracie_train.txt")
    
    if not os.path.exists(train_file):
        print(f"Tracie train file not found: {train_file}")
        return samples
    
    with open(train_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            
            # Parse Tracie format: event: [query] story: [context] \t answer: [label]
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            
            main_part = parts[0]
            answer_part = parts[1] if len(parts) > 1 else ""
            
            # Extract event
            event_match = main_part.split("story:")
            if len(event_match) >= 2:
                event_part = event_match[0].replace("event:", "").strip()
                story_part = event_match[1].strip()
            else:
                event_part = main_part
                story_part = ""
            
            # Extract answer
            answer = ""
            if "answer:" in answer_part:
                answer = answer_part.split("answer:")[1].strip()
            
            # Create question
            question = f"Based on the story '{story_part[:200]}...', determine: {event_part}"
            context = story_part
            
            sample = {
                "context": context,
                "question": question,
                "answer": answer,
                "difficulty": "medium",
                "source_id": f"tracie_{line_num}",
                "source_dataset": "Tracie",
                "ground_truth": {
                    "event": event_part,
                    "story": story_part,
                    "answer": answer
                }
            }
            samples.append(sample)
    
    return samples

# ----- TimeQA Converter -----
def convert_timeqa_to_single(data_dir: str) -> List[Dict]:
    """Convert TimeQA dataset to single-turn format."""
    samples = []
    
    import gzip
    
    # Process easy files
    easy_files = [
        ("train.easy.json.gzip", "train_easy"),
        ("dev.easy.json", "dev_easy"),
        ("test.easy.json", "test_easy"),
        ("human_test.easy.json", "human_test_easy")
    ]
    
    hard_files = [
        ("train.hard.json.gzip", "train_hard"),
        ("dev.hard.json", "dev_hard"),
        ("test.hard.json", "test_hard"),
        ("human_test.hard.json", "human_test_hard")
    ]
    
    all_files = easy_files + hard_files
    
    for filename, split_name in all_files:
        filepath = os.path.join(data_dir, "TimeQA", "dataset", filename)
        
        if not os.path.exists(filepath):
            continue
        
        # Load data
        if filename.endswith('.gzip'):
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                data = [json.loads(line.strip()) for line in f if line.strip()]
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content.startswith('['):
                    data = json.loads(content)
                else:
                    data = [json.loads(line.strip()) for line in content.split('\n') if line.strip()]
        
        for i, item in enumerate(data):
            question = item.get("question", "")
            context = item.get("context", "")
            idx = item.get("idx", f"{split_name}_{i}")
            targets = item.get("targets", [])
            
            if not question or not targets:
                continue
            
            answer = targets[0] if targets else ""
            difficulty = "hard" if "hard" in split_name else "easy"
            
            sample = {
                "context": context[:2000] if len(context) > 2000 else context,
                "question": question,
                "answer": answer,
                "difficulty": difficulty,
                "source_id": f"timeqa_{idx}",
                "source_dataset": "TimeQA",
                "ground_truth": {
                    "original_question": question,
                    "all_answers": targets,
                    "idx": idx
                }
            }
            samples.append(sample)
    
    return samples

# ----- MCTACO Converter -----
def convert_mctaco_to_single(data_dir: str) -> List[Dict]:
    """Convert MCTACO dataset to single-turn format."""
    samples = []
    
    # Load MCTACO data
    train_file = os.path.join(data_dir, "MCTACO", "dataset", "dev_3783.tsv")
    
    if not os.path.exists(train_file):
        print(f"MCTACO file not found: {train_file}")
        return samples
    
    with open(train_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f):
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue
            
            context = parts[0]
            question = parts[1]
            answer = parts[2]
            label = parts[3]
            category = parts[4] if len(parts) > 4 else "unknown"
            
            # Only include correct answers (label == "yes")
            if label.lower() == "yes":
                sample = {
                    "context": context,
                    "question": question,
                    "answer": answer,
                    "difficulty": "medium",
                    "source_id": f"mctaco_{line_num}",
                    "source_dataset": "MCTACO",
                    "ground_truth": {
                        "question": question,
                        "answer": answer,
                        "category": category
                    }
                }
                samples.append(sample)
    
    return samples

# ----- TempReason Converter -----
def convert_tempreason_to_single(data_dir: str) -> List[Dict]:
    """Convert TempReason dataset to single-turn format."""
    samples = []
    
    files = [
        ("train_l1.json", "train_l1"),
        ("train_l2.json", "train_l2"),
        ("train_l3.json", "train_l3"),
        ("val_l1.json", "val_l1"),
        ("val_l2.json", "val_l2"),
        ("val_l3.json", "val_l3"),
        ("test_l1.jsonl", "test_l1"),
        ("test_l2.json", "test_l2"),
        ("test_l3.json", "test_l3")
    ]
    
    for filename, split_name in files:
        filepath = os.path.join(data_dir, "TempReason", filename)
        
        if not os.path.exists(filepath):
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content.startswith('['):
                data = json.loads(content)
            else:
                data = [json.loads(line.strip()) for line in content.split('\n') if line.strip()]
        
        for i, item in enumerate(data):
            question = item.get("question", "")
            date = item.get("date", "")
            text_answers = item.get("text_answers", {})
            answers = text_answers.get("text", [])
            item_id = item.get("id", str(i))
            
            if not question:
                continue
            
            answer = answers[0] if answers else ""
            
            # Infer difficulty from level
            level = split_name.split("_")[-1]
            difficulty = "easy" if level == "l1" else ("medium" if level == "l2" else "hard")
            
            sample = {
                "context": date,  # TempReason uses date as context
                "question": question,
                "answer": answer,
                "difficulty": difficulty,
                "source_id": f"tempreason_{split_name}_{item_id}",
                "source_dataset": "TempReason",
                "ground_truth": {
                    "question": question,
                    "date": date,
                    "answers": answers
                }
            }
            samples.append(sample)
    
    return samples

# ----- UDST-DurationQA Converter -----
def convert_udst_durationqa_to_single(data_dir: str) -> List[Dict]:
    """Convert UDST-DurationQA dataset to single-turn format."""
    samples = []
    
    files = [
        ("train.tsv", "train"),
        ("dev.tsv", "dev"),
        ("test.tsv", "test")
    ]
    
    for filename, split_name in files:
        filepath = os.path.join(data_dir, "UDST-DurationQA", "data", filename)
        
        if not os.path.exists(filepath):
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f):
                parts = line.strip().split('\t')
                if len(parts) < 4:
                    continue
                
                sentence = parts[0]
                question = parts[1]
                answer = parts[2]
                label = parts[3]
                
                # Only include correct answers
                if label.lower() == "yes":
                    sample = {
                        "context": sentence,
                        "question": question,
                        "answer": answer,
                        "difficulty": "medium",
                        "source_id": f"udst_durationqa_{split_name}_{line_num}",
                        "source_dataset": "UDST-DurationQA",
                        "ground_truth": {
                            "sentence": sentence,
                            "question": question,
                            "answer": answer
                        }
                    }
                    samples.append(sample)
    
    return samples

# ----- TimeDial Converter -----
def convert_timedial_to_single(data_dir: str) -> List[Dict]:
    """Convert TimeDial dataset to single-turn format."""
    samples = []
    
    filepath = os.path.join(data_dir, "TimeDial", "test.json")
    
    if not os.path.exists(filepath):
        print(f"TimeDial file not found: {filepath}")
        return samples
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for i, item in enumerate(data):
        conversation = item.get("conversation", [])
        correct1 = item.get("correct1", "")
        correct2 = item.get("correct2", "")
        
        if not conversation or not correct1:
            continue
        
        # Join conversation as context
        context = " ".join(conversation)
        
        # Create question about the missing information
        question = "What time-related information fills the <MASK> in this dialogue?"
        
        # Use correct answer
        answer = correct1 if correct1 != "none" else correct2
        
        # Replace mask in context for ground truth
        sample = {
            "context": context,
            "question": question,
            "answer": answer,
            "difficulty": "medium",
            "source_id": f"timedial_{item.get('id', i)}",
            "source_dataset": "TimeDial",
            "ground_truth": {
                "correct1": correct1,
                "correct2": correct2,
                "conversation": conversation
            }
        }
        samples.append(sample)
    
    return samples

# ----- NarrativeQA Converter -----
def convert_narrativeqa_to_single(data_dir: str) -> List[Dict]:
    """Convert NarrativeQA dataset to single-turn format."""
    samples = []
    
    filepath = os.path.join(data_dir, "narrative-qa", "queries.jsonl")
    
    if not os.path.exists(filepath):
        print(f"NarrativeQA file not found: {filepath}")
        return samples
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f):
            item = json.loads(line.strip())
            
            og_query = item.get("og_query", "")
            query = item.get("query", "")
            answer = item.get("answer", "")
            chunk_id = item.get("chunk_id", "")
            
            if not query or not answer:
                continue
            
            sample = {
                "context": f"Document chunk ID: {chunk_id}",
                "question": query,
                "answer": answer,
                "difficulty": "medium",
                "source_id": f"narrativeqa_{chunk_id}_{line_num}",
                "source_dataset": "NarrativeQA",
                "ground_truth": {
                    "original_query": og_query,
                    "query": query,
                    "answer": answer
                }
            }
            samples.append(sample)
    
    return samples

# ----- Winogrande Converter -----
def convert_winogrande_to_single(data_dir: str) -> List[Dict]:
    """Convert Winogrande dataset to single-turn format."""
    import pyarrow.parquet as pq
    
    samples = []
    
    variants = ["winogrande_xs", "winogrande_s", "winogrande_m", "winogrande_l", "winogrande_debiased"]
    splits = ["train", "validation", "test"]
    
    for variant in variants:
        for split in splits:
            filepath = os.path.join(data_dir, "winogrande", variant, f"{split}-00000-of-00001.parquet")
            
            if not os.path.exists(filepath):
                continue
            
            try:
                table = pq.read_table(filepath)
                df = table.to_pandas()
                
                for i, row in df.iterrows():
                    sentence = row.get("sentence", "")
                    option1 = row.get("option1", "")
                    option2 = row.get("option2", "")
                    answer_str = row.get("answer", "1")
                    answer = str(answer_str) if answer_str else "1"
                    
                    if not sentence or not option1 or not option2:
                        continue
                    
                    # Create question with options
                    question = f"Complete the sentence with the correct option.\nSentence: {sentence}\nOption A: {option1}\nOption B: {option2}"
                    
                    correct_answer = option1 if answer == "1" else option2
                    
                    sample = {
                        "context": sentence,
                        "question": question,
                        "answer": f"Option {'A' if answer == '1' else 'B'}: {correct_answer}",
                        "difficulty": "medium",
                        "source_id": f"winogrande_{variant}_{split}_{i}",
                        "source_dataset": f"Winogrande_{variant}",
                        "ground_truth": {
                            "sentence": sentence,
                            "option1": option1,
                            "option2": option2,
                            "correct_answer": answer
                        }
                    }
                    samples.append(sample)
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
                continue
    
    return samples

# ----- CosmosQA Converter -----
def convert_cosmosqa_to_single(data_dir: str) -> List[Dict]:
    """Convert CosmosQA dataset to single-turn format."""
    samples = []
    
    import csv
    
    filepath = os.path.join(data_dir, "CosmosQA", "data", "train.csv")
    
    if not os.path.exists(filepath):
        print(f"CosmosQA file not found: {filepath}")
        return samples
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            context = row.get("context", "")
            question = row.get("question", "")
            answer0 = row.get("answer0", "")
            answer1 = row.get("answer1", "")
            answer2 = row.get("answer2", "")
            answer3 = row.get("answer3", "")
            label_str = row.get("label", "0")
            label = int(label_str) if label_str.isdigit() else 0
            
            if not question:
                continue
            
            answers = [answer0, answer1, answer2, answer3]
            correct_answer = answers[label] if label < len(answers) else ""
            
            # Create question with all options
            full_question = f"{question}\nA: {answer0}\nB: {answer1}\nC: {answer2}\nD: {answer3}"
            
            sample = {
                "context": context,
                "question": full_question,
                "answer": f"Option {['A', 'B', 'C', 'D'][label]}: {correct_answer}",
                "difficulty": "medium",
                "source_id": f"cosmosqa_{i}",
                "source_dataset": "CosmosQA",
                "ground_truth": {
                    "correct_index": label,
                    "correct_answer": correct_answer,
                    "all_answers": answers
                }
            }
            samples.append(sample)
    
    return samples

# ----- HellaSwag Converter -----
def convert_hellaswag_to_single(data_dir: str) -> List[Dict]:
    """Convert HellaSwag dataset to single-turn format."""
    samples = []
    
    filepath = os.path.join(data_dir, "HellaSwag", "data", "hellaswag_train.jsonl")
    
    if not os.path.exists(filepath):
        print(f"HellaSwag file not found: {filepath}")
        return samples
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            item = json.loads(line.strip())
            
            ctx = item.get("ctx", "")
            endings = item.get("endings", [])
            label_str = item.get("label", "0")
            # Handle both string and int labels
            if isinstance(label_str, int):
                label = label_str
            else:
                label = int(label_str) if str(label_str).isdigit() else 0
            activity = item.get("activity_label", "")
            
            if not ctx or not endings:
                continue
            
            # Create question with all options
            options_text = "\n".join([f"Option {j}: {endings[j]}" for j in range(len(endings))])
            question = f"Complete the following context:\n{ctx}\n\n{options_text}"
            
            correct_answer = endings[label] if label < len(endings) else ""
            
            sample = {
                "context": ctx,
                "question": question,
                "answer": f"Option {label}: {correct_answer}",
                "difficulty": "medium",
                "source_id": f"hellaswag_{i}",
                "source_dataset": "HellaSwag",
                "ground_truth": {
                    "correct_index": label,
                    "correct_answer": correct_answer,
                    "activity": activity,
                    "all_endings": endings
                }
            }
            samples.append(sample)
    
    return samples

# ----- DROP Converter -----
def convert_drop_to_single(data_dir: str) -> List[Dict]:
    """Convert DROP dataset to single-turn format."""
    samples = []
    
    filepath = os.path.join(data_dir, "DROP", "DROP.jsonl")
    
    if not os.path.exists(filepath):
        print(f"DROP file not found: {filepath}")
        return samples
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            item = json.loads(line.strip())
            
            passage = item.get("passage", "")
            question = item.get("question", "")
            answers_spans = item.get("answers_spans", {})
            spans = answers_spans.get("spans", [])
            query_id = item.get("query_id", str(i))
            
            if not question or not spans:
                continue
            
            answer = spans[0] if spans else ""
            answer_type = answers_spans.get("types", ["unknown"])[0]
            
            sample = {
                "context": passage,
                "question": question,
                "answer": answer,
                "difficulty": "hard" if answer_type == "number" else "medium",
                "source_id": f"drop_{query_id}",
                "source_dataset": "DROP",
                "ground_truth": {
                    "answer": answer,
                    "answer_type": answer_type,
                    "all_answers": spans
                }
            }
            samples.append(sample)
    
    return samples

# ----- Choice-75 Converter -----
def convert_choice75_to_single(data_dir: str) -> List[Dict]:
    """Convert Choice-75 dataset to single-turn format."""
    samples = []
    
    # Find all JSON files in verb_phrase_manual
    base_path = os.path.join(data_dir, "choice-75", "data", "choice-75")
    
    for split in ["train", "dev"]:
        split_path = os.path.join(base_path, "verb_phrase_manual", split)
        if not os.path.exists(split_path):
            continue
        
        for filename in os.listdir(split_path):
            if not filename.endswith(".json"):
                continue
            
            filepath = os.path.join(split_path, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    item = json.load(f)
                
                goal = item.get("goal", "")
                steps = item.get("steps", [])
                branching_info = item.get("branching_info", {})
                
                if not goal or not branching_info:
                    continue
                
                branching_step = branching_info.get("branching_step", "")
                option1 = branching_info.get("option 1", "")
                option2 = branching_info.get("option 2", "")
                
                # Get scenarios - each has [scenario, correct_option, difficulty]
                # correct_option: 1 = option 1, 2 = option 2
                freeform_ra = branching_info.get("freeform_ra", [])
                
                # Create samples for each scenario
                for scenario_idx, scenario_data in enumerate(freeform_ra):
                    if len(scenario_data) < 3:
                        continue
                    
                    scenario = scenario_data[0]
                    correct_option = scenario_data[1]  # 1 or 2
                    difficulty = scenario_data[2] if len(scenario_data) > 2 else "medium"
                    
                    # Map difficulty values
                    if difficulty == "na":
                        difficulty = "medium"
                    
                    # Determine the correct answer
                    if correct_option == 1:
                        answer = f"A: {option1}"
                    elif correct_option == 2:
                        answer = f"B: {option2}"
                    else:
                        continue  # Skip invalid options
                    
                    # Create context from steps and scenario
                    branching_idx = branching_info.get("branching_idx", 0)
                    steps_before = " -> ".join(steps[:branching_idx + 1])
                    context = f"Goal: {goal}\nSteps completed so far: {steps_before}\nScenario: {scenario}"
                    
                    # Create question with options
                    question = f"At the step '{branching_step}', which option should be chosen given the scenario?\nA: {option1}\nB: {option2}"
                    
                    sample = {
                        "context": context,
                        "question": question,
                        "answer": answer,
                        "difficulty": difficulty,
                        "source_id": f"choice75_{item.get('index', filename)}_{scenario_idx}",
                        "source_dataset": "Choice-75",
                        "ground_truth": {
                            "goal": goal,
                            "branching_step": branching_step,
                            "option1": option1,
                            "option2": option2,
                            "scenario": scenario,
                            "correct_option": correct_option
                        }
                    }
                    samples.append(sample)
                
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
                continue
    
    return samples

# ----- UDS_T Converter -----
def convert_uds_t_to_single(data_dir: str) -> List[Dict]:
    """Convert UDS-T dataset to single-turn format.
    
    UDS-T contains temporal relation annotations between predicates.
    Column order (0-indexed):
    10: Pred1.Text, 12: Pred2.Text, 14: Pred1.Duration, 15: Pred2.Duration
    16: Pred1.Beg, 17: Pred1.End, 18: Pred2.Beg, 19: Pred2.End
    """
    samples = []
    
    filepath = os.path.join(data_dir, "UDS_T_v1.0", "time_eng_ud_v1.2_2015_10_30.tsv")
    
    if not os.path.exists(filepath):
        print(f"UDS-T file not found: {filepath}")
        return samples
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Header: Split	Annotator.ID	Sentence1.ID	Pred1.Span	Pred1.Token	Event1.ID	Sentence2.ID	Pred2.Span	Pred2.Token	Event2.ID	Pred1.Text	Pred1.Lemma	Pred2.Text	Pred2.Lemma	Pred1.Duration	Pred2.Duration	Pred1.Beg	Pred1.End	Pred2.Beg	Pred2.End	...
    # Columns (0-indexed): 10=Pred1.Text, 12=Pred2.Text, 14=Pred1.Duration, 15=Pred2.Duration, 16=Pred1.Beg, 17=Pred1.End, 18=Pred2.Beg, 19=Pred2.End
    
    for i, line in enumerate(lines[1:], start=1):
        parts = line.strip().split('\t')
        if len(parts) < 20:
            continue
        
        try:
            # Extract relevant columns
            pred1_text = parts[10].strip() if len(parts) > 10 else ""
            pred2_text = parts[12].strip() if len(parts) > 12 else ""
            pred1_duration = parts[14].strip() if len(parts) > 14 else ""
            pred2_duration = parts[15].strip() if len(parts) > 15 else ""
            pred1_beg = parts[16].strip() if len(parts) > 16 else ""
            pred1_end = parts[17].strip() if len(parts) > 17 else ""
            pred2_beg = parts[18].strip() if len(parts) > 18 else ""
            pred2_end = parts[19].strip() if len(parts) > 19 else ""
            
            if not pred1_text or not pred2_text:
                continue
            
            # Parse numeric values (remove spaces and convert to int)
            def parse_num(s):
                try:
                    return int(s.strip().replace(' ', ''))
                except (ValueError, AttributeError):
                    return -1
            
            beg1 = parse_num(pred1_beg)
            end1 = parse_num(pred1_end)
            beg2 = parse_num(pred2_beg)
            end2 = parse_num(pred2_end)
            
            # Skip if we can't parse the time points
            if beg1 < 0 or end1 < 0 or beg2 < 0 or end2 < 0:
                continue
            
            context = f"Event 1: {pred1_text} (duration: {pred1_duration})\nEvent 2: {pred2_text} (duration: {pred2_duration})"
            
            # Determine temporal relationship based on Beg/End points (0-100 scale)
            # Lower Beg = earlier start, Lower End = earlier finish
            
            if end1 <= beg2:
                # Event 1 ends before Event 2 starts
                answer = f"'{pred1_text}' occurs before '{pred2_text}'"
                rel_type = "before"
            elif end2 <= beg1:
                # Event 2 ends before Event 1 starts
                answer = f"'{pred2_text}' occurs before '{pred1_text}'"
                rel_type = "after"
            elif beg1 <= beg2 and end1 >= end2:
                # Event 1 contains Event 2
                answer = f"'{pred1_text}' contains '{pred2_text}'"
                rel_type = "contains"
            elif beg2 <= beg1 and end2 >= end1:
                # Event 2 contains Event 1
                answer = f"'{pred2_text}' contains '{pred1_text}'"
                rel_type = "contained_by"
            elif beg1 == beg2 and end1 == end2:
                # Both events start and end at the same time
                answer = f"'{pred1_text}' and '{pred2_text}' occur simultaneously"
                rel_type = "simultaneous"
            else:
                # Events overlap
                answer = f"'{pred1_text}' and '{pred2_text}' overlap in time"
                rel_type = "overlap"
            
            question = f"What is the temporal relationship between '{pred1_text}' and '{pred2_text}'?"
            
            # Determine difficulty based on relationship complexity
            difficulty = "hard" if rel_type in ["overlap", "contains", "contained_by"] else "medium"
            
            sample = {
                "context": context,
                "question": question,
                "answer": answer,
                "difficulty": difficulty,
                "source_id": f"uds_t_{i}",
                "source_dataset": "UDS_T",
                "ground_truth": {
                    "predicate1": pred1_text,
                    "predicate2": pred2_text,
                    "duration1": pred1_duration,
                    "duration2": pred2_duration,
                    "begin1": beg1,
                    "end1": end1,
                    "begin2": beg2,
                    "end2": end2,
                    "relationship": rel_type
                }
            }
            samples.append(sample)
        except Exception as e:
            # Skip malformed entries
            continue
    
    return samples

# ----- SocialIQA Converter -----
def convert_socialiqa_to_single(data_dir: str) -> List[Dict]:
    """Convert SocialIQA dataset to single-turn format."""
    samples = []
    
    # SocialIQA has train/dev splits with corresponding label files
    for split in ["train", "dev"]:
        # Data file
        data_path = os.path.join(data_dir, "SocialIQA", f"{split}.jsonl")
        if not os.path.exists(data_path):
            data_path = os.path.join(data_dir, "SocialIQA", "data", f"{split}.jsonl")
        
        # Label file
        label_path = os.path.join(data_dir, "SocialIQA", f"{split}-labels.lst")
        
        if not os.path.exists(data_path):
            continue
        
        # Load labels
        labels = []
        if os.path.exists(label_path):
            with open(label_path, 'r', encoding='utf-8') as f:
                labels = [int(line.strip()) for line in f if line.strip()]
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    item = json.loads(line.strip())
                    
                    context = item.get("context", "")
                    question = item.get("question", "")
                    answerA = item.get("answerA", "")
                    answerB = item.get("answerB", "")
                    answerC = item.get("answerC", "")
                    
                    if not question:
                        continue
                    
                    # Get correct answer from labels (1=A, 2=B, 3=C)
                    label = labels[i] if i < len(labels) else 1
                    answers = [answerA, answerB, answerC]
                    correct_answer = answers[label - 1] if 0 < label <= 3 else answerA
                    
                    # Create question with all options
                    full_question = f"{question}\nA: {answerA}\nB: {answerB}\nC: {answerC}"
                    
                    sample = {
                        "context": context,
                        "question": full_question,
                        "answer": f"Option {['A', 'B', 'C'][label-1]}: {correct_answer}",
                        "difficulty": "medium",
                        "source_id": f"socialiqa_{split}_{i}",
                        "source_dataset": "SocialIQA",
                        "ground_truth": {
                            "context": context,
                            "question": question,
                            "answerA": answerA,
                            "answerB": answerB,
                            "answerC": answerC,
                            "correct_label": label
                        }
                    }
                    samples.append(sample)
        except Exception as e:
            print(f"Error processing SocialIQA {split}: {e}")
    
    return samples

# ----- ProPara Converter -----
def convert_propara_to_single(data_dir: str) -> List[Dict]:
    """Convert ProPara dataset to single-turn format."""
    samples = []
    
    # Use the JSON files which have better structured data
    files = [
        ("data/naacl18/prolocal/propara.run1.train.json", "train"),
        ("data/naacl18/prolocal/propara.run1.dev.json", "dev"),
    ]
    
    for filename, split_name in files:
        filepath = os.path.join(data_dir, "ProPara", filename)
        
        if not os.path.exists(filepath):
            print(f"ProPara file not found: {filepath}")
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    
                    item = json.loads(line)
                    
                    # Extract instance info
                    instance = item.get("instance", "")
                    parts = instance.split("++++")
                    
                    if len(parts) < 4:
                        continue
                    
                    split = parts[0]  # train/dev/test
                    para_id = parts[1]  # paragraph ID
                    step_num = parts[2]  # step number
                    sentence = parts[3] if len(parts) > 3 else ""  # sentence
                    
                    entity = item.get("entity", item.get("", ""))
                    if not entity:
                        # Try to get entity from the data
                        entity_parts = parts[4].split("####") if len(parts) > 4 else []
                        entity = entity_parts[0] if entity_parts else ""
                    
                    # Get state change type
                    state_change = item.get("", "")
                    
                    # Generate question-answer pairs
                    question = f"What happens to {entity} in step {step_num}?"
                    context = sentence
                    
                    # Generate answer based on state change
                    # The data contains state tracking information, but we need meaningful answers
                    # For procedural text, we can ask about entity states
                    
                    sample = {
                        "context": context,
                        "question": question,
                        "answer": sentence,  # The sentence itself describes what happens
                        "difficulty": "medium",
                        "source_id": f"propara_{para_id}_{step_num}",
                        "source_dataset": "ProPara",
                        "ground_truth": {
                            "paragraph_id": para_id,
                            "step": step_num,
                            "entity": entity,
                            "sentence": sentence
                        }
                    }
                    samples.append(sample)
                    
        except Exception as e:
            print(f"Error processing ProPara {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    # Also try the grids.v1 JSON files which have better structure
    grids_files = [
        ("data/emnlp18/grids.v1.train.json", "train"),
        ("data/emnlp18/grids.v1.dev.json", "dev"),
    ]
    
    for filename, split_name in grids_files:
        filepath = os.path.join(data_dir, "ProPara", filename)
        
        if not os.path.exists(filepath):
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    item = json.loads(line)
                    
                    para_id = item.get("para_id", "")
                    sentences = item.get("sentence_texts", [])
                    participants = item.get("participants", [])
                    states = item.get("states", [])
                    
                    if not sentences or not participants:
                        continue
                    
                    # Create questions about entity states
                    for i, participant in enumerate(participants):
                        if i >= len(states):
                            continue
                        
                        participant_states = states[i]
                        
                        # Ask about initial and final states
                        initial_state = participant_states[0] if participant_states else "?"
                        final_state = participant_states[-1] if participant_states else "?"
                        
                        # Skip if states are unclear
                        if initial_state == "?" and final_state == "?":
                            continue
                        
                        # Context is the full procedure
                        context = " ".join(sentences)
                        
                        # Generate meaningful question-answer pairs
                        if initial_state != "?" and initial_state != "-":
                            question = f"Where is {participant} at the start?"
                            answer = initial_state
                            
                            sample = {
                                "context": context[:2000] if len(context) > 2000 else context,
                                "question": question,
                                "answer": answer,
                                "difficulty": "easy",
                                "source_id": f"propara_{para_id}_{participant}_start",
                                "source_dataset": "ProPara",
                                "ground_truth": {
                                    "paragraph_id": para_id,
                                    "participant": participant,
                                    "state": initial_state,
                                    "step": "start"
                                }
                            }
                            samples.append(sample)
                        
                        if final_state != "?" and final_state != "-":
                            question = f"Where is {participant} at the end?"
                            answer = final_state
                            
                            sample = {
                                "context": context[:2000] if len(context) > 2000 else context,
                                "question": question,
                                "answer": answer,
                                "difficulty": "easy",
                                "source_id": f"propara_{para_id}_{participant}_end",
                                "source_dataset": "ProPara",
                                "ground_truth": {
                                    "paragraph_id": para_id,
                                    "participant": participant,
                                    "state": final_state,
                                    "step": "end"
                                }
                            }
                            samples.append(sample)
                    
                    # Ask about the overall procedure
                    if len(sentences) > 1:
                        question = "What are the main steps in this procedure?"
                        answer = "; ".join(sentences[:3])  # First 3 sentences as summary
                        
                        sample = {
                            "context": context[:2000] if len(context) > 2000 else context,
                            "question": question,
                            "answer": answer,
                            "difficulty": "medium",
                            "source_id": f"propara_{para_id}_steps",
                            "source_dataset": "ProPara",
                            "ground_truth": {
                                "paragraph_id": para_id,
                                "sentences": sentences
                            }
                        }
                        samples.append(sample)
                    
        except Exception as e:
            print(f"Error processing ProPara grids {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    return samples

# ----- OpenPI Converter -----
def convert_openpi_to_single(data_dir: str) -> List[Dict]:
    """Convert OpenPI2.0 dataset to single-turn format."""
    samples = []
    
    # OpenPI2.0 has JSON files with procedure data
    files = [
        ("train-data-reformatted-v4.json", "train"),
        ("dev-data-reformatted-v4.json", "dev"),
        ("test-data-reformatted-v4.json", "test"),
    ]
    
    for filename, split_name in files:
        filepath = os.path.join(data_dir, "OpenPI2.0", "data", filename)
        
        if not os.path.exists(filepath):
            # Try alternative path
            filepath = os.path.join(data_dir, "OpenPI2.0", filename)
        
        if not os.path.exists(filepath):
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Data is a dict with keys like "1", "2", etc.
            for item_id, item in data.items():
                goal = item.get("goal", "")
                steps = item.get("steps", [])
                
                if not goal or not steps:
                    continue
                
                # Create context from goal and steps
                context = f"Goal: {goal}\n\nSteps:\n" + "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                
                # Create question about the procedure
                question = f"What are the steps to {goal.lower()}?"
                answer = " -> ".join(steps)
                
                # Determine difficulty based on number of steps
                difficulty = "easy" if len(steps) <= 3 else ("medium" if len(steps) <= 6 else "hard")
                
                sample = {
                    "context": context,
                    "question": question,
                    "answer": answer,
                    "difficulty": difficulty,
                    "source_id": f"openpi_{split_name}_{item_id}",
                    "source_dataset": "OpenPI",
                    "ground_truth": {
                        "goal": goal,
                        "steps": steps
                    }
                }
                samples.append(sample)
                
        except Exception as e:
            print(f"Error processing OpenPI {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    return samples

# ----- PASTA Converter -----
def convert_pasta_to_single(data_dir: str) -> List[Dict]:
    """Convert PASTA dataset to single-turn format."""
    samples = []
    
    # PASTA has train, val, test files
    files = [
        ("tr_data.jsonl", "train"),
        ("val_data.jsonl", "val"),
        ("te_data.jsonl", "test"),
    ]
    
    for filename, split_name in files:
        filepath = os.path.join(data_dir, "pasta", "data", filename)
        
        if not os.path.exists(filepath):
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    item = json.loads(line.strip())
                    
                    # PASTA format: Input.line1-5 are story sentences, Answer.assertion is the inferred state
                    lines = []
                    for j in range(1, 6):
                        line_key = f"Input.line{j}"
                        if line_key in item and item[line_key]:
                            lines.append(item[line_key])
                    
                    story = " ".join(lines)
                    assertion = item.get("Answer.assertion", "")
                    mod_assertion = item.get("Answer.mod_assertion", "")
                    
                    if not story or not assertion:
                        continue
                    
                    # Create question about the participant state
                    question = f"Based on the following story, what can be inferred about the participant's state?\nStory: {story}"
                    answer = assertion
                    
                    # Determine difficulty based on which lines support the assertion
                    supporting_lines = [j for j in range(1, 6) if item.get(f"Answer.line{j}.on", False)]
                    difficulty = "easy" if len(supporting_lines) >= 3 else ("medium" if len(supporting_lines) >= 2 else "hard")
                    
                    sample = {
                        "context": story,
                        "question": question,
                        "answer": answer,
                        "difficulty": difficulty,
                        "source_id": f"pasta_{split_name}_{i}",
                        "source_dataset": "PASTA",
                        "ground_truth": {
                            "story": story,
                            "assertion": assertion,
                            "counterfactual_assertion": mod_assertion,
                            "supporting_lines": supporting_lines
                        }
                    }
                    samples.append(sample)
                    
        except Exception as e:
            print(f"Error processing PASTA {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    return samples

# ----- LongBench Converter -----
def convert_longbench_to_single(data_dir: str) -> List[Dict]:
    """Convert LongBench dataset to single-turn format."""
    samples = []
    
    # LongBench has multiple .jsonl files in data/ subdirectory
    data_path = os.path.join(data_dir, "LongBench", "data")
    
    if not os.path.exists(data_path):
        print(f"LongBench data directory not found: {data_path}")
        return samples
    
    # Get all .jsonl files in the data directory
    jsonl_files = [f for f in os.listdir(data_path) if f.endswith('.jsonl') and not f.endswith('_e.jsonl')]
    
    for filename in jsonl_files:
        filepath = os.path.join(data_path, filename)
        dataset_name = filename.replace('.jsonl', '')
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    item = json.loads(line.strip())
                    
                    # LongBench format: input, context, answers
                    input_text = item.get("input", "")
                    context = item.get("context", "")
                    answers = item.get("answers", [])
                    answer = answers[0] if answers else ""
                    
                    if not input_text:
                        continue
                    
                    # Truncate context if too long
                    if len(context) > 4000:
                        context = context[:4000]
                    
                    # Determine difficulty based on context length
                    difficulty = "hard" if len(context) > 2000 else ("medium" if len(context) > 1000 else "easy")
                    
                    sample = {
                        "context": context,
                        "question": input_text,
                        "answer": answer,
                        "difficulty": difficulty,
                        "source_id": f"longbench_{dataset_name}_{i}",
                        "source_dataset": f"LongBench_{dataset_name}",
                        "ground_truth": {
                            "question": input_text,
                            "answers": answers,
                            "dataset": dataset_name
                        }
                    }
                    samples.append(sample)
                    
        except Exception as e:
            print(f"Error processing LongBench {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    return samples

# ----- QASPER Converter -----
def convert_qasper_to_single(data_dir: str) -> List[Dict]:
    """Convert QASPER dataset to single-turn format."""
    samples = []
    
    # QASPER has JSON files with paper data
    files = [
        ("qasper-train-v0.3.json", "train"),
        ("qasper-dev-v0.3.json", "dev"),
        ("qasper-test-v0.3.json", "test"),
    ]
    
    for filename, split_name in files:
        filepath = os.path.join(data_dir, "qasper", filename)
        
        if not os.path.exists(filepath):
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Data is a dict with paper IDs as keys
            for paper_id, paper_data in data.items():
                title = paper_data.get("title", "")
                abstract = paper_data.get("abstract", "")
                qas = paper_data.get("qas", [])
                
                # Create context from title and abstract
                context = f"Paper: {title}\n\nAbstract: {abstract}"
                if len(context) > 4000:
                    context = context[:4000]
                
                # Process question-answer pairs (qas is a list, not a dict)
                for qa_item in qas:
                    question = qa_item.get("question", "")
                    question_id = qa_item.get("question_id", "")
                    answers = qa_item.get("answers", [])
                    
                    if not question or not answers:
                        continue
                    
                    # Get first answer
                    ans_obj = answers[0] if answers else {}
                    answer_data = ans_obj.get("answer", {})
                    
                    # Check for different answer types
                    answer_text = ""
                    if answer_data.get("unanswerable", False):
                        answer_text = "Unanswerable based on the paper."
                    elif answer_data.get("yes_no") is not None:
                        answer_text = "Yes" if answer_data.get("yes_no") else "No"
                    elif answer_data.get("free_form_answer"):
                        answer_text = answer_data.get("free_form_answer", "")
                    elif answer_data.get("extractive_spans"):
                        extractive = answer_data.get("extractive_spans", [])
                        answer_text = " ".join(extractive) if extractive else ""
                    
                    if not answer_text:
                        continue
                    
                    # Determine difficulty based on answer type
                    difficulty = "medium"
                    if answer_data.get("unanswerable", False):
                        difficulty = "hard"
                    
                    sample = {
                        "context": context,
                        "question": question,
                        "answer": answer_text,
                        "difficulty": difficulty,
                        "source_id": f"qasper_{split_name}_{paper_id}_{question_id}",
                        "source_dataset": "QASPER",
                        "ground_truth": {
                            "paper_id": paper_id,
                            "title": title,
                            "question": question,
                            "answer": answer_text
                        }
                    }
                    samples.append(sample)
                    
        except Exception as e:
            print(f"Error processing QASPER {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    return samples

# ----- SituatedGen Converter -----
def convert_situatedgen_to_single(data_dir: str) -> List[Dict]:
    """Convert SituatedGen dataset to single-turn format."""
    samples = []
    
    # SituatedGen has train, dev, test files
    files = [
        ("train.jsonl", "train"),
        ("dev.jsonl", "dev"),
        ("test.jsonl", "test"),
    ]
    
    for filename, split_name in files:
        filepath = os.path.join(data_dir, "situated_gen", "data", filename)
        
        if not os.path.exists(filepath):
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    item = json.loads(line.strip())
                    
                    # SituatedGen format: keywords, statement, statements
                    keywords = item.get("keywords", [])
                    statement = item.get("statement", "")
                    statements = item.get("statements", [])
                    
                    if not statement:
                        continue
                    
                    # Create context from keywords
                    context = f"Keywords: {', '.join(keywords)}"
                    
                    # Create question asking to generate a statement using keywords
                    question = f"Generate a coherent statement using the following keywords: {', '.join(keywords)}"
                    answer = statement
                    
                    # Determine difficulty based on number of keywords
                    difficulty = "easy" if len(keywords) <= 4 else ("medium" if len(keywords) <= 6 else "hard")
                    
                    sample = {
                        "context": context,
                        "question": question,
                        "answer": answer,
                        "difficulty": difficulty,
                        "source_id": f"situatedgen_{split_name}_{i}",
                        "source_dataset": "SituatedGen",
                        "ground_truth": {
                            "keywords": keywords,
                            "statement": statement,
                            "statements": statements
                        }
                    }
                    samples.append(sample)
                    
        except Exception as e:
            print(f"Error processing SituatedGen {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    return samples

# ----- PIQA (additional formats) -----
def convert_piqa_additional(data_dir: str) -> List[Dict]:
    """Additional PIQA conversion for test set."""
    samples = []
    
    test_file = os.path.join(data_dir, "PIQA", "tests.jsonl")
    
    if not os.path.exists(test_file):
        return samples
    
    with open(test_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            item = json.loads(line.strip())
            goal = item.get("goal", "")
            sol1 = item.get("sol1", "")
            sol2 = item.get("sol2", "")
            
            question = f"Which is correct for: {goal}?\nA: {sol1}\nB: {sol2}"
            
            sample = {
                "context": goal,
                "question": question,
                "answer": "Answer not provided in test set",
                "difficulty": "medium",
                "source_id": f"piqa_test_{i}",
                "source_dataset": "PIQA",
                "ground_truth": {
                    "goal": goal,
                    "sol1": sol1,
                    "sol2": sol2
                }
            }
            samples.append(sample)
    
    return samples

# =====================================================================
# Main Converter Function
# =====================================================================

CONVERTERS = {
    "PIQA": convert_piqa_to_single,
    "Tracie": convert_tracie_to_single,
    "TimeQA": convert_timeqa_to_single,
    "MCTACO": convert_mctaco_to_single,
    "TempReason": convert_tempreason_to_single,
    "UDST-DurationQA": convert_udst_durationqa_to_single,
    "TimeDial": convert_timedial_to_single,
    "NarrativeQA": convert_narrativeqa_to_single,
    "Winogrande": convert_winogrande_to_single,
    "CosmosQA": convert_cosmosqa_to_single,
    "HellaSwag": convert_hellaswag_to_single,
    "DROP": convert_drop_to_single,
    "Choice-75": convert_choice75_to_single,
    "UDS_T": convert_uds_t_to_single,
    "SocialIQA": convert_socialiqa_to_single,
    "ProPara": convert_propara_to_single,
    "OpenPI": convert_openpi_to_single,
    "PASTA": convert_pasta_to_single,
    "LongBench": convert_longbench_to_single,
    "QASPER": convert_qasper_to_single,
    "SituatedGen": convert_situatedgen_to_single,
}

def convert_all_datasets(data_dir: str, output_dir: str):
    """Convert all datasets to single-turn format."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    all_stats = {}
    
    for dataset_name, converter_func in CONVERTERS.items():
        print(f"\n{'='*60}")
        print(f"Converting {dataset_name}...")
        print(f"{'='*60}")
        
        try:
            samples = converter_func(data_dir)
            
            if not samples:
                print(f"No samples generated for {dataset_name}")
                continue
            
            # Deduplicate samples
            samples = deduplicate_samples(samples, dataset_name)
            
            if not samples:
                print(f"No samples remaining after deduplication for {dataset_name}")
                continue
            
            # Save JSONL
            output_file = os.path.join(output_dir, f"{dataset_name.lower()}.jsonl")
            save_jsonl(samples, output_file)
            
            # Calculate and save report
            stats = calculate_statistics(samples, dataset_name)
            report_file = os.path.join(output_dir, f"{dataset_name.lower()}_report.json")
            save_report(stats, report_file)
            
            all_stats[dataset_name] = stats
            
            print(f"Generated {len(samples)} samples for {dataset_name}")
            print(f"Saved to {output_file}")
            
        except Exception as e:
            print(f"Error converting {dataset_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Print summary
    print(f"\n{'='*60}")
    print("CONVERSION SUMMARY")
    print(f"{'='*60}")
    
    total_samples = 0
    for dataset_name, stats in all_stats.items():
        print(f"{dataset_name}: {stats['total_samples']} samples")
        total_samples += stats['total_samples']
    
    print(f"\nTotal samples across all datasets: {total_samples}")
    print(f"Output directory: {output_dir}")

# =====================================================================
# Entry Point
# =====================================================================

def main():
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Default paths
    data_dir = os.path.join(os.path.dirname(script_dir), "data")
    output_dir = os.path.join(os.path.dirname(script_dir), "converted_data_single")
    
    print("=" * 60)
    print("Single-Turn Conversational Data Converter")
    print("=" * 60)
    print(f"Data directory: {data_dir}")
    print(f"Output directory: {output_dir}")
    
    convert_all_datasets(data_dir, output_dir)

if __name__ == "__main__":
    main()