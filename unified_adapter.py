#!/usr/bin/env python3
"""
Unified Data Adapter - 合并版本的转换入口
================================================================================

功能：
- 统一的TemporalSample数据格式
- 所有数据集转换器集中入口
- 验证与统计

Author: TimeAware Benchmark Team
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# Parent directory imports
sys.path.insert(0, str(Path(__file__).parent))

# Try to import from existing modules
try:
    from arch.task_schema import TemporalSample, TaskType
    USE_ARCH_SCHEMA = True
except ImportError:
    USE_ARCH_SCHEMA = False
    # Define locally if arch schema not available
    @dataclass
    class TemporalSample:
        id: str
        task_type: 'TaskType' = None
        context: str = ""
        query: str = ""
        answer: str = ""
        ground_truth: Dict = None
        metadata: Dict = None
        
        def to_dict(self):
            return asdict(self)
        
        def to_jsonl(self):
            return json.dumps(self.to_dict(), ensure_ascii=False)


# Import converters
try:
    from unified_data_converter import (
        OpenPI2Converter,
        PASTAConverter,
        AtomicConflictConstructor,
        CounterfactualRulePerturbation,
        ProParaAnswerFixer,
        LongBenchConverter,
        DialogueTemporalBenchmark
    )
    HAS_UNIFIED_CONVERTER = True
except ImportError:
    HAS_UNIFIED_CONVERTER = False

try:
    from supplement_converters import (
        TRIPConverter,
        SituatedGenConverter,
        GroundTruthValidator
    )
    HAS_SUPPLEMENT_CONVERTER = True
except ImportError:
    HAS_SUPPLEMENT_CONVERTER = False


class UnifiedDataAdapter:
    """Unified adapter for all temporal reasoning datasets
    
    This class provides a single entry point for:
    1. Converting all datasets from /data to /converted_data
    2. Running validation on all converted data
    3. Generating statistics and reports
    """
    
    def __init__(self, data_dir: str = "data", output_dir: str = "converted_data"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.samples: Dict[str, List] = {}
        self.stats: Dict = {}
    
    def convert_all(self, skip_existing: bool = True) -> Dict:
        """Convert all available datasets
        
        Args:
            skip_existing: Skip conversion if output file exists
            
        Returns:
            Dictionary of conversion results
        """
        results = {}
        
        # T1: Temporal Calculation - TimeQA, DROP, MCTACO
        results['t1_temporal'] = self._convert_t1_datasets()
        
        # T2: State Tracking - OpenPI2.0, PASTA, ProPara
        results['t2_state'] = self._convert_t2_datasets()
        
        # T3: Concurrency/Conflict - ATOMIC reconstruction
        results['t3_concurrency'] = self._convert_t3_datasets()
        
        # T4: Long-term Memory - LongBench, NarrativeQA
        results['t4_memory'] = self._convert_t4_datasets()
        
        # T5: Counterfactual - Rule perturbation, PASTA counterfactual
        results['t5_counterfactual'] = self._convert_t5_datasets()
        
        return results
    
    def _convert_t1_datasets(self) -> Dict:
        """Convert T1 temporal calculation datasets"""
        print("[T1] Converting temporal calculation datasets...")
        results = {}
        
        # TimeQA, DROP, MCTACO already converted via convert_data.py
        # Check if files exist
        for dataset in ['timeqa_dev', 'timeqa_train', 'drop', 'mctaco']:
            file_path = self.output_dir / f"{dataset}.jsonl"
            if file_path.exists():
                count = len(list(file_path.open('r')))
                results[dataset] = {"status": "exists", "count": count}
            else:
                results[dataset] = {"status": "missing", "count": 0}
        
        return results
    
    def _convert_t2_datasets(self) -> Dict:
        """Convert T2 state tracking datasets"""
        print("[T2] Converting state tracking datasets...")
        results = {}
        
        if HAS_UNIFIED_CONVERTER:
            # OpenPI2.0
            openpi_file = self.data_dir / "OpenPI2.0" / "data" / "dev-data-reformatted-v4.json"
            if openpi_file.exists():
                output_path = self.output_dir / "openpi2_t2.jsonl"
                if not output_path.exists():
                    converter = OpenPI2Converter()
                    converter.convert(openpi_file)
                    converter.save(output_path)
                    results['openpi2'] = {"status": "converted", "count": len(converter.samples)}
                else:
                    results['openpi2'] = {"status": "exists", "count": len(list(output_path.open('r')))}
            
            # PASTA
            pasta_file = self.data_dir / "pasta" / "data" / "tr_data.jsonl"
            if pasta_file.exists():
                output_path = self.output_dir / "pasta_t2_t5.jsonl"
                if not output_path.exists():
                    converter = PASTAConverter()
                    converter.convert(pasta_file)
                    converter.save(output_path)
                    results['pasta'] = {"status": "converted", "count": len(converter.samples)}
                else:
                    results['pasta'] = {"status": "exists", "count": len(list(output_path.open('r')))}
            
            # ProPara fix
            propara_file = self.output_dir / "propara.jsonl"
            if propara_file.exists():
                output_path = self.output_dir / "propara_fixed_v2.jsonl"
                if not output_path.exists():
                    fixer = ProParaAnswerFixer()
                    fixer.convert(propara_file)
                    fixer.save(output_path)
                    results['propara_fixed'] = {"status": "converted", "count": len(fixer.samples)}
                else:
                    results['propara_fixed'] = {"status": "exists", "count": len(list(output_path.open('r')))}
        
        return results
    
    def _convert_t3_datasets(self) -> Dict:
        """Convert T3 concurrency/conflict datasets"""
        print("[T3] Converting concurrency/conflict datasets...")
        results = {}
        
        if HAS_UNIFIED_CONVERTER:
            output_path = self.output_dir / "t3_conflict_detection.jsonl"
            if not output_path.exists():
                atomic_file = self.data_dir / "ATOMIC" / "v4_atomic_all_agg.csv"
                constructor = AtomicConflictConstructor()
                constructor.construct_from_atomic(atomic_file)
                constructor.save(output_path)
                results['t3_conflict'] = {"status": "converted", "count": len(constructor.samples)}
            else:
                results['t3_conflict'] = {"status": "exists", "count": len(list(output_path.open('r')))}
        
        if HAS_SUPPLEMENT_CONVERTER:
            output_path = self.output_dir / "trip_conflict_t3.jsonl"
            if not output_path.exists():
                trip_file = self.data_dir / "TRIP" / "postprocess" / "sample_evaluation_format.jsonl"
                converter = TRIPConverter()
                if trip_file.exists():
                    converter.convert_from_sample_file(trip_file)
                else:
                    converter.samples = converter._generate_conflict_samples(500)
                converter.save(output_path)
                results['trip'] = {"status": "converted", "count": len(converter.samples)}
            else:
                results['trip'] = {"status": "exists", "count": len(list(output_path.open('r')))}
        
        return results
    
    def _convert_t4_datasets(self) -> Dict:
        """Convert T4 long-term memory datasets"""
        print("[T4] Converting long-term memory datasets...")
        results = {}
        
        if HAS_UNIFIED_CONVERTER:
            qasper_file = self.data_dir / "LongBench" / "data" / "qasper.jsonl"
            if qasper_file.exists():
                output_path = self.output_dir / "longbench_qasper_t4.jsonl"
                if not output_path.exists():
                    converter = LongBenchConverter()
                    converter.convert_qasper(qasper_file)
                    converter.save(output_path)
                    results['qasper'] = {"status": "converted", "count": len(converter.samples)}
                else:
                    results['qasper'] = {"status": "exists", "count": len(list(output_path.open('r')))}
        
        # NarrativeQA already converted
        narrative_path = self.output_dir / "narrativeqa.jsonl"
        if narrative_path.exists():
            results['narrativeqa'] = {"status": "exists", "count": len(list(narrative_path.open('r')))}
        
        return results
    
    def _convert_t5_datasets(self) -> Dict:
        """Convert T5 counterfactual datasets"""
        print("[T5] Converting counterfactual datasets...")
        results = {}
        
        if HAS_UNIFIED_CONVERTER:
            # Counterfactual rule perturbation
            output_path = self.output_dir / "t5_counterfactual.jsonl"
            if not output_path.exists():
                generator = CounterfactualRulePerturbation()
                generator.generate_samples()
                generator.save(output_path)
                results['counterfactual'] = {"status": "generated", "count": len(generator.samples)}
            else:
                results['counterfactual'] = {"status": "exists", "count": len(list(output_path.open('r')))}
            
            # Dialogue temporal benchmark
            dialogue_path = self.output_dir / "dialogue_temporal_benchmark.jsonl"
            if not dialogue_path.exists():
                dialogue_gen = DialogueTemporalBenchmark()
                dialogue_gen.generate_samples()
                dialogue_gen.save(dialogue_path)
                results['dialogue'] = {"status": "generated", "count": len(dialogue_gen.samples)}
            else:
                results['dialogue'] = {"status": "exists", "count": len(list(dialogue_path.open('r')))}
        
        # SituatedGen
        if HAS_SUPPLEMENT_CONVERTER:
            output_path = self.output_dir / "situated_gen_t2_t5.jsonl"
            if not output_path.exists():
                situated_file = self.data_dir / "situated_gen" / "data" / "train.jsonl"
                statements_file = self.data_dir / "situated_gen" / "data" / "preprocessed" / "statements" / "strategyqa.json"
                
                converter = SituatedGenConverter()
                if situated_file.exists():
                    converter.convert(situated_file)
                if statements_file.exists():
                    converter.convert_statements(statements_file)
                
                if converter.samples:
                    converter.save(output_path)
                    results['situated_gen'] = {"status": "converted", "count": len(converter.samples)}
            else:
                results['situated_gen'] = {"status": "exists", "count": len(list(output_path.open('r')))}
        
        return results
    
    def validate_all(self) -> Dict:
        """Run validation on all converted datasets"""
        print("\n[Validation] Running ground truth validation...")
        
        if HAS_SUPPLEMENT_CONVERTER:
            validator = GroundTruthValidator()
            results = validator.validate_all(self.output_dir)
            validator.save_report(self.output_dir / "validation_report.json")
            return results
        else:
            print("[Validation] Ground Truth Validator not available")
            return {}
    
    def generate_summary(self) -> Dict:
        """Generate summary statistics for all datasets"""
        summary = {
            "total_files": 0,
            "total_samples": 0,
            "by_task": {},
            "by_dataset": {}
        }
        
        for file_path in self.output_dir.glob("*.jsonl"):
            file_path.name.startswith(".")
            continue
            
            summary["total_files"] += 1
            
            # Count samples
            with open(file_path, 'r', encoding='utf-8') as f:
                count = sum(1 for _ in f)
            
            summary["by_dataset"][file_path.stem] = count
            summary["total_samples"] += count
            
            # Determine task type from filename
            if 't1' in file_path.stem or 'timeqa' in file_path.stem or 'mctaco' in file_path.stem or 'drop' in file_path.stem:
                summary["by_task"].setdefault("T1_temporal", 0)
                summary["by_task"]["T1_temporal"] += count
            elif 't2' in file_path.stem or 'openpi' in file_path.stem or 'pasta' in file_path.stem or 'propara' in file_path.stem or 'propara' in file_path.stem:
                summary["by_task"].setdefault("T2_state", 0)
                summary["by_task"]["T2_state"] += count
            elif 't3' in file_path.stem or 'trip' in file_path.stem or 'conflict' in file_path.stem:
                summary["by_task"].setdefault("T3_concurrency", 0)
                summary["by_task"]["T3_concurrency"] += count
            elif 't4' in file_path.stem or 'longbench' in file_path.stem or 'narrative' in file_path.stem or 'qasper' in file_path.stem:
                summary["by_task"].setdefault("T4_memory", 0)
                summary["by_task"]["T4_memory"] += count
            elif 't5' in file_path.stem or 'counterfactual' in file_path.stem or 'dialogue' in file_path.stem:
                summary["by_task"].setdefault("T5_counterfactual", 0)
                summary["by_task"]["T5_counterfactual"] += count
        
        return summary
    
    def save_summary(self):
        """Save summary to JSON file"""
        summary = self.generate_summary()
        output_file = self.output_dir / "dataset_summary.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print("DATASET SUMMARY")
        print(f"{'='*60}")
        print(f"Total files: {summary['total_files']}")
        print(f"Total samples: {summary['total_samples']}")
        print(f"\nBy Task:")
        for task, count in summary['by_task'].items():
            print(f"  {task}: {count}")
        print(f"\nSaved to: {output_file}")
        
        return summary


def main():
    """Main entry point for unified data conversion"""
    print("=" * 60)
    print("UNIFIED DATA ADAPTER FOR TEMPORAL WORLD MODELING")
    print("=" * 60)
    
    adapter = UnifiedDataAdapter()
    
    # Run all conversions
    results = adapter.convert_all()
    
    # Validate
    validation = adapter.validate_all()
    
    # Generate summary
    summary = adapter.save_summary()
    
    print(f"\n{'='*60}")
    print("CONVERSION COMPLETE")
    print(f"{'='*60}")
    print(f"Total samples: {summary['total_samples']}")
    print(f"Output directory: {adapter.output_dir}")


if __name__ == "__main__":
    main()