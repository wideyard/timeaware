#!/usr/bin/env python3
"""
Reformat All Datasets to Unified TemporalSample Format
======================================================

将所有已转换的数据集重新格式化为包含完整ground_truth的TemporalSample格式。

Author: TimeAware Benchmark Team
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import hashlib

DATA_DIR = Path("data")
INPUT_DIR = Path("converted_data")
OUTPUT_DIR = Path("converted_data_v2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TemporalSample:
    """统一的TemporalSample数据格式"""
    id: str
    task: str
    sub_task: str
    context: str
    query: str
    answer: str
    ground_truth: Dict[str, Any]
    delta_t: Optional[str] = None
    event: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.state is None:
            self.state = {}
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_jsonl(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


def reformat_sample(data: Dict, source: str, idx: int) -> Optional[TemporalSample]:
    """将旧格式样本重新格式化为新的TemporalSample格式"""
    
    # Extract or generate ID
    sample_id = data.get('id') or data.get('original_id') or f"{source}_{idx}"
    if not isinstance(sample_id, str):
        sample_id = f"{source}_{idx}"
    
    # Extract task info
    task = data.get('task', 'T1')
    sub_task = data.get('sub_task', 'T1-1')
    
    # Extract context and query
    context = data.get('context', '')
    query = data.get('query', '')
    if not query:
        query = data.get('question', '') or data.get('input', '')
    
    # Extract answer
    answer = data.get('answer', '')
    if not answer:
        answer = data.get('answers', [''])[0] if isinstance(data.get('answers'), list) else str(data.get('answers', ''))
    
    # Build ground_truth from various fields
    ground_truth = {}
    
    # Preserve original answer in ground_truth
    if answer:
        ground_truth['answer'] = answer
    
    # Add label if present
    if 'label' in data:
        ground_truth['label'] = data['label']
    
    # Add original_id if present
    if 'original_id' in data:
        ground_truth['original_id'] = data['original_id']
    
    # Add evidence/supporting facts if present
    if 'evidence' in data:
        ground_truth['evidence'] = data['evidence']
    
    # Add state info to ground_truth
    if 'state' in data and data['state']:
        state = data['state']
        if isinstance(state, dict):
            ground_truth['state'] = state
    
    # Add reasoning if present
    if 'reasoning' in data:
        ground_truth['reasoning'] = data['reasoning']
    
    # For TimeQA/DROP style data
    if 'type' in data.get('state', {}):
        ground_truth['type'] = data['state']['type']
    
    # For MCTACO style data
    if 'category' in data:
        ground_truth['category'] = data['category']
    
    # Build complete ground_truth if empty
    if not ground_truth:
        ground_truth = {
            'answer': answer,
            'source': source
        }
    
    # Extract other fields
    delta_t = data.get('delta_t', '')
    event = data.get('event', '')
    state = data.get('state', {})
    reasoning = data.get('reasoning', '')
    
    # Build metadata
    metadata = {
        'source': source,
        'original_task': task,
        'original_subtask': sub_task
    }
    
    # Add any additional fields to metadata
    for key in ['difficulty', 'category', 'type', 'question_type']:
        if key in data:
            metadata[key] = data[key]
    
    try:
        return TemporalSample(
            id=sample_id,
            task=task,
            sub_task=sub_task,
            context=context,
            query=query,
            answer=answer,
            ground_truth=ground_truth,
            delta_t=delta_t,
            event=event,
            state=state,
            reasoning=reasoning,
            metadata=metadata
        )
    except Exception as e:
        print(f"Error creating sample {sample_id}: {e}")
        return None


def process_file(input_file: Path, source: str) -> tuple[int, int]:
    """处理单个JSONL文件
    
    Returns:
        (total_count, success_count)
    """
    print(f"Processing {input_file.name}...")
    
    total = 0
    success = 0
    output_file = OUTPUT_DIR / input_file.name
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        for idx, line in enumerate(f_in):
            total += 1
            try:
                data = json.loads(line.strip())
                sample = reformat_sample(data, source, idx)
                if sample:
                    f_out.write(sample.to_jsonl() + '\n')
                    success += 1
            except Exception as e:
                print(f"  Error at line {idx}: {e}")
    
    print(f"  Processed {success}/{total} samples")
    return total, success


def reformat_dataset(input_file: Path, output_file: Path, source: str, transform_fn=None) -> tuple[int, int]:
    """重新格式化数据集"""
    print(f"Reformatting {input_file.name}...")
    
    total = 0
    success = 0
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        for idx, line in enumerate(f_in):
            total += 1
            try:
                data = json.loads(line.strip())
                
                if transform_fn:
                    data = transform_fn(data, source, idx)
                
                sample = reformat_sample(data, source, idx)
                if sample:
                    f_out.write(sample.to_jsonl() + '\n')
                    success += 1
            except Exception as e:
                print(f"  Error at line {idx}: {e}")
    
    print(f"  Reformatted {success}/{total} samples")
    return total, success


# ============================================================================
# Dataset-specific transformers
# ============================================================================

def transform_timeqa(data: Dict, source: str, idx: int) -> Dict:
    """Transform TimeQA samples"""
    # Ensure delta_t is properly formatted
    if 'delta_t' in data and '从' in str(data.get('delta_t', '')):
        data['delta_t'] = data['delta_t']  # Keep Chinese format
    return data


def transform_mctaco(data: Dict, source: str, idx: int) -> Dict:
    """Transform MCTACO samples"""
    # Add category to metadata
    if 'category' not in data:
        # Infer from context
        context = data.get('context', '')
        if 'how long' in context.lower() or 'how many' in context.lower():
            data['category'] = 'Duration'
        elif 'before' in context.lower() or 'after' in context.lower():
            data['category'] = 'Ordering'
        else:
            data['category'] = 'Unknown'
    return data


def transform_propara(data: Dict, source: str, idx: int) -> Dict:
    """Transform ProPara samples with proper answer"""
    # Build answer from state if empty
    if not data.get('answer') and data.get('state'):
        state = data['state']
        answer_parts = []
        for entity, location in state.items():
            if location and location not in ['-', '', '?']:
                answer_parts.append(f"{entity}: {location}")
        data['answer'] = '; '.join(answer_parts) if answer_parts else ''
    return data


def transform_atomic(data: Dict, source: str, idx: int) -> Dict:
    """Transform ATOMIC samples"""
    # ATOMIC should already have proper structure from conflict detection
    return data


def transform_piqa(data: Dict, source: str, idx: int) -> Dict:
    """Transform PIQA samples"""
    # Add goal as context
    if 'goal' in data:
        data['context'] = data.get('context', '') or f"Goal: {data['goal']}"
    return data


def transform_socialiqa(data: Dict, source: str, idx: int) -> Dict:
    """Transform SocialIQA samples"""
    # Ensure proper context format
    if 'context' not in data and 'input' in data:
        data['context'] = data['input']
    return data


def transform_narrativeqa(data: Dict, source: str, idx: int) -> Dict:
    """Transform NarrativeQA samples"""
    # NarrativeQA should already have context
    if 'answers' in data and isinstance(data['answers'], list):
        data['answer'] = data['answers'][0] if data['answers'] else ''
    return data


def transform_hellaswag(data: Dict, source: str, idx: int) -> Dict:
    """Transform HellaSwag samples"""
    # Add proper context
    if 'context' not in data:
        data['context'] = data.get('activity_label', '') + ' ' + data.get('ctx', '')
    return data


def transform_winogrande(data: Dict, source: str, idx: int) -> Dict:
    """Transform Winogrande samples"""
    # Winogrande structure
    if 'sentence' in data:
        data['context'] = data['sentence']
    return data


def transform_cosmosqa(data: Dict, source: str, idx: int) -> Dict:
    """Transform CosmosQA samples"""
    # CosmosQA structure
    if 'context' not in data and 'context' in data:
        pass  # Already has context
    return data


# ============================================================================
# Main processing
# ============================================================================

def main():
    """Main entry point"""
    print("=" * 60)
    print("REFORMATTING ALL DATASETS TO TEMPORAL SAMPLE FORMAT")
    print("=" * 60)
    
    results = {}
    
    # Mapping of files to their transformers
    DATASET_TRANSFORMERS = {
        'timeqa_dev.jsonl': ('TimeQA', transform_timeqa),
        'timeqa_easy.jsonl': ('TimeQA', transform_timeqa),
        'timeqa_hard.jsonl': ('TimeQA', transform_timeqa),
        'timeqa_test.jsonl': ('TimeQA', transform_timeqa),
        'timeqa_train.jsonl': ('TimeQA', transform_timeqa),
        'drop.jsonl': ('DROP', None),
        'mctaco.jsonl': ('MCTACO', transform_mctaco),
        'propara.jsonl': ('ProPara', transform_propara),
        'propara_fixed.jsonl': ('ProPara', transform_propara),
        'propara_fixed_v2.jsonl': ('ProPara', transform_propara),
        'atomic_fixed.jsonl': ('ATOMIC', transform_atomic),
        'piqa.jsonl': ('PIQA', transform_piqa),
        'socialiqa_train.jsonl': ('SocialIQA', transform_socialiqa),
        'narrativeqa.jsonl': ('NarrativeQA', transform_narrativeqa),
        'hellaswag.jsonl': ('HellaSwag', transform_hellaswag),
        'winogrande.jsonl': ('Winogrande', transform_winogrande),
        'cosmosqa.jsonl': ('CosmosQA', transform_cosmosqa),
        # Already properly formatted
        'openpi2_t2.jsonl': ('OpenPI2', None),
        'pasta_t2_t5.jsonl': ('PASTA', None),
        't3_conflict_detection.jsonl': ('T3_Conflict', None),
        't5_counterfactual.jsonl': ('T5_Counterfactual', None),
        'trip_conflict_t3.jsonl': ('TRIP', None),
        'situated_gen_t2_t5.jsonl': ('SituatedGen', None),
        'longbench_qasper_t4.jsonl': ('LongBench', None),
        'dialogue_temporal_benchmark.jsonl': ('DialogueTemporal', None),
    }
    
    total_samples = 0
    total_success = 0
    
    for filename, (source, transformer) in DATASET_TRANSFORMERS.items():
        input_file = INPUT_DIR / filename
        if not input_file.exists():
            print(f"Skipping {filename} - file not found")
            continue
        
        output_file = OUTPUT_DIR / filename
        
        if transformer:
            t, s = reformat_dataset(input_file, output_file, source, transformer)
        else:
            t, s = process_file(input_file, source)
        
        results[source] = {'total': t, 'success': s, 'rate': s/t*100 if t > 0 else 0}
        total_samples += t
        total_success += s
    
    # Copy already properly formatted files
    for filename in ['openpi2_t2.jsonl', 'pasta_t2_t5.jsonl', 't3_conflict_detection.jsonl',
                     't5_counterfactual.jsonl', 'trip_conflict_t3.jsonl', 'situated_gen_t2_t5.jsonl',
                     'longbench_qasper_t4.jsonl', 'dialogue_temporal_benchmark.jsonl']:
        input_file = INPUT_DIR / filename
        output_file = OUTPUT_DIR / filename
        if input_file.exists() and not output_file.exists():
            import shutil
            shutil.copy(input_file, output_file)
            # Count lines
            with open(output_file, 'r', encoding='utf-8') as f:
                count = sum(1 for _ in f)
            results[filename.replace('.jsonl', '')] = {'total': count, 'success': count, 'rate': 100.0}
    
    # Print summary
    print("\n" + "=" * 60)
    print("REFORMATTING SUMMARY")
    print("=" * 60)
    print(f"Total samples processed: {total_samples}")
    print(f"Successfully reformatted: {total_success}")
    print(f"Success rate: {total_success/total_samples*100:.1f}%" if total_samples > 0 else "N/A")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    
    print("\nDataset breakdown:")
    for name, stats in sorted(results.items()):
        print(f"  {name}: {stats['success']}/{stats['total']} ({stats['rate']:.1f}%)")
    
    # Save summary
    summary = {
        'total_samples': total_samples,
        'total_success': total_success,
        'success_rate': total_success / total_samples * 100 if total_samples > 0 else 0,
        'datasets': results
    }
    
    with open(OUTPUT_DIR / 'reformat_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\nSummary saved to: {OUTPUT_DIR / 'reformat_summary.json'}")


if __name__ == "__main__":
    main()