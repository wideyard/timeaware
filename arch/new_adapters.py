"""新数据集适配器 - 包含 DROP, TimeQA, bAbI, ProPara, SocialIQA, CosmosQA, PIQA, LongBench

基于 data_.md 的改造方式：
- T1: Temporalization - 加时间维度
- T2: State Structuring - 提取状态
- T5: Rule Perturbation - 改规则
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from .task_schema import TemporalSample, TaskType


class DROPAdapter:
    """DROP 数据集适配器
    
    DROP: Discrete Reasoning Over Paragraphs
    来源: ACL 2019
    
    包含数字/时间计算，适合 T1 时间计算任务
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.samples: List[TemporalSample] = []
    
    def load(self, split: str = "train") -> List[TemporalSample]:
        """加载DROP数据集"""
        filepath = self.data_dir / "DROP" / f"{split}-00000-of-00001.parquet"
        
        import pandas as pd
        df = pd.read_parquet(filepath)
        
        samples = []
        for idx, row in df.iterrows():
            sample = self._convert_row(row, idx, split)
            if sample:
                samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_row(self, row, idx: int, split: str) -> Optional[TemporalSample]:
        """转换一行数据"""
        passage = row.get("passage", "")
        question = row.get("question", "")
        answer_spans = row.get("answers_spans", {})
        
        spans = answer_spans.get("spans", []) if isinstance(answer_spans, dict) else []
        answer = spans[0] if len(spans) > 0 else ""
        
        if not question or not passage:
            return None
        
        return TemporalSample(
            id=f"drop_{split}_{idx}",
            task_type=TaskType.T1_TEMPORAL_CALCULATION,
            context=f"[文本]\n{passage}",
            query=question,
            answer=str(answer),
            ground_truth={"spans": spans, "types": answer_spans.get("types", []) if isinstance(answer_spans, dict) else []},
            metadata={"section_id": row.get("section_id", ""), "query_id": row.get("query_id", "")}
        )


class TimeQAAdapter:
    """TimeQA 数据集适配器
    
    本身包含时间推理的问答数据
    来源: EMNLP 2023
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir) / "TimeQA"
        self.samples: List[TemporalSample] = []
    
    def load(self, split: str = "train") -> List[TemporalSample]:
        """加载TimeQA数据集"""
        filepath = self.data_dir / "dataset" / f"annotated_{split}.json"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        samples = []
        for idx, item in enumerate(data):
            sample = self._convert_item(item, idx, split)
            if sample:
                samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_item(self, item: Dict, idx: int, split: str) -> Optional[TemporalSample]:
        """转换一项数据"""
        questions = item.get("questions", [])
        paras = item.get("paras", [])
        
        if not questions or not paras:
            return None
        
        main_q = questions[0]
        if not main_q or len(main_q) < 2:
            return None
        
        time_range = main_q[0]
        answer_info = main_q[1]
        
        time_str = " to ".join(time_range) if isinstance(time_range, list) else str(time_range)
        
        context_parts = []
        for p in paras[:5]:
            if isinstance(p, str):
                context_parts.append(p)
            elif isinstance(p, dict):
                context_parts.append(p.get("text", str(p)))
        
        context = "\n".join(context_parts)
        
        answer = ""
        if answer_info and isinstance(answer_info, list) and len(answer_info) > 0:
            for ans in answer_info:
                if isinstance(ans, dict):
                    answer = ans.get("answer", "")
                    if answer:
                        break
        
        return TemporalSample(
            id=f"timeqa_{split}_{idx}",
            task_type=TaskType.T1_TEMPORAL_CALCULATION,
            context=f"[时间范围] {time_str}\n\n[文本]\n{context}",
            query="根据文本回答问题" if not questions[0] else str(questions[0][0]) if len(questions[0]) > 0 else "回答问题",
            answer=answer,
            ground_truth={"time_range": time_range},
            metadata={"type": item.get("type", ""), "link": item.get("link", "")}
        )


class BABiAdapter:
    """bAbI 数据集适配器
    
    人物移动、物体位置等状态追踪
    来源: Facebook AI Research
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir) / "bAbI"
        self.samples: List[TemporalSample] = []
    
    def load(self, task: str = "tasks_1-20_v1-2") -> List[TemporalSample]:
        """加载bAbI数据集"""
        task_dir = self.data_dir / task
        
        samples = []
        idx = 0
        
        for split in ["train", "test", "valid"]:
            filepath = task_dir / f"qa{idx}_{split}.txt" if idx else None
            
            if not filepath or not filepath.exists():
                for f in task_dir.glob(f"*_{split}.txt"):
                    filepath = f
                    break
            
            if filepath and filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            story = parts[0]
                            qa = parts[1] if len(parts) > 1 else ""
                            
                            sample = self._convert_line(story, qa, idx, split)
                            if sample:
                                samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_line(self, story: str, qa: str, idx: int, split: str) -> Optional[TemporalSample]:
        """转换一行"""
        if not story:
            return None
        
        return TemporalSample(
            id=f"babi_{idx}_{split}",
            task_type=TaskType.T2_STATE_TRACKING,
            context=f"[故事]\n{story}",
            query=qa.split('?')[0] + '?' if '?' in qa else qa,
            answer=qa.split('\t')[-1] if '\t' in qa else "",
            ground_truth={},
            metadata={"source": "bAbI", "story": story}
        )


class ProParaAdapter:
    """ProPara 数据集适配器
    
    描述物理过程的状态变化
    来源: EMNLP 2018
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir) / "ProPara"
        self.samples: List[TemporalSample] = []
    
    def load(self, split: str = "train") -> List[TemporalSample]:
        """加载ProPara数据集"""
        filepath = self.data_dir / "data" / "emnlp18" / f"grids.v1.{split}.tsv"
        
        if not filepath.exists():
            filepath = self.data_dir / f"prolocal.naacl_cr.data_run1.model_run1.{split}.tsv"
        
        if not filepath.exists():
            return []
        
        samples = []
        current_doc = None
        current_entity = None
        steps = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 5:
                    doc_id = parts[0]
                    step_id = parts[1]
                    entity = parts[2]
                    action = parts[3]
                    location = parts[4] if len(parts) > 4 else ""
                    
                    if current_doc != doc_id:
                        if current_doc and steps:
                            sample = self._create_sample(current_doc, current_entity, steps)
                            if sample:
                                samples.append(sample)
                        current_doc = doc_id
                        current_entity = entity
                        steps = []
                    
                    steps.append({
                        "step": step_id,
                        "entity": entity,
                        "action": action,
                        "location": location
                    })
        
        if current_doc and steps:
            sample = self._create_sample(current_doc, current_entity, steps)
            if sample:
                samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _create_sample(self, doc_id: str, entity: str, steps: List[Dict]) -> Optional[TemporalSample]:
        """创建样本"""
        if not steps:
            return None
        
        context = "\n".join([f"Step {s['step']}: {s['action']} - {s['location']}" for s in steps])
        
        final_location = steps[-1].get("location", "") if steps else ""
        
        return TemporalSample(
            id=f"propara_{doc_id}_{entity}",
            task_type=TaskType.T2_STATE_TRACKING,
            context=f"[实体] {entity}\n\n[过程]\n{context}",
            query=f"{entity} 最终在哪里?",
            answer=final_location,
            ground_truth={"steps": steps},
            metadata={"entity": entity, "doc_id": doc_id}
        )


class SocialIQAAdapter:
    """SocialIQA 数据集适配器
    
    社会常识推理问答
    来源: ICLR 2020
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir) / "SocialIQA"
        self.samples: List[TemporalSample] = []
    
    def load(self, split: str = "train") -> List[TemporalSample]:
        """加载SocialIQA数据集"""
        filepath = self.data_dir / f"{split}.jsonl"
        
        samples = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                data = json.loads(line)
                sample = self._convert_item(data, idx, split)
                if sample:
                    samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_item(self, item: Dict, idx: int, split: str) -> Optional[TemporalSample]:
        """转换一项"""
        context = item.get("context", "")
        question = item.get("question", "")
        answer_a = item.get("answerA", "")
        answer_b = item.get("answerB", "")
        answer_c = item.get("answerC", "")
        
        if not context or not question:
            return None
        
        return TemporalSample(
            id=f"socialiqa_{split}_{idx}",
            task_type=TaskType.T3_CONCURRENCY,
            context=f"[情境]\n{context}",
            query=question,
            answer=f"A. {answer_a}\nB. {answer_b}\nC. {answer_c}",
            ground_truth={"options": {"A": answer_a, "B": answer_b, "C": answer_c}},
            metadata={"source": "SocialIQA"}
        )


class CosmosQAAdapter:
    """CosmosQA 数据集适配器
    
    常识推理问答
    来源: EMNLP 2019
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir) / "CosmosQA"
        self.samples: List[TemporalSample] = []
    
    def load(self, split: str = "train") -> List[TemporalSample]:
        """加载CosmosQA数据集
        
        Args:
            split: "train", "valid" (test split doesn't exist, use "valid")
        """
        samples = []
        # Try CSV format first
        filepath = self.data_dir / "data" / f"{split}.csv"
        
        if not filepath.exists():
            filepath = self.data_dir / "data" / f"{split}.jsonl"
        
        if not filepath.exists():
            return samples
        
        import csv
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                sample = self._convert_item(row, idx, split)
                if sample:
                    samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_item(self, item: Dict, idx: int, split: str) -> Optional[TemporalSample]:
        """转换一项"""
        context = item.get("context", "")
        question = item.get("question", "")
        answers = [item.get(f"answer{i}", "") for i in range(4)]
        
        if not context or not question:
            return None
        
        options_text = "\n".join([f"{chr(65+i)}. {a}" for i, a in enumerate(answers) if a])
        
        return TemporalSample(
            id=f"cosmosqa_{split}_{idx}",
            task_type=TaskType.T3_CONCURRENCY,
            context=f"[文本]\n{context}",
            query=question,
            answer=options_text,
            ground_truth={"answers": answers, "label": item.get("label", "")},
            metadata={"id": item.get("id", "")}
        )


class PIQAAdapter:
    """PIQA 数据集适配器
    
    物理常识推理问答
    来源: NeurIPS 2019
    
    适合 T5 反事实/虚构规则推理
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir) / "PIQA"
        self.samples: List[TemporalSample] = []
    
    def load(self, split: str = "test") -> List[TemporalSample]:
        """加载PIQA数据集
        
        split 可以是 "test" (tests.jsonl) 或 "train"/"dev" (physicaliqa-train-dev目录)
        """
        if split == "test":
            filepath = self.data_dir / "tests.jsonl"
        else:
            filepath = self.data_dir / "physicaliqa-train-dev" / f"{split}.json"
        
        if not filepath.exists():
            return []
        
        samples = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                data = json.loads(line)
                sample = self._convert_item(data, idx, split)
                if sample:
                    samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_item(self, item: Dict, idx: int, split: str) -> Optional[TemporalSample]:
        """转换一项"""
        goal = item.get("goal", "")
        sol1 = item.get("sol1", "")
        sol2 = item.get("sol2", "")
        
        if not goal:
            return None
        
        return TemporalSample(
            id=f"piqa_{split}_{idx}",
            task_type=TaskType.T5_COUNTERFACTUAL,
            context=f"[问题]\n{goal}",
            query="哪个解决方案更合理?",
            answer=f"A. {sol1}\nB. {sol2}",
            ground_truth={"sol1": sol1, "sol2": sol2},
            metadata={"source": "PIQA"}
        )


class LongBenchAdapter:
    """LongBench 数据集适配器
    
    长文本理解基准
    来源: NeurIPS 2023
    
    适合 T4 长期记忆任务
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir) / "LongBench"
        self.samples: List[TemporalSample] = []
    
    def load(self, subset: str = None) -> List[TemporalSample]:
        """加载LongBench数据集
        
        Args:
            subset: 可选，指定子集名称如 "narrativeqa", "qasper" 等。
                   如果为 None，则加载所有本地子集。
        """
        local_data_dir = self.data_dir / "data"
        if not local_data_dir.exists():
            return self._load_from_huggingface()
        
        samples = []
        jsonl_files = list(local_data_dir.glob("*.jsonl"))
        
        for jsonl_file in jsonl_files:
            dataset_name = jsonl_file.stem
            if subset and dataset_name != subset:
                continue
            
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for idx, line in enumerate(f):
                    try:
                        item = json.loads(line)
                        sample = self._convert_item(item, idx)
                        if sample:
                            samples.append(sample)
                    except json.JSONDecodeError:
                        continue
        
        self.samples = samples
        return samples
    
    def _load_from_huggingface(self) -> List[TemporalSample]:
        """从 Hugging Face 加载"""
        try:
            from datasets import load_dataset
            
            dataset = load_dataset("THUDM/LongBench", split="test")
            
            samples = []
            for idx, item in enumerate(dataset):
                sample = self._convert_item(item, idx)
                if sample:
                    samples.append(sample)
            
            self.samples = samples
            return samples
        except ImportError:
            print("Warning: datasets library not available. LongBench requires manual download.")
            return []
        except Exception as e:
            print(f"Warning: Failed to load LongBench: {e}")
            return []
    
    def _convert_item(self, item: Dict, idx: int) -> Optional[TemporalSample]:
        """转换一项"""
        context = item.get("context", "")
        question = item.get("input", "") or item.get("question", "")
        answers = item.get("answers", [])
        dataset = item.get("dataset", "")
        
        if not context or not question:
            return None
        
        answer = answers[0] if isinstance(answers, list) and len(answers) > 0 else str(answers)
        
        return TemporalSample(
            id=f"longbench_{dataset}_{idx}",
            task_type=TaskType.T4_LONG_TERM_MEMORY,
            context=f"[文档]\n{context}",
            query=question,
            answer=str(answer),
            ground_truth={"answers": answers},
            metadata={"dataset": dataset, "length": len(context), "id": item.get("_id", "")}
        )


# 便捷函数
def load_drop_data(data_dir: str, split: str = "train") -> List[TemporalSample]:
    """加载DROP数据"""
    adapter = DROPAdapter(data_dir)
    return adapter.load(split)

def load_timeqa_data(data_dir: str, split: str = "train") -> List[TemporalSample]:
    """加载TimeQA数据"""
    adapter = TimeQAAdapter(data_dir)
    return adapter.load(split)

def load_socialiqa_data(data_dir: str, split: str = "train") -> List[TemporalSample]:
    """加载SocialIQA数据"""
    adapter = SocialIQAAdapter(data_dir)
    return adapter.load(split)

def load_cosmosqa_data(data_dir: str, split: str = "train") -> List[TemporalSample]:
    """加载CosmosQA数据"""
    adapter = CosmosQAAdapter(data_dir)
    return adapter.load(split)

def load_piqa_data(data_dir: str, split: str = "test") -> List[TemporalSample]:
    """加载PIQA数据"""
    adapter = PIQAAdapter(data_dir)
    return adapter.load(split)


class ATOMICAdapter:
    """ATOMIC 数据集适配器
    
    常识推理知识图谱，包含 if-then 关系
    来源: AAAI 2021
    
    适合 T5 反事实/规则推理
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir) / "ATOMIC"
        self.samples: List[TemporalSample] = []
    
    def load(self, split: str = "test") -> List[TemporalSample]:
        """加载ATOMIC数据集"""
        filepath = self.data_dir / "system_eval" / f"{split}.tsv"
        
        if not filepath.exists():
            return []
        
        samples = []
        with open(filepath, 'r', encoding='latin-1') as f:
            for idx, line in enumerate(f):
                line = line.strip().replace('\r', '')
                parts = line.split('\t')
                if len(parts) >= 2:
                    sample = self._convert_line(parts, idx, split)
                    if sample:
                        samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_line(self, parts: List[str], idx: int, split: str) -> Optional[TemporalSample]:
        """转换一行"""
        if len(parts) < 2:
            return None
        
        head = parts[0]
        tail = parts[1]
        
        if not head or not tail:
            return None
        
        head_parts = head.split(' @@ ')
        relation = head_parts[-1] if len(head_parts) > 1 else ""
        premise = ' @@ '.join(head_parts[:-1]) if len(head_parts) > 1 else head
        
        tail_options = tail.split('|')
        tail_options = [t.strip() for t in tail_options if t.strip()]
        
        if not tail_options:
            return None
        
        answer = tail_options[0]
        
        return TemporalSample(
            id=f"atomic_{split}_{idx}",
            task_type=TaskType.T5_COUNTERFACTUAL,
            context=f"[前提]\n{premise}",
            query=f"如果 {premise}，那么 {relation} 是？",
            answer=answer,
            ground_truth={"relation": relation, "options": tail_options},
            metadata={"relation_type": relation, "head": premise}
        )


class TRIPAdapter:
    """TRIP (TripCraft) 数据集适配器
    
    时空旅行规划基准
    来源: ACL 2025
    
    适合 T2 状态追踪和 T3 并发冲突
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir) / "TRIP"
        self.samples: List[TemporalSample] = []
    
    def load(self, split: str = "test") -> List[TemporalSample]:
        """加载TRIP数据集
        
        TRIP 需要额外申请获取数据，暂不支持自动加载
        """
        print("Warning: TRIP (TripCraft) dataset requires additional access request.")
        print("Please contact the authors for dataset access.")
        return []
    
    def load_from_json(self, filepath: str) -> List[TemporalSample]:
        """从 JSON 文件加载 TRIP 数据"""
        samples = []
        
        if not Path(filepath).exists():
            return samples
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                try:
                    item = json.loads(line)
                    sample = self._convert_item(item, idx)
                    if sample:
                        samples.append(sample)
                except json.JSONDecodeError:
                    continue
        
        self.samples = samples
        return samples
    
    def _convert_item(self, item: Dict, idx: int) -> Optional[TemporalSample]:
        """转换一项"""
        query = item.get("query", "") or item.get("instruction", "")
        context = item.get("context", "") or item.get("documents", [])
        
        if isinstance(context, list):
            context = "\n".join([str(c) for c in context])
        
        answer = item.get("answer", "") or item.get("response", "")
        
        if not query:
            return None
        
        return TemporalSample(
            id=f"trip_{idx}",
            task_type=TaskType.T2_STATE_TRACKING,
            context=f"[旅行规划]\n{context}",
            query=query,
            answer=str(answer),
            ground_truth={},
            metadata={"source": "TripCraft", "id": item.get("id", idx)}
        )


class NarrativeQAAdapter:
    """NarrativeQA 数据集适配器
    
    长篇叙事问答
    来源: TACL 2018
    
    适合 T4 长期记忆任务
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir) / "NarrativeQA"
        self.samples: List[TemporalSample] = []
    
    def load(self, split: str = "test") -> List[TemporalSample]:
        """加载NarrativeQA数据集"""
        qaps_file = self.data_dir / "qaps.csv"
        
        if not qaps_file.exists():
            return []
        
        samples = []
        import csv
        
        with open(qaps_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if split and row.get('set', '') != split:
                    continue
                
                sample = self._convert_row(row, idx)
                if sample:
                    samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_row(self, row: Dict, idx: int) -> Optional[TemporalSample]:
        """转换一行"""
        doc_id = row.get("document_id", "")
        question = row.get("question", "")
        answer1 = row.get("answer1", "")
        answer2 = row.get("answer2", "")
        
        if not question:
            return None
        
        context = f"[文档 ID] {doc_id}\n\n请根据文档内容回答问题。"
        
        combined_answer = answer1
        if answer2 and answer2 != answer1:
            combined_answer = f"{answer1} (或: {answer2})"
        
        return TemporalSample(
            id=f"narrativeqa_{doc_id}_{idx}",
            task_type=TaskType.T4_LONG_TERM_MEMORY,
            context=context,
            query=question,
            answer=combined_answer,
            ground_truth={"answer1": answer1, "answer2": answer2},
            metadata={"document_id": doc_id, "set": row.get("set", "")}
        )


# 便捷函数
def load_atomic_data(data_dir: str, split: str = "test") -> List[TemporalSample]:
    """加载ATOMIC数据"""
    adapter = ATOMICAdapter(data_dir)
    return adapter.load(split)

def load_trip_data(data_dir: str) -> List[TemporalSample]:
    """加载TRIP数据"""
    adapter = TRIPAdapter(data_dir)
    return adapter.load()

def load_narrativeqa_data(data_dir: str, split: str = "test") -> List[TemporalSample]:
    """加载NarrativeQA数据"""
    adapter = NarrativeQAAdapter(data_dir)
    return adapter.load(split)


if __name__ == "__main__":
    import sys
    
    print("=== 测试新数据集适配器 ===\n")
    
    data_dir = "data"
    
    # DROP
    try:
        adapter = DROPAdapter(data_dir)
        samples = adapter.load("train")
        print(f"DROP train: {len(samples)} samples")
    except Exception as e:
        print(f"DROP: {e}")
    
    # TimeQA
    try:
        adapter = TimeQAAdapter(data_dir)
        samples = adapter.load("train")
        print(f"TimeQA train: {len(samples)} samples")
    except Exception as e:
        print(f"TimeQA: {e}")
    
    # SocialIQA
    try:
        adapter = SocialIQAAdapter(data_dir)
        samples = adapter.load("dev")
        print(f"SocialIQA dev: {len(samples)} samples")
    except Exception as e:
        print(f"SocialIQA: {e}")
    
    # CosmosQA
    try:
        adapter = CosmosQAAdapter(data_dir)
        samples = adapter.load("dev")
        print(f"CosmosQA dev: {len(samples)} samples")
    except Exception as e:
        print(f"CosmosQA: {e}")
    
    # PIQA
    try:
        adapter = PIQAAdapter(data_dir)
        samples = adapter.load("test")
        print(f"PIQA test: {len(samples)} samples")
    except Exception as e:
        print(f"PIQA: {e}")
    
    # ATOMIC
    try:
        adapter = ATOMICAdapter(data_dir)
        samples = adapter.load("test")
        print(f"ATOMIC test: {len(samples)} samples")
    except Exception as e:
        print(f"ATOMIC: {e}")
    
    # NarrativeQA
    try:
        adapter = NarrativeQAAdapter(data_dir)
        samples = adapter.load("test")
        print(f"NarrativeQA test: {len(samples)} samples")
    except Exception as e:
        print(f"NarrativeQA: {e}")
