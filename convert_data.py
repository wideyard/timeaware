#!/usr/bin/env python3
"""
Data Conversion Framework for Temporal World Modeling
=====================================================
Converts various datasets to the unified Temporal World Modeling format.

Input Format:
    [Context / 对话历史]
    [时间推进 Δt]
    [事件 a_t]
    [问题 Query]

Output Format:
    {
        "answer": "...",
        "state": {...},
        "reasoning": "..."
    }
"""

import json
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import re

# Configuration
DATA_DIR = Path("data")
OUTPUT_DIR = Path("converted_data")


@dataclass
class ConvertedSample:
    """Single converted sample in unified format."""
    task: str  # T1-T5
    sub_task: str  # e.g., T1-1, T1-2, etc.
    context: str
    delta_t: str  # Time delta
    event: str
    query: str
    answer: str
    state: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    original_id: Optional[str] = None


class BaseConverter:
    """Base class for all dataset converters."""
    
    def __init__(self, dataset_name: str, task: str, sub_task: str):
        self.dataset_name = dataset_name
        self.task = task
        self.sub_task = sub_task
        self.samples: List[ConvertedSample] = []
    
    def convert(self, input_path: Path) -> List[ConvertedSample]:
        """Main conversion method to be overridden by subclasses."""
        raise NotImplementedError
    
    def save(self, output_path: Path):
        """Save converted samples to JSONL format."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
        print(f"Saved {len(self.samples)} samples to {output_path}")


# ============================================================================
# T1: Temporal Calculation Converters
# ============================================================================

class TimeQAConverter(BaseConverter):
    """Converter for TimeQA dataset -> T1 Temporal Calculation."""
    
    def __init__(self):
        super().__init__("TimeQA", "T1", "T1-1")
    
    def convert(self, input_path: Path) -> List[ConvertedSample]:
        """Convert TimeQA to unified format.
        
        Original format:
        {
            "idx": "...",
            "question": "What was X from Y to Z?",
            "context": "..."
        }
        
        Target format:
        - Context: The passage context
        - Delta t: Time period mentioned in question
        - Event: Position held during that time
        - Query: Original question
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                
                # Extract time period from question
                question = data.get('question', '')
                time_match = re.search(r'from\s+([^to]+)\s+to\s+(\d{4})', question)
                
                if time_match:
                    start_time = time_match.group(1).strip()
                    end_time = time_match.group(2).strip()
                    delta_t = f"从 {start_time} 到 {end_time}"
                else:
                    # Try other patterns
                    delta_t = "时间范围未知"
                
                # Create converted sample
                sample = ConvertedSample(
                    task="T1",
                    sub_task="T1-1",  # Duration
                    context=data.get('context', ''),
                    delta_t=delta_t,
                    event="担任职位",  # Position held
                    query=question,
                    answer="",  # To be filled by model
                    state={"type": "temporal_position"},
                    original_id=data.get('idx')
                )
                self.samples.append(sample)
        
        return self.samples


class DROPConverter(BaseConverter):
    """Converter for DROP dataset -> T1 Temporal Calculation."""
    
    def __init__(self):
        super().__init__("DROP", "T1", "T1-2")
    
    def convert(self, input_path: Path) -> List[ConvertedSample]:
        """Convert DROP to unified format.
        
        DROP contains numerical operations including temporal calculations.
        """
        df = pd.read_parquet(input_path)
        
        for _, row in df.iterrows():
            # Extract context and question
            passage = row.get('passage', '')
            question = row.get('question', '')
            
            # Determine if it's a temporal question
            if any(kw in question.lower() for kw in ['when', 'how many', 'how much', 'year', 'day', 'time']):
                sample = ConvertedSample(
                    task="T1",
                    sub_task="T1-2",  # Temporal offset/ordering
                    context=passage,
                    delta_t="计算中",
                    event="数值推理",
                    query=question,
                    answer="",
                    state={"type": "numerical_temporal"},
                    original_id=str(row.get('idx', ''))
                )
                self.samples.append(sample)
        
        return self.samples


# ============================================================================
# T2: State Tracking Converters
# ============================================================================

class ProParaConverter(BaseConverter):
    """Converter for ProPara dataset -> T2 State Tracking."""
    
    def __init__(self):
        super().__init__("ProPara", "T2", "T2-1")
    
    def convert(self, input_path: Path) -> List[ConvertedSample]:
        """Convert ProPara to unified format.
        
        Original format (TSV):
        paragraph_id  SID  PARTICIPANTS  entity1  entity2  ...
        state1  -  -  -
        event1  Description
        state2  x  -  -
        
        Target format:
        - Context: Process description
        - Delta t: Sequential steps
        - Event: State change event
        - Query: Where is entity now?
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            current_para = None
            entities = []
            states = []
            events = []
            
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 3:
                    continue
                
                sid = parts[1] if len(parts) > 1 else ''
                
                if sid == 'SID':
                    # New paragraph
                    if current_para:
                        self._process_paragraph(current_para, entities, states, events)
                    current_para = parts[2] if len(parts) > 2 else ''
                    entities = parts[3:] if len(parts) > 3 else []
                    states = []
                    events = []
                elif sid.startswith('state'):
                    states.append(parts[2:] if len(parts) > 2 else [])
                elif sid.startswith('event'):
                    events.append(parts[2] if len(parts) > 2 else '')
            
            # Process last paragraph
            if current_para:
                self._process_paragraph(current_para, entities, states, events)
        
        return self.samples
    
    def _process_paragraph(self, prompt: str, entities: List[str], states: List[List[str]], events: List[str]):
        """Process a single paragraph into samples."""
        # Build context from events
        context = f"过程: {prompt}\n\n"
        for i, event in enumerate(events[:5]):  # Limit to first 5 steps
            context += f"步骤{i+1}: {event}\n"
        
        # Create sample for each step
        for i in range(len(states) - 1):
            delta_t = f"步骤 {i+1} 到 {i+2}"
            event_desc = events[i] if i < len(events) else "状态变化"
            
            # Build state info
            current_state = {}
            for j, entity in enumerate(entities):
                if j < len(states[i]):
                    current_state[entity] = states[i][j]
            
            sample = ConvertedSample(
                task="T2",
                sub_task="T2-1",
                context=context,
                delta_t=delta_t,
                event=event_desc,
                query=f"在 {delta_t} 后，实体状态是什么？",
                answer="",
                state=current_state,
                reasoning=f"从状态 {states[i]} 变化到 {states[i+1]}" if i < len(states) - 1 else None,
                original_id=prompt[:50]
            )
            self.samples.append(sample)


class BaBiConverter(BaseConverter):
    """Converter for bAbI dataset -> T2 State Tracking."""
    
    def __init__(self):
        super().__init__("bAbI", "T2", "T2-2")
    
    def convert(self, input_path: Path) -> List[ConvertedSample]:
        """Convert bAbI tasks to unified format.
        
        bAbI contains various reasoning tasks including:
        - Task 1-3: Location tracking (WhereIsActor, WhereIsObject)
        - Task 14: Time reasoning
        """
        # bAbI uses Lua generation - look for task files
        # This is a simplified converter
        
        # Try to find task files
        babi_tasks_dir = DATA_DIR / "bAbI" / "lua" / "babi" / "tasks"
        
        if not babi_tasks_dir.exists():
            print(f"bAbI tasks directory not found: {babi_tasks_dir}")
            return self.samples
        
        # Check for relevant tasks
        task_files = list(babi_tasks_dir.glob("WhereIs*.lua"))
        
        for task_file in task_files:
            task_name = task_file.stem
            print(f"Found bAbI task: {task_name}")
            
            # For now, create placeholder samples
            # In practice, would run Lua generator
            sample = ConvertedSample(
                task="T2",
                sub_task="T2-2",
                context="Mary went to the kitchen. John went to the garden.",
                delta_t="步骤1",
                event="Mary moves to kitchen",
                query="Mary在哪里?",
                answer="kitchen",
                state={"Mary": {"location": "kitchen"}},
                original_id=task_name
            )
            self.samples.append(sample)
        
        return self.samples


# ============================================================================
# T3: Concurrency/Conflict Converters
# ============================================================================

class CosmosQAConverter(BaseConverter):
    """Converter for CosmosQA dataset -> T3 Concurrency Detection."""
    
    def __init__(self):
        super().__init__("CosmosQA", "T3", "T3-1")
    
    def convert(self, input_path: Path) -> List[ConvertedSample]:
        """Convert CosmosQA to unified format.
        
        Original format (CSV):
        id, context, question, answer0, answer1, answer2, answer3, label
        
        Target format for T3:
        - Detect potential conflicts in the context
        """
        df = pd.read_csv(input_path)
        
        for _, row in df.iterrows():
            context = row.get('context', '')
            question = row.get('question', '')
            
            # Get all answers and correct one
            answers = [row.get(f'answer{i}', '') for i in range(4)]
            label = row.get('label', 0)
            
            # Convert to conflict detection format
            sample = ConvertedSample(
                task="T3",
                sub_task="T3-1",  # Spatial conflict
                context=context,
                delta_t="同一时间点",
                event="分析情境",
                query=question,
                answer=answers[label] if label < len(answers) else "",
                state={"type": "commonsense_reasoning"},
                original_id=row.get('id')
            )
            self.samples.append(sample)
        
        return self.samples


class ATOMICConverter(BaseConverter):
    """Converter for ATOMIC dataset -> T3 Concurrency/Commonsense."""
    
    def __init__(self):
        super().__init__("ATOMIC", "T3", "T3-2")
    
    def convert(self, input_path: Path) -> List[ConvertedSample]:
        """Convert ATOMIC to unified format.
        
        ATOMIC contains if-then commonsense knowledge:
        Event -> xEffect, xWant, xReact, etc.
        
        For T3, we use it to detect conflicts in events.
        
        CSV columns:
        - event: The initial event
        - oEffect, oReact, oWant, xAttr, xEffect, xIntent, xNeed, xReact, xWant: Relations
        - prefix: Template prefix
        - split: Dataset split
        """
        csv_file = input_path / "v4_atomic_trn.csv"
        
        if not csv_file.exists():
            # Try alternative paths
            csv_file = Path("data/ATOMIC/v4_atomic_trn.csv")
            if not csv_file.exists():
                print(f"ATOMIC CSV file not found")
                return self.samples
        
        print(f"Loading ATOMIC from {csv_file}...")
        df = pd.read_csv(csv_file)
        
        print(f"Processing {len(df)} ATOMIC events...")
        
        for idx, row in df.iterrows():
            event = row.get('event', '')
            
            # Extract effects/reactions
            o_effects = row.get('oEffect', '[]')
            o_reacts = row.get('oReact', '[]')
            x_effects = row.get('xEffect', '[]')
            x_intents = row.get('xIntent', '[]')
            x_wants = row.get('xWant', '[]')
            
            # Parse lists
            try:
                o_effects_list = eval(o_effects) if isinstance(o_effects, str) else o_effects
                o_reacts_list = eval(o_reacts) if isinstance(o_reacts, str) else o_reacts
            except:
                o_effects_list = []
                o_reacts_list = []
            
            # Create samples for different relation types
            # For T3: Create conflict detection scenarios
            
            # xEffect - what happens after event
            if x_effects and x_effects != '[]':
                try:
                    effects = eval(x_effects) if isinstance(x_effects, str) else x_effects
                    if effects and len(effects) > 0:
                        sample = ConvertedSample(
                            task="T3",
                            sub_task="T3-2",  # Resource/Effect reasoning
                            context=f"事件: {event}",
                            delta_t="事件后",
                            event=event,
                            query="事件的结果是什么?",
                            answer=str(effects[0]) if effects else "",
                            state={"type": "causal_effect", "relation": "xEffect"},
                            original_id=f"atomic_{idx}"
                        )
                        self.samples.append(sample)
                except:
                    pass
            
            # oReact - other's reaction
            if o_reacts_list and len(o_reacts_list) > 0:
                sample = ConvertedSample(
                    task="T3",
                    sub_task="T3-1",  # Spatial/Reaction conflict
                    context=f"事件: {event}",
                    delta_t="事件后",
                    event=event,
                    query="其他人对这个事件的反应是什么?",
                    answer=o_reacts_list[0] if o_reacts_list else "",
                    state={"type": "commonsense_reaction", "relation": "oReact"},
                    original_id=f"atomic_react_{idx}"
                )
                self.samples.append(sample)
            
            # Limit to prevent memory issues
            if len(self.samples) >= 10000:
                break
        
        print(f"Converted {len(self.samples)} ATOMIC samples")
        return self.samples


# ============================================================================
# T4: Long-Horizon Memory Converters
# ============================================================================

class NarrativeQAConverter(BaseConverter):
    """Converter for NarrativeQA dataset -> T4 Long-Horizon Memory."""
    
    def __init__(self):
        super().__init__("NarrativeQA", "T4", "T4-1")
    
    def convert(self, input_path: Path) -> List[ConvertedSample]:
        """Convert NarrativeQA to unified format.
        
        NarrativeQA contains long narratives with questions.
        Designed for testing memory over long contexts.
        
        Input format (parquet):
        - documents: chunk_id, chunk (story text)
        - queries: og_query, query, chunk_id, answer
        """
        # Read documents and queries
        docs_path = input_path / "documents"
        queries_path = input_path / "queries"
        
        # Load train split
        docs_df = pd.read_parquet(docs_path / "train-00000-of-00001.parquet")
        queries_df = pd.read_parquet(queries_path / "train-00000-of-00001.parquet")
        
        # Create document lookup
        doc_lookup = dict(zip(docs_df['chunk_id'], docs_df['chunk']))
        
        print(f"Processing {len(queries_df)} queries from NarrativeQA...")
        
        for idx, row in queries_df.iterrows():
            chunk_id = row.get('chunk_id', '')
            query_text = row.get('query', '')
            answer_text = row.get('answer', '')
            
            # Get full story context by finding all chunks with same story ID
            story_id = chunk_id.rsplit('_', 1)[0] if '_' in chunk_id else chunk_id
            
            # Find all chunks for this story
            story_chunks = []
            for cid, text in doc_lookup.items():
                if cid.startswith(story_id):
                    story_chunks.append((int(cid.split('_')[-1]) if '_' in cid else 0, text))
            
            # Sort by chunk order
            story_chunks.sort(key=lambda x: x[0])
            full_context = " ".join([c[1] for c in story_chunks])
            
            # Limit context length for processing
            context = full_context[:5000] if full_context else ""
            
            sample = ConvertedSample(
                task="T4",
                sub_task="T4-1",
                context=context,
                delta_t="长时间跨度",
                event="长期记忆",
                query=query_text,
                answer=answer_text,
                state={"type": "long_context", "length": len(full_context), "chunks": len(story_chunks)},
                original_id=chunk_id
            )
            self.samples.append(sample)
            
            # Limit for now
            if len(self.samples) >= 5000:
                break
        
        return self.samples


# ============================================================================
# T5: Counterfactual/Sandbox Converters
# ============================================================================

class WinograndeConverter(BaseConverter):
    """Converter for Winogrande dataset -> T5 Counterfactual."""
    
    def __init__(self):
        super().__init__("Winogrande", "T5", "T5-1")
    
    def convert(self, input_path: Path) -> List[ConvertedSample]:
        """Convert Winogrande to unified format.
        
        Original format:
        sentence, option1, option2, answer
        
        Target format for T5:
        - Test model's ability to reason with different rules
        - Create "sandbox" versions with modified rules
        """
        df = pd.read_parquet(input_path)
        
        for idx, row in df.iterrows():
            sentence = row.get('sentence', '')
            option1 = row.get('option1', '')
            option2 = row.get('option2', '')
            answer = row.get('answer', 0)
            
            # Original format: fill in the blank
            # Convert to counterfactual by changing the scenario
            
            # Create original version
            sample = ConvertedSample(
                task="T5",
                sub_task="T5-1",
                context=sentence.replace('_', '[BLANK]'),
                delta_t="当前情境",
                event="推理",
                query="谁[BLANK]?",
                answer=option1 if answer == 1 else option2,
                state={"type": "winograd"},
                original_id=f"winogrande_{idx}"
            )
            self.samples.append(sample)
            
            # Create counterfactual version (rule changed)
            cf_sentence = sentence.replace('because', 'despite').replace('.', ' (contrary to expectation).')
            cf_sample = ConvertedSample(
                task="T5",
                sub_task="T5-2",  # Counterfactual
                context=cf_sentence.replace('_', '[BLANK]'),
                delta_t="反事实情境",
                event="反事实推理",
                query="谁[BLANK]?",
                answer=option2 if answer == 1 else option1,  # Flipped
                state={"type": "counterfactual", "modified": True},
                original_id=f"winogrande_cf_{idx}"
            )
            self.samples.append(cf_sample)
        
        return self.samples


class HellaSwagConverter(BaseConverter):
    """Converter for HellaSwag dataset -> T5 Counterfactual."""
    
    def __init__(self):
        super().__init__("HellaSwag", "T5", "T5-3")
    
    def convert(self, input_path: Path) -> List[ConvertedSample]:
        """Convert HellaSwag to unified format.
        
        HellaSwag is multiple choice about activity endings.
        Good for testing physical commonsense.
        """
        # Find HellaSwag data
        hs_files = list((DATA_DIR / "HellaSwag").glob("**/*.jsonl"))
        
        for json_file in hs_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        data = json.loads(line.strip())
                        
                        ctx = data.get('ctx', '')
                        question = data.get('question', '')
                        endings = data.get('endings', [])
                        label = data.get('label', 0)
                        
                        # Create sample
                        sample = ConvertedSample(
                            task="T5",
                            sub_task="T5-3",
                            context=ctx + " [MASK]",
                            delta_t="情境推断",
                            event="物理推理",
                            query="接下来会发生什么?",
                            answer=endings[label] if label < len(endings) else "",
                            state={"type": "physical_commonsense"},
                            original_id=data.get('ind')
                        )
                        self.samples.append(sample)
            except Exception as e:
                print(f"Error processing {json_file}: {e}")
        
        return self.samples


# ============================================================================
# Main Conversion Pipeline
# ============================================================================

def get_converters() -> Dict[str, BaseConverter]:
    """Get all available converters."""
    return {
        'timeqa_easy': TimeQAConverter(),
        'timeqa_hard': TimeQAConverter(),
        'drop': DROPConverter(),
        'propara': ProParaConverter(),
        'babi': BaBiConverter(),
        'cosmosqa': CosmosQAConverter(),
        'atomic': ATOMICConverter(),
        'narrativeqa': NarrativeQAConverter(),
        'winogrande': WinograndeConverter(),
        'hellaswag': HellaSwagConverter(),
    }


def run_conversion():
    """Run all conversions."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    converters = get_converters()
    results = {}
    
    # TimeQA conversion
    timeqa_files = {
        'timeqa_easy': DATA_DIR / 'TimeQA' / 'dataset' / 'dev.easy.json',
        'timeqa_hard': DATA_DIR / 'TimeQA' / 'dataset' / 'dev.hard.json',
    }
    
    for name, path in timeqa_files.items():
        if path.exists():
            print(f"\nConverting {name}...")
            converter = converters.get(name.split('_')[0], TimeQAConverter())
            converter.convert(path)
            output_path = OUTPUT_DIR / f"{name}.jsonl"
            converter.save(output_path)
            results[name] = len(converter.samples)
    
    # DROP conversion
    drop_file = DATA_DIR / 'DROP' / 'train-00000-of-00001.parquet'
    if drop_file.exists():
        print(f"\nConverting DROP...")
        converter = converters['drop']
        converter.convert(drop_file)
        output_path = OUTPUT_DIR / "drop.jsonl"
        converter.save(output_path)
        results['drop'] = len(converter.samples)
    
    # ProPara conversion
    propara_file = DATA_DIR / 'ProPara' / 'data' / 'emnlp18' / 'grids.v1.train.tsv'
    if propara_file.exists():
        print(f"\nConverting ProPara...")
        converter = converters['propara']
        converter.convert(propara_file)
        output_path = OUTPUT_DIR / "propara.jsonl"
        converter.save(output_path)
        results['propara'] = len(converter.samples)
    
    # CosmosQA conversion
    cosmosqa_file = DATA_DIR / 'CosmosQA' / 'data' / 'train.csv'
    if cosmosqa_file.exists():
        print(f"\nConverting CosmosQA...")
        converter = converters['cosmosqa']
        converter.convert(cosmosqa_file)
        output_path = OUTPUT_DIR / "cosmosqa.jsonl"
        converter.save(output_path)
        results['cosmosqa'] = len(converter.samples)
    
    # Winogrande conversion
    winogrande_file = DATA_DIR / 'winogrande' / 'winogrande_xs' / 'train-00000-of-00001.parquet'
    if winogrande_file.exists():
        print(f"\nConverting Winogrande...")
        converter = converters['winogrande']
        converter.convert(winogrande_file)
        output_path = OUTPUT_DIR / "winogrande.jsonl"
        converter.save(output_path)
        results['winogrande'] = len(converter.samples)
    
    # HellaSwag conversion
    hellaswag_dir = DATA_DIR / 'HellaSwag'
    hellaswag_files = list(hellaswag_dir.glob("**/*.jsonl"))[:1]
    for hs_file in hellaswag_files:
        print(f"\nConverting HellaSwag...")
        converter = converters['hellaswag']
        converter.convert(hs_file)
        output_path = OUTPUT_DIR / "hellaswag.jsonl"
        converter.save(output_path)
        results['hellaswag'] = len(converter.samples)

    # NarrativeQA conversion (illuin-conteb/narrative-qa)
    narrative_qa_dir = DATA_DIR / 'narrative-qa'
    if narrative_qa_dir.exists() and (narrative_qa_dir / "documents").exists():
        print(f"\nConverting NarrativeQA...")
        converter = converters['narrativeqa']
        converter.convert(narrative_qa_dir)
        output_path = OUTPUT_DIR / "narrativeqa.jsonl"
        converter.save(output_path)
        results['narrativeqa'] = len(converter.samples)
    
    # Summary
    print("\n" + "="*60)
    print("CONVERSION SUMMARY")
    print("="*60)
    for name, count in results.items():
        print(f"  {name}: {count} samples")
    print("="*60)
    print(f"Total: {sum(results.values())} samples")
    print(f"Output directory: {OUTPUT_DIR}")
    
    return results


if __name__ == "__main__":
    run_conversion()
