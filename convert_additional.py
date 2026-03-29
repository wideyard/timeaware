#!/usr/bin/env python3
"""
Additional Data Conversion Script
================================
Handles:
1. ATOMIC - Fixed conversion with complete sentences
2. MCTACO - Extract correct answers
3. SocialIQA - Match labels to answers
4. PIQA - Extract correct answers

"""

import json
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import random

# Configuration
DATA_DIR = Path("data")
OUTPUT_DIR = Path("converted_data")


@dataclass
class ConvertedSample:
    """Single converted sample in unified format."""
    task: str
    sub_task: str
    context: str
    delta_t: str
    event: str
    query: str
    answer: str
    state: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    original_id: Optional[str] = None


def parse_atomic_list(value: str) -> List[str]:
    """Parse ATOMIC list values safely."""
    if not value or value == '[]':
        return []
    try:
        # Handle the format: ["item1", "item2"]
        result = eval(value)
        if isinstance(result, list):
            return [str(x).strip() for x in result if str(x).strip() and str(x).strip() != 'none']
        return []
    except:
        return []


class FixedATOMICConverter:
    """Fixed ATOMIC converter - generates complete sentences."""
    
    def __init__(self):
        self.samples = []
        
    def convert(self) -> List[ConvertedSample]:
        """Convert ATOMIC with complete event descriptions."""
        
        csv_file = DATA_DIR / "ATOMIC" / "v4_atomic_all_agg.csv"
        
        if not csv_file.exists():
            print(f"ATOMIC CSV file not found: {csv_file}")
            return self.samples
        
        print(f"Loading ATOMIC from {csv_file}...")
        df = pd.read_csv(csv_file)
        print(f"Processing {len(df)} ATOMIC events...")
        
        # Templates for filling in the blanks
        # Map of event patterns to fill-in suggestions
        fill_templates = {
            "PersonX uses PersonX's ___": ["phone", "money", "skills", "influence", "connections"],
            "PersonX changes ___": ["clothes", "mind", "direction", "plans", "jobs"],
            "PersonX thanks ___": ["PersonY", "their teacher", "their friend", "their parents"],
            "PersonX lets loose ___": ["the dog", "the birds", "their anger", "their emotions"],
            "PersonX calls ___": ["the police", "a meeting", "attention", "911"],
            "PersonX abandons ___": ["the plan", "the project", "their friends", "the idea"],
            "PersonX abolishes ___": ["the law", "the rule", "the system"],
            "PersonX about to get married": ["soon", "next month", "today"],
            "PersonX absolutely loved ___": ["the movie", "the book", "the gift", "the song"],
            "PersonX absorbs ___": ["the knowledge", "the information", "the lesson"],
            "PersonX abuses ___": ["their power", "their position", "their authority"],
            "PersonX accepts ___": ["the job", "the offer", "the invitation", "PersonY's apology"],
        }
        
        # Relation to query mapping
        relation_queries = {
            "oEffect": ("其他人会受到什么影响?", "T3-2", "causal_effect"),
            "oReact": ("其他人看到这个事件后的情绪反应是什么?", "T3-1", "commonsense_reaction"),
            "oWant": ("其他人之后想要做什么?", "T3-2", "desire"),
            "xEffect": ("PersonX身上会发生什么变化?", "T3-2", "causal_effect"),
            "xIntent": ("PersonX为什么这样做?(动机)", "T3-2", "intent"),
            "xNeed": ("PersonX做这件事之前需要什么?", "T3-2", "prerequisite"),
            "xReact": ("PersonX的情绪反应是什么?", "T3-1", "self_reaction"),
            "xWant": ("PersonX之后想要做什么?", "T3-2", "desire"),
            "xAttr": ("人们会如何评价PersonX的性格?", "T3-1", "personality"),
        }
        
        sample_id = 0
        
        for idx, row in df.iterrows():
            event = str(row.get('event', ''))
            if not event or event == 'nan':
                continue
            
            # Try to create a more complete event description
            complete_event = event
            
            # Fill in blanks with common options if possible
            for template, options in fill_templates.items():
                if template in event:
                    # Use first option as default fill
                    filled = event.replace("___", options[0])
                    complete_event = filled
                    break
            
            # Generate samples for each relation type
            for relation, (query_template, sub_task, state_type) in relation_queries.items():
                values = parse_atomic_list(str(row.get(relation, '[]')))
                
                if not values:
                    continue
                
                # Take up to 3 values per relation
                for value in values[:3]:
                    if not value or value == 'none':
                        continue
                    
                    sample = ConvertedSample(
                        task="T3",
                        sub_task=sub_task,
                        context=f"事件: {complete_event}",
                        delta_t="事件发生后",
                        event=complete_event,
                        query=query_template,
                        answer=value,
                        state={"type": state_type, "relation": relation},
                        reasoning=None,
                        original_id=f"atomic_{sample_id}"
                    )
                    self.samples.append(sample)
                    sample_id += 1
                    
                    # Limit samples
                    if sample_id >= 20000:
                        break
            
            if sample_id >= 20000:
                break
        
        print(f"Converted {len(self.samples)} ATOMIC samples")
        return self.samples
    
    def save(self, output_path: Path):
        """Save to JSONL."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
        print(f"Saved {len(self.samples)} samples to {output_path}")


class MCTACOConverter:
    """Converter for MCTACO dataset - extracts correct answers."""
    
    def __init__(self):
        self.samples = []
        
    def convert(self) -> List[ConvertedSample]:
        """Convert MCTACO with answer extraction.
        
        TSV format: context, question, answer, isGold, question_type
        """
        tsv_file = DATA_DIR / "MCTACO" / "dataset" / "dev_3783.tsv"
        
        if not tsv_file.exists():
            print(f"MCTACO file not found: {tsv_file}")
            return self.samples
        
        print(f"Loading MCTACO from {tsv_file}...")
        
        with open(tsv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"Processing {len(lines)} MCTACO samples...")
        
        sample_id = 0
        
        # Map question types to subtasks
        type_mapping = {
            "Stationarity": ("T1-1", "duration"),
            "Event Duration": ("T1-1", "duration"),
            "Event Ordering": ("T1-3", "ordering"),
            "Frequency": ("T1-1", "frequency"),
            "Typical Time": ("T1-2", "typical_time"),
        }
        
        for line in lines:
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue
            
            context = parts[0]
            question = parts[1]
            answer = parts[2]  # This is one answer option
            is_gold = parts[3]  # 'yes' or 'no' - indicates if this is correct
            q_type = parts[4]  # Question type
            
            # Only process gold (correct) answers
            if is_gold.lower() != 'yes':
                continue
            
            # Determine subtask
            sub_task, reason_type = type_mapping.get(q_type, ("T1-1", "temporal"))
            
            sample = ConvertedSample(
                task="T1",
                sub_task=sub_task,
                context=context,
                delta_t="当前时刻",
                event="问题相关事件",
                query=question,
                answer=answer,
                state={"type": reason_type, "question_type": q_type},
                reasoning=None,
                original_id=f"mctaco_{sample_id}"
            )
            self.samples.append(sample)
            sample_id += 1
        
        print(f"Converted {len(self.samples)} MCTACO samples (gold answers only)")
        return self.samples
    
    def save(self, output_path: Path):
        """Save to JSONL."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
        print(f"Saved {len(self.samples)} samples to {output_path}")


class SocialIQAConverter:
    """Converter for SocialIQA dataset - matches labels to answers."""
    
    def __init__(self):
        self.samples = []
        
    def convert(self, split: str = "train") -> List[ConvertedSample]:
        """Convert SocialIQA with label matching.
        
        JSONL format: context, question, answerA, answerB, answerC
        Labels file: 1/2/3 corresponding to answerA/B/C
        """
        jsonl_file = DATA_DIR / "SocialIQA" / f"{split}.jsonl"
        label_file = DATA_DIR / "SocialIQA" / f"{split}-labels.lst"
        
        if not jsonl_file.exists():
            print(f"SocialIQA file not found: {jsonl_file}")
            return self.samples
        
        print(f"Loading SocialIQA from {jsonl_file}...")
        
        # Load labels
        labels = []
        if label_file.exists():
            with open(label_file, 'r') as f:
                labels = [int(line.strip()) for line in f.readlines()]
        
        # Load data
        samples_data = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                samples_data.append(data)
        
        print(f"Processing {len(samples_data)} SocialIQA samples...")
        
        for idx, data in enumerate(samples_data):
            context = data.get('context', '')
            question = data.get('question', '')
            answer_a = data.get('answerA', '')
            answer_b = data.get('answerB', '')
            answer_c = data.get('answerC', '')
            
            answers = [answer_a, answer_b, answer_c]
            
            # Get correct answer from label
            label = labels[idx] if idx < len(labels) else 1
            correct_answer = answers[label - 1] if label <= len(answers) else answer_a
            
            # Map question type
            if "How would Others feel" in question:
                sub_task = "T3-1"
                state_type = "emotion_prediction"
            elif "What will Others want" in question or "What does Others want" in question:
                sub_task = "T3-2"
                state_type = "desire_prediction"
            elif "Why did" in question or "What was the reason" in question:
                sub_task = "T3-2"
                state_type = "intent_reasoning"
            else:
                sub_task = "T3-1"
                state_type = "social_reasoning"
            
            sample = ConvertedSample(
                task="T3",
                sub_task=sub_task,
                context=context,
                delta_t="当前情境",
                event="情境描述",
                query=question,
                answer=correct_answer,
                state={"type": state_type, "label": label},
                reasoning=None,
                original_id=f"socialiqa_{split}_{idx}"
            )
            self.samples.append(sample)
        
        print(f"Converted {len(self.samples)} SocialIQA samples")
        return self.samples
    
    def save(self, output_path: Path):
        """Save to JSONL."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
        print(f"Saved {len(self.samples)} samples to {output_path}")


class PIQAConverter:
    """Converter for PIQA dataset - extracts correct answers."""
    
    def __init__(self):
        self.samples = []
        
    def convert(self, input_file: Path = None) -> List[ConvertedSample]:
        """Convert PIQA with answer extraction.
        
        JSONL format: goal, sol1, sol2
        The correct answer is sol1 (sol1 is always the correct physical intuition)
        """
        if input_file is None:
            input_file = DATA_DIR / "PIQA" / "tests.jsonl"
        
        if not input_file.exists():
            print(f"PIQA file not found: {input_file}")
            return self.samples
        
        print(f"Loading PIQA from {input_file}...")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"Processing {len(lines)} PIQA samples...")
        
        # PIQA: sol1 is the correct answer (physically plausible)
        for idx, line in enumerate(lines):
            data = json.loads(line.strip())
            goal = data.get('goal', '')
            sol1 = data.get('sol1', '')  # Correct answer
            sol2 = data.get('sol2', '')  # Incorrect answer
            
            sample = ConvertedSample(
                task="T5",
                sub_task="T5-3",  # Physical commonsense
                context=f"目标: {goal}",
                delta_t="当前情境",
                event="物理操作",
                query="哪个解决方案是正确的物理操作?",
                answer=sol1,
                state={"type": "physical_commonsense", "correct_idx": 1},
                reasoning=None,
                original_id=f"piqa_{idx}"
            )
            self.samples.append(sample)
        
        print(f"Converted {len(self.samples)} PIQA samples")
        return self.samples
    
    def save(self, output_path: Path):
        """Save to JSONL."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
        print(f"Saved {len(self.samples)} samples to {output_path}")


def run_additional_conversion():
    """Run all additional conversions."""
    print("="*60)
    print("ADDITIONAL DATA CONVERSION")
    print("="*60)
    
    results = {}
    
    # 1. Fixed ATOMIC
    print("\n[1/4] Converting ATOMIC (fixed)...")
    converter = FixedATOMICConverter()
    converter.convert()
    output_path = OUTPUT_DIR / "atomic_fixed.jsonl"
    converter.save(output_path)
    results['atomic_fixed'] = len(converter.samples)
    
    # 2. MCTACO
    print("\n[2/4] Converting MCTACO...")
    converter = MCTACOConverter()
    converter.convert()
    output_path = OUTPUT_DIR / "mctaco.jsonl"
    converter.save(output_path)
    results['mctaco'] = len(converter.samples)
    
    # 3. SocialIQA
    print("\n[3/4] Converting SocialIQA...")
    converter = SocialIQAConverter()
    converter.convert("train")
    output_path = OUTPUT_DIR / "socialiqa_train.jsonl"
    converter.save(output_path)
    results['socialiqa_train'] = len(converter.samples)
    
    # 4. PIQA
    print("\n[4/4] Converting PIQA...")
    converter = PIQAConverter()
    converter.convert()
    output_path = OUTPUT_DIR / "piqa.jsonl"
    converter.save(output_path)
    results['piqa'] = len(converter.samples)
    
    # Summary
    print("\n" + "="*60)
    print("ADDITIONAL CONVERSION SUMMARY")
    print("="*60)
    for name, count in results.items():
        print(f"  {name}: {count} samples")
    print("="*60)
    print(f"Total: {sum(results.values())} samples")
    
    return results


if __name__ == "__main__":
    run_additional_conversion()
