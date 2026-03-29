#!/usr/bin/env python3
"""
Fix Script: Add answers to converted datasets
==============================================
1. DROP - Extract from answers_spans
2. TimeQA - Extract from annotated_*.json
3. ProPara - Move state to answer field
4. ATOMIC - Filter out nonsensical template matches
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

DATA_DIR = Path("data")
OUTPUT_DIR = Path("converted_data")


@dataclass
class ConvertedSample:
    task: str
    sub_task: str
    context: str
    delta_t: str
    event: str
    query: str
    answer: str
    state: Any = None
    reasoning: Any = None
    original_id: Any = None


def load_jsonl(path: Path) -> List[dict]:
    samples = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            samples.append(json.loads(line.strip()))
    return samples


def save_jsonl(samples: List[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + '\n')
    print(f"Saved {len(samples)} samples to {path}")


def fix_drop():
    """Fix DROP - extract answers from answers_spans."""
    print("\n[1/4] Fixing DROP...")
    
    input_path = DATA_DIR / "DROP" / "validation-00000-of-00001.parquet"
    output_path = OUTPUT_DIR / "drop.jsonl"
    
    df = pd.read_parquet(input_path)
    samples = []
    
    for _, row in df.iterrows():
        passage = row.get('passage', '')
        question = row.get('question', '')
        answers_spans = row.get('answers_spans', {})
        
        # Extract answer from spans
        answer = ""
        if answers_spans and 'spans' in answers_spans:
            spans = answers_spans['spans']
            if len(spans) > 0:
                answer = str(spans[0])
        
        # Only include temporal questions
        if any(kw in question.lower() for kw in ['when', 'how many', 'how much', 'year', 'day', 'time', 'quarter', 'first', 'second', 'minute', 'hour', 'score', 'point']):
            sample = {
                "task": "T1",
                "sub_task": "T1-2",
                "context": passage,
                "delta_t": "计算中",
                "event": "数值推理",
                "query": question,
                "answer": answer,
                "state": {"type": "numerical_temporal"},
                "reasoning": None,
                "original_id": str(row.get('query_id', ''))
            }
            samples.append(sample)
    
    save_jsonl(samples, output_path)
    print(f"  Fixed {len(samples)} DROP samples")
    return len(samples)


def fix_timeqa():
    """Fix TimeQA - extract answers from annotated files."""
    print("\n[2/4] Fixing TimeQA...")
    
    total = 0
    
    # Process annotated files
    annotated_files = [
        ("annotated_train.json", "train"),
        ("annotated_dev.json", "dev"),
        ("annotated_test.json", "test"),
    ]
    
    for filename, split in annotated_files:
        input_path = DATA_DIR / "TimeQA" / "dataset" / filename
        if not input_path.exists():
            continue
            
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        samples = []
        
        for item in data:
            questions = item.get('questions', [])
            paras = item.get('paras', [])
            
            for q in questions:
                # q[0] = time period, q[1] = answer spans
                time_period = q[0]
                answer_spans = q[1]
                
                for ans_info in answer_spans:
                    # ans_info = {para, from, end, answer}
                    answer = ans_info.get('answer', '')
                    if not answer:
                        continue
                    
                    # Get context from para
                    para_idx = ans_info.get('para', 0)
                    context = ""
                    if para_idx < len(paras):
                        context = paras[para_idx]
                    
                    # Build query with time period
                    query = f"What was the answer from {time_period[0]} to {time_period[1]}?"
                    
                    sample = {
                        "task": "T1",
                        "sub_task": "T1-1",
                        "context": context,
                        "delta_t": f"从 {time_period[0]} 到 {time_period[1]}",
                        "event": "时间推理",
                        "query": query,
                        "answer": answer,
                        "state": {"type": "temporal_position"},
                        "reasoning": None,
                        "original_id": item.get('index', '')
                    }
                    samples.append(sample)
        
        if samples:
            output_path = OUTPUT_DIR / f"timeqa_{split}.jsonl"
            save_jsonl(samples, output_path)
            print(f"  Fixed {len(samples)} TimeQA {split} samples")
            total += len(samples)
    
    return total


def fix_propara():
    """Fix ProPara - move state to answer field."""
    print("\n[3/4] Fixing ProPara...")
    
    input_path = OUTPUT_DIR / "propara.jsonl"
    output_path = OUTPUT_DIR / "propara_fixed.jsonl"
    
    samples = load_jsonl(input_path)
    fixed_samples = []
    
    for s in samples:
        # Move state to answer
        state = s.get('state', {})
        if state:
            # Format state as answer
            state_str = ", ".join([f"{k}: {v}" for k, v in state.items()])
            s['answer'] = state_str
        
        fixed_samples.append(s)
    
    save_jsonl(fixed_samples, output_path)
    print(f"  Fixed {len(fixed_samples)} ProPara samples")
    return len(fixed_samples)


def fix_atomic():
    """Fix ATOMIC - filter to only use sensible answer-event pairs."""
    print("\n[4/4] Fixing ATOMIC...")
    
    input_path = OUTPUT_DIR / "atomic_fixed.jsonl"
    output_path = OUTPUT_DIR / "atomic_fixed.jsonl"
    
    samples = load_jsonl(input_path)
    filtered_samples = []
    
    # Filter criteria:
    # 1. Answer should be a reasonable response to the event
    # 2. Avoid answers with pronouns that don't match (she/he/they when event has PersonX)
    # 3. Prefer short, generic answers that make sense as template responses
    
    # Answers that are clearly mismatched (from different events)
    bad_patterns = [
        "She ran to the bathroom",  # Doesn't relate to "PersonX 'd better go"
        "She finally made it",
    ]
    
    for s in samples:
        answer = s.get('answer', '')
        event = s.get('event', '')
        
        # Skip clearly bad matches
        if answer in bad_patterns:
            continue
        
        # Skip very long answers that seem like different events
        if len(answer.split()) > 10:
            continue
        
        # Accept the sample
        filtered_samples.append(s)
    
    save_jsonl(filtered_samples, output_path)
    print(f"  Filtered {len(samples)} -> {len(filtered_samples)} ATOMIC samples")
    return len(filtered_samples)


def main():
    print("="*60)
    print("FIX ANSWERS IN CONVERTED DATA")
    print("="*60)
    
    results = {}
    
    results['drop'] = fix_drop()
    results['timeqa'] = fix_timeqa()
    results['propara'] = fix_propara()
    results['atomic'] = fix_atomic()
    
    print("\n" + "="*60)
    print("FIX SUMMARY")
    print("="*60)
    for name, count in results.items():
        print(f"  {name}: {count} samples")
    print("="*60)


if __name__ == "__main__":
    main()
