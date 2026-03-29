"""数据集适配器 - 将现有数据集转换为统一格式

将 data/ 目录下的数据集转换为 arch/task_schema.py 定义的 TemporalSample 格式。

适配的数据集:
- MCTACO: 时间常识理解
- UDST-DurationQA: 持续时间QA
- TimeDial: 对话时间推理
- TRACIE: 隐式事件推理
- situated_gen: 生成式常识推理
- UDS_T_v1.0: 时间关系提取
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .task_schema import TemporalSample, TaskType, DifficultyLevel


class DatasetAdapter:
    """数据集适配器基类"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.samples: List[TemporalSample] = []
    
    def load(self) -> List[TemporalSample]:
        """加载并转换数据集"""
        raise NotImplementedError
    
    def convert(self, raw_sample: Dict) -> Optional[TemporalSample]:
        """转换单个样本为统一格式"""
        raise NotImplementedError


class MCTACOAdapter(DatasetAdapter):
    """MCTACO 数据集适配器
    
    原始格式: TSV (context, question, answer, label, category)
    任务类型: T1 (时间计算) / T2 (状态更新)
    """
    
    CATEGORY_TO_TASK = {
        "Event Duration": TaskType.T1_TEMPORAL_CALCULATION,
        "Stationarity": TaskType.T2_STATE_TRACKING,
        "Event Ordering": TaskType.T1_TEMPORAL_CALCULATION,
        "Frequency": TaskType.T1_TEMPORAL_CALCULATION,
    }
    
    def load(self, split: str = "test") -> List[TemporalSample]:
        """加载MCTACO数据集
        
        Args:
            split: "dev" 或 "test"
        """
        filepath = self.data_dir / "MCTACO" / "dataset" / f"{split}_9442.tsv"
        if split == "dev":
            filepath = self.data_dir / "MCTACO" / "dataset" / "dev_3783.tsv"
        
        samples = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                parts = line.strip().split('\t')
                if len(parts) >= 5:
                    sample = self._convert_line(parts, f"{split}_{line_num}")
                    if sample:
                        samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_line(self, parts: List[str], sample_id: str) -> Optional[TemporalSample]:
        """转换一行数据"""
        context, question, answer, label, category = parts[:5]
        
        if label.lower() != 'yes':
            return None
        
        task_type = self.CATEGORY_TO_TASK.get(category, TaskType.T1_TEMPORAL_CALCULATION)
        
        metadata = {
            "original_category": category,
            "label": label,
        }
        
        return TemporalSample(
            id=f"mctaco_{sample_id}",
            task_type=task_type,
            context=context,
            query=question,
            answer=answer,
            ground_truth={"answer": answer, "label": label},
            metadata=metadata
        )


class UDSTDurationQAAdapter(DatasetAdapter):
    """UDST-DurationQA 数据集适配器
    
    原始格式: TSV (sentence, question, answer, label)
    任务类型: T1 (时间计算) - 持续时间问答
    """
    
    def load(self, split: str = "train") -> List[TemporalSample]:
        """加载UDST-DurationQA数据集"""
        filepath = self.data_dir / "UDST-DurationQA" / "data" / f"{split}.tsv"
        
        samples = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                parts = line.strip().split('\t')
                if len(parts) >= 4:
                    sample = self._convert_line(parts, f"{split}_{line_num}")
                    if sample:
                        samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_line(self, parts: List[str], sample_id: str) -> Optional[TemporalSample]:
        """转换一行数据"""
        sentence, question, answer, label = parts[:4]
        
        if label.lower() != 'yes':
            return None
        
        return TemporalSample(
            id=f"udst_dur_{sample_id}",
            task_type=TaskType.T1_TEMPORAL_CALCULATION,
            context=sentence,
            query=question,
            answer=answer,
            ground_truth={"answer": answer, "label": label},
            metadata={"source": "UDST-DurationQA"}
        )


class TimeDialAdapter(DatasetAdapter):
    """TimeDial 数据集适配器
    
    原始格式: JSON (conversation, correct1, correct2, incorrect1, incorrect2)
    任务类型: T1 (时间计算) - 对话时间推理
    """
    
    def load(self) -> List[TemporalSample]:
        """加载TimeDial数据集"""
        filepath = self.data_dir / "TimeDial" / "test.json"
        
        samples = []
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if isinstance(item, dict) and 'conversation' in item:
                    sample = self._convert_item(item)
                    if sample:
                        samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_item(self, item: Dict) -> Optional[TemporalSample]:
        """转换一个对话项"""
        conversation = item.get('conversation', [])
        if not conversation:
            return None
        
        dialogue_text = "\n".join([f"{i+1}: {c}" for i, c in enumerate(conversation)])
        correct1 = item.get('correct1', '')
        correct2 = item.get('correct2', '')
        
        correct_answers = [a.strip() for a in [correct1, correct2] if a.strip() and a.strip() != 'none']
        if not correct_answers:
            return None
        
        incorrect1 = item.get('incorrect1', '')
        incorrect2 = item.get('incorrect2', '')
        
        return TemporalSample(
            id=f"timedial_{item.get('id', 'unknown')}",
            task_type=TaskType.T1_TEMPORAL_CALCULATION,
            context=f"[对话历史]\n{dialogue_text}",
            query="根据对话上下文，<MASK>处应该填什么时间表达？",
            answer=correct_answers[0] if correct_answers else None,
            ground_truth={
                "correct_answers": correct_answers,
                "incorrect_answers": [incorrect1, incorrect2],
            },
            metadata={
                "conversation": conversation,
                "incorrect1_rule": item.get('incorrect1_rule', ''),
                "incorrect2_rule": item.get('incorrect2_rule', ''),
            }
        )


class TRACIEAdapter(DatasetAdapter):
    """TRACIE 数据集适配器
    
    原始格式: 文本 (event: ... story: ... answer: positive/negative)
    任务类型: T2 (状态更新) - 隐式事件时间推理
    """
    
    def load(self, split: str = "train") -> List[TemporalSample]:
        """加载TRACIE数据集"""
        filepath = self.data_dir / "tracie" / "data" / "iid" / f"tracie_{split}.txt"
        
        samples = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                sample = self._convert_line(line, f"{split}_{line_num}")
                if sample:
                    samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_line(self, line: str, sample_id: str) -> Optional[TemporalSample]:
        """转换一行数据"""
        if '\t' not in line:
            return None
        
        parts = line.strip().split('\t')
        if len(parts) < 2:
            return None
        
        event_story = parts[0]
        answer = parts[1].replace('answer: ', '').strip()
        
        event = ""
        story = ""
        
        if 'story:' in event_story:
            event_part, story_part = event_story.split('story:', 1)
            event = event_part.replace('event:', '').strip()
            story = story_part.strip()
        else:
            event = event_story
        
        return TemporalSample(
            id=f"tracie_{sample_id}",
            task_type=TaskType.T2_STATE_TRACKING,
            context=f"[事件描述]\n{event}\n\n[故事上下文]\n{story}",
            query="事件的时间关系是否正确？",
            answer="正确" if answer == 'positive' else "不正确",
            ground_truth={"is_correct": answer == 'positive', "raw_answer": answer},
            metadata={"source": "TRACIE", "event": event}
        )


class SituatedGenAdapter(DatasetAdapter):
    """SituatedGen 数据集适配器
    
    原始格式: JSONL (keywords, statement, ids, keywords_pos, statements)
    任务类型: 用于数据增强和示例生成
    """
    
    def load(self, split: str = "train") -> List[TemporalSample]:
        """加载SituatedGen数据集"""
        filepath = self.data_dir / "situated_gen" / "data" / f"{split}.jsonl"
        
        samples = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                item = json.loads(line.strip())
                sample = self._convert_item(item, f"{split}_{line_num}")
                if sample:
                    samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_item(self, item: Dict, sample_id: str) -> Optional[TemporalSample]:
        """转换一个JSON项"""
        keywords = item.get('keywords', [])
        statement = item.get('statement', '')
        statements = item.get('statements', [])
        
        if not statement:
            return None
        
        return TemporalSample(
            id=f"situated_{sample_id}",
            task_type=TaskType.T2_STATE_TRACKING,
            context=f"[关键词]\n{', '.join(keywords)}",
            event=statement,
            query="根据关键词生成包含时间信息的句子",
            answer=statement,
            ground_truth={"keywords": keywords, "statements": statements},
            metadata={
                "ids": item.get('ids', []),
                "keywords_pos": item.get('keywords_pos', []),
            }
        )


class UDSTAdapter(DatasetAdapter):
    """UDS_T_v1.0 数据集适配器
    
    原始格式: TSV (丰富的时间标注)
    任务类型: 用于提取时间关系知识
    """
    
    def load(self, split: str = "train") -> List[TemporalSample]:
        """加载UDS_T数据集"""
        filepath = self.data_dir / "UDS_T_v1.0" / "time_eng_ud_v1.2_2015_10_30.tsv"
        
        samples = []
        with open(filepath, 'r', encoding='utf-8') as f:
            header = f.readline()
            for line_num, line in enumerate(f, 1):
                parts = line.strip().split('\t')
                if len(parts) >= 23:
                    sample = self._convert_line(parts, f"{split}_{line_num}")
                    if sample and sample.metadata.get('split') == split:
                        samples.append(sample)
        
        self.samples = samples
        return samples
    
    def _convert_line(self, parts: List[str], sample_id: str) -> Optional[TemporalSample]:
        """转换一行数据"""
        if len(parts) < 23:
            return None
        
        split = parts[0]
        pred1_text = parts[11]
        pred2_text = parts[13]
        pred1_duration = parts[15]
        pred2_duration = parts[16]
        
        return TemporalSample(
            id=f"udst_{sample_id}",
            task_type=TaskType.T1_TEMPORAL_CALCULATION,
            context=f"[事件1]\n{pred1_text}\n\n[事件2]\n{pred2_text}",
            query="分析两个事件的时间关系",
            answer=f"事件1持续时间标签: {pred1_duration}, 事件2持续时间标签: {pred2_duration}",
            ground_truth={
                "pred1_duration": pred1_duration,
                "pred2_duration": pred2_duration,
            },
            metadata={
                "split": split,
                "pred1_span": parts[3],
                "pred2_span": parts[5],
                "pred1_lemma": parts[12],
                "pred2_lemma": parts[14],
            }
        )


class DatasetConverter:
    """数据集转换器 - 将多个数据集转换为统一格式"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.adapters: Dict[str, DatasetAdapter] = {}
    
    def register_adapter(self, name: str, adapter: DatasetAdapter):
        """注册适配器"""
        self.adapters[name] = adapter
    
    def convert_all(self) -> Dict[str, List[TemporalSample]]:
        """转换所有已注册的数据集"""
        results = {}
        for name, adapter in self.adapters.items():
            try:
                samples = adapter.load()
                results[name] = samples
                print(f"  {name}: {len(samples)} samples")
            except Exception as e:
                print(f"  {name}: 转换失败 - {e}")
                results[name] = []
        return results
    
    def save_converted(self, samples: Dict[str, List[TemporalSample]], output_dir: str):
        """保存转换后的数据集"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        all_samples = []
        for name, sample_list in samples.items():
            for sample in sample_list:
                all_samples.append(sample.to_dict())
            
            filepath = output_path / f"{name}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([s.to_dict() for s in sample_list], f, ensure_ascii=False, indent=2)
            print(f"  Saved {name}: {filepath}")
        
        all_filepath = output_path / "all_samples.json"
        with open(all_filepath, 'w', encoding='utf-8') as f:
            json.dump(all_samples, f, ensure_ascii=False, indent=2)
        print(f"  Saved all samples: {all_filepath}")
        
        return all_samples


def convert_all_datasets(data_dir: str, output_dir: str) -> List[TemporalSample]:
    """转换所有可用数据集
    
    Args:
        data_dir: 数据根目录
        output_dir: 输出目录
    
    Returns:
        所有转换后的样本列表
    """
    converter = DatasetConverter(data_dir)
    
    converter.register_adapter("mctaco", MCTACOAdapter(data_dir))
    converter.register_adapter("udst_duration_qa", UDSTDurationQAAdapter(data_dir))
    converter.register_adapter("timedial", TimeDialAdapter(data_dir))
    converter.register_adapter("tracie", TRACIEAdapter(data_dir))
    converter.register_adapter("situated_gen", SituatedGenAdapter(data_dir))
    converter.register_adapter("udst", UDSTAdapter(data_dir))
    
    print("开始转换数据集...")
    results = converter.convert_all()
    
    print("\n保存转换后的数据集...")
    all_samples = converter.save_converted(results, output_dir)
    
    print(f"\n转换完成！共 {len(all_samples)} 个样本")
    return all_samples


if __name__ == "__main__":
    import sys
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    output_dir = project_root / "arch" / "converted_data"
    
    convert_all_datasets(str(data_dir), str(output_dir))
