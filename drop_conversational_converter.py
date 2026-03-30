#!/usr/bin/env python3
"""
DROP Temporal Awareness Data Converter - Conversational Only
==============================================================
将DROP（Discrete Reasoning Over Paragraphs）数据转化为对话式时间感知评测数据。

核心特点：
- 数值推理（加减法、排序、计数）
- 体育比赛事件（时间戳、得分）
- 跨句引用解析

任务映射：
- T1: 时间计算（极高匹配）- 数值转时间计算
- T3: 并发冲突（高匹配）- 时间重叠冲突
- T5: 反事实（极高匹配）- 修改计分规则

作者：TemporalAware Team
"""

import json
import pandas as pd
import re
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Configuration
DATA_DIR = Path("data/DROP")
OUTPUT_DIR = Path("converted_data_v3")


@dataclass
class ConversationalSample:
    """对话式时间感知评测数据样本。"""
    task: str  # T1, T3, T5
    sub_task: str  # 细分任务
    passage: str  # 原始段落
    conversation: List[Dict[str, str]]  # 多轮对话
    query: str  # 最终问题
    answer: str  # 答案
    state_info: Optional[Dict[str, Any]] = None
    ground_truth: Optional[Dict[str, Any]] = None
    difficulty: str = "medium"
    source_id: Optional[str] = None


class DROPLoader:
    """加载DROP数据集。"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        
    def load(self) -> pd.DataFrame:
        """加载数据。"""
        # 尝试 parquet 格式
        parquet_file = self.data_dir / "train-00000-of-00001.parquet"
        if parquet_file.exists():
            print(f"Loading DROP from {parquet_file}...")
            df = pd.read_parquet(parquet_file)
            print(f"Loaded {len(df)} samples from parquet")
            return df
        
        # 尝试 JSONL 格式
        jsonl_file = self.data_dir / "DROP.jsonl"
        if jsonl_file.exists():
            print(f"Loading DROP from {jsonl_file}...")
            data = []
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data.append(json.loads(line))
            df = pd.DataFrame(data)
            print(f"Loaded {len(df)} samples from JSONL")
            return df
        
        raise FileNotFoundError("No DROP data file found")
    
    def extract_numbers(self, passage: str, question: str) -> Tuple[List[int], List[str]]:
        """从文本提取数字和单位。"""
        # 提取数字
        numbers = re.findall(r'\b(\d+)\b', passage + " " + question)
        numbers = [int(n) for n in numbers if int(n) > 0]
        
        # 提取时间相关单位
        time_units = re.findall(r'\b(minutes?|hours?|seconds?|quarters?|yards?|points?|times?)\b', 
                               (passage + " " + question).lower())
        
        return numbers, time_units
    
    def extract_scores(self, passage: str) -> List[Dict[str, Any]]:
        """提取得分信息。"""
        # 匹配得分模式：Team A 21, Team B 14
        score_pattern = r'(\d+)\s*[-–]\s*(\d+)'
        scores = []
        
        for match in re.finditer(score_pattern, passage):
            scores.append({
                'score1': int(match.group(1)),
                'score2': int(match.group(2)),
                'position': match.start()
            })
        
        # 匹配 touchdown, field goal 等
        scoring_events = re.findall(r'(touchdown|field goal|extra point|safety)', passage.lower())
        
        return scores, scoring_events
    
    def extract_time_refs(self, passage: str) -> List[Dict[str, str]]:
        """提取时间引用。"""
        time_refs = []
        
        # 匹配时间：1:00 PM, 3:15, etc.
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM)?)',
            r'(first quarter|second quarter|third quarter|fourth quarter)',
            r'(halftime|overtime)',
            r'(\d+\s*(?:minutes?|hours?|seconds?)\s*(?:remaining|left|into))',
        ]
        
        for pattern in time_patterns:
            for match in re.finditer(pattern, passage, re.IGNORECASE):
                time_refs.append({
                    'text': match.group(0),
                    'position': match.start()
                })
        
        return time_refs


class DROPConversationalConverter:
    """DROP对话式数据转换器。"""
    
    # NFL计分规则
    NFL_SCORING = {
        'touchdown': 6,
        'field_goal': 3,
        'extra_point': 1,
        'two_point_conversion': 2,
        'safety': 2
    }
    
    # 反事实计分规则（修改版）
    COUNTERFACTUAL_SCORING = {
        'touchdown': 10,  # 原来是6，改为10
        'field_goal': 1,   # 原来是3，改为1
        'extra_point': 5,  # 原来是1，改为5
        'safety': 3        # 原来是2，改为3
    }
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.loader = DROPLoader(DATA_DIR)
        self.samples: List[ConversationalSample] = []
        
    def convert_all(self, max_samples: int = 5000) -> List[ConversationalSample]:
        """转换所有数据。"""
        print("\n" + "="*60)
        print("Converting DROP to Conversational Temporal Data")
        print("="*60)
        
        count = 0
        for idx, row in self.df.iterrows():
            if count >= max_samples:
                break
            
            passage = row.get('passage', '')
            question = row.get('question', '')
            answer_spans = row.get('answers_spans', {})
            
            # 提取答案
            if isinstance(answer_spans, dict):
                spans = answer_spans.get('spans', [])
                answer_types = answer_spans.get('types', [])
            else:
                spans = []
                answer_types = []
            
            # 处理numpy array
            if hasattr(spans, '__len__') and len(spans) == 0:
                continue
            if hasattr(spans, '__len__') and len(spans) > 0:
                span_value = spans[0] if hasattr(spans, '__getitem__') else spans
                answer = str(span_value) if span_value is not None else ""
            else:
                answer = str(spans) if spans else ""
            
            if not answer:
                continue
            
            # T1: 时间计算
            t1_samples = self._generate_t1_samples(passage, question, answer, row)
            self.samples.extend(t1_samples)
            
            # T3: 并发冲突
            t3_samples = self._generate_t3_samples(passage, question, answer, row)
            self.samples.extend(t3_samples)
            
            # T5: 反事实
            t5_samples = self._generate_t5_samples(passage, question, answer, row)
            self.samples.extend(t5_samples)
            
            count += 1
        
        print(f"\nTotal converted: {len(self.samples)} samples")
        return self.samples
    
    # =====================================================================
    # T1: 时间计算 (Time Calculation)
    # =====================================================================
    
    def _generate_t1_samples(self, passage: str, question: str, 
                            answer: str, row: pd.Series) -> List[ConversationalSample]:
        """生成T1时间计算样本。"""
        results = []
        
        numbers, time_units = self.loader.extract_numbers(passage, question)
        time_refs = self.loader.extract_time_refs(passage)
        
        # 只处理包含数字和时间的样本
        if not numbers or not time_units:
            return results
        
        # T1-Convo-Duration: 时长计算
        conv = self._create_duration_conversation(passage, question, answer, numbers, time_units, row)
        if conv:
            results.append(conv)
        
        # T1-Convo-Addition: 时间加法
        conv = self._create_addition_conversation(passage, question, answer, numbers, row)
        if conv:
            results.append(conv)
        
        # T1-Convo-Sequence: 时间序列
        conv = self._create_sequence_conversation(passage, question, answer, numbers, time_refs, row)
        if conv:
            results.append(conv)
        
        return results
    
    def _create_duration_conversation(self, passage: str, question: str,
                                       answer: str, numbers: List[int], 
                                       time_units: List[str], row: pd.Series) -> Optional[ConversationalSample]:
        """创建时长计算对话。"""
        # 构造时间场景
        if len(numbers) < 2:
            return None
        
        # 使用数字构造时间问题
        start_time = random.choice([1, 2, 3, 10, 15])
        duration = numbers[0] if numbers[0] < 60 else random.choice([15, 30, 45])
        
        conversation = []
        
        # 分段叙述
        sentences = passage.split('. ')[:3]
        for sent in sentences:
            if sent.strip():
                conversation.append({
                    "role": "user",
                    "content": sent.strip() + "."
                })
        
        # 添加时间信息
        conversation.append({
            "role": "user",
            "content": f"The game started at {start_time}:00 PM."
        })
        
        # 干扰
        conversation.append({
            "role": "user",
            "content": "By the way, how's the weather?"
        })
        conversation.append({
            "role": "assistant",
            "content": "I don't have weather information."
        })
        
        # 时间计算问题
        conversation.append({
            "role": "user",
            "content": f"If the first half lasted {duration} minutes, when did halftime begin?"
        })
        
        # 计算答案
        end_minute = start_time * 60 + duration
        end_hour = end_minute // 60
        end_min = end_minute % 60
        answer_text = f"{end_hour}:{end_min:02d} PM"
        
        return ConversationalSample(
            task="T1",
            sub_task="T1-Convo-Duration",
            passage=passage[:500],
            conversation=conversation,
            query=f"If the game started at {start_time}:00 PM and the first half lasted {duration} minutes, when did halftime begin?",
            answer=answer_text,
            state_info={
                "type": "duration_calculation",
                "start_time": f"{start_time}:00 PM",
                "duration": duration,
                "operation": "addition"
            },
            ground_truth={
                "start_minutes": start_time * 60,
                "duration": duration,
                "end_time": answer_text
            },
            difficulty="medium",
            source_id=f"drop_t1_dur_{row.get('query_id', 'unknown')[:20]}"
        )
    
    def _create_addition_conversation(self, passage: str, question: str,
                                       answer: str, numbers: List[int], 
                                       row: pd.Series) -> Optional[ConversationalSample]:
        """创建时间加法对话。"""
        if len(numbers) < 2:
            return None
        
        # 取两个数字进行加法
        num1 = numbers[0] if numbers[0] < 60 else 10
        num2 = numbers[1] if len(numbers) > 1 and numbers[1] < 60 else 5
        
        operation = random.choice(["drive", "travel", "walk", "run"])
        
        conversation = []
        
        sentences = passage.split('. ')[:2]
        for sent in sentences:
            if sent.strip():
                conversation.append({
                    "role": "user",
                    "content": sent.strip() + "."
                })
        
        conversation.append({
            "role": "user",
            "content": f"I {operation} for {num1} minutes first, then {num2} more minutes."
        })
        
        conversation.append({
            "role": "user",
            "content": "What's for dinner today?"  # 干扰
        })
        conversation.append({
            "role": "assistant",
            "content": "I don't know your dinner plans."
        })
        
        conversation.append({
            "role": "user",
            "content": f"How long did I {operation} in total?"
        })
        
        return ConversationalSample(
            task="T1",
            sub_task="T1-Convo-Addition",
            passage=passage[:500],
            conversation=conversation,
            query=f"If I {operation} for {num1} minutes and then {num2} more minutes, how long in total?",
            answer=f"{num1 + num2} minutes",
            state_info={
                "type": "time_addition",
                "num1": num1,
                "num2": num2,
                "operation": "addition"
            },
            ground_truth={
                "result": num1 + num2,
                "unit": "minutes"
            },
            difficulty="easy",
            source_id=f"drop_t1_add_{row.get('query_id', 'unknown')[:20]}"
        )
    
    def _create_sequence_conversation(self, passage: str, question: str,
                                        answer: str, numbers: List[int],
                                        time_refs: List[Dict[str, str]], row: pd.Series) -> Optional[ConversationalSample]:
        """创建时间序列对话。"""
        if not time_refs:
            return None
        
        time_ref = time_refs[0]['text']
        
        conversation = []
        
        sentences = passage.split('. ')[:3]
        for sent in sentences:
            if sent.strip():
                conversation.append({
                    "role": "user",
                    "content": sent.strip() + "."
                })
        
        conversation.append({
            "role": "user",
            "content": "When did this event happen in the game?"
        })
        
        # 找到原始问题中的时间相关信息
        return ConversationalSample(
            task="T1",
            sub_task="T1-Convo-Sequence",
            passage=passage[:500],
            conversation=conversation,
            query=f"According to the passage, at what time reference '{time_ref}' did this occur?",
            answer=answer,
            state_info={
                "type": "time_sequence",
                "time_reference": time_ref
            },
            ground_truth={
                "original_answer": answer,
                "time_ref": time_ref
            },
            difficulty="medium",
            source_id=f"drop_t1_seq_{row.get('query_id', 'unknown')[:20]}"
        )
    
    # =====================================================================
    # T3: 并发冲突 (Conflict Detection)
    # =====================================================================
    
    def _generate_t3_samples(self, passage: str, question: str,
                             answer: str, row: pd.Series) -> List[ConversationalSample]:
        """生成T3并发冲突样本。"""
        results = []
        
        scores, scoring_events = self.loader.extract_scores(passage)
        time_refs = self.loader.extract_time_refs(passage)
        
        # T3-Convo-TimeOverlap: 时间重叠冲突
        if time_refs:
            conv = self._create_time_overlap_conversation(passage, question, answer, time_refs, row)
            if conv:
                results.append(conv)
        
        # T3-Convo-Conflict: 事件冲突
        if scores:
            conv = self._create_event_conflict_conversation(passage, question, answer, scores, row)
            if conv:
                results.append(conv)
        
        return results
    
    def _create_time_overlap_conversation(self, passage: str, question: str,
                                           answer: str, time_refs: List[Dict], 
                                           row: pd.Series) -> Optional[ConversationalSample]:
        """创建时间重叠冲突对话。"""
        conversation = []
        
        sentences = passage.split('. ')[:3]
        for sent in sentences:
            if sent.strip():
                conversation.append({
                    "role": "user",
                    "content": sent.strip() + "."
                })
        
        # 构造冲突场景
        conversation.append({
            "role": "user",
            "content": "Wait, let me add more context."
        })
        conversation.append({
            "role": "user",
            "content": "During the same time, the coach was supposed to be at a press conference downtown."
        })
        
        conversation.append({
            "role": "user",
            "content": "I also heard about a weather forecast. But that's unrelated."
        })
        conversation.append({
            "role": "assistant",
            "content": "Okay, noted."
        })
        
        conversation.append({
            "role": "user",
            "content": "Is there any scheduling conflict here?"
        })
        
        return ConversationalSample(
            task="T3",
            sub_task="T3-Convo-TimeOverlap",
            passage=passage[:500],
            conversation=conversation,
            query="Given the game schedule and the coach's press conference, is there a time conflict?",
            answer="Yes, there is a scheduling conflict - both events occur during the same time period",
            state_info={
                "type": "time_overlap",
                "time_refs": [t['text'] for t in time_refs[:3]]
            },
            ground_truth={
                "has_conflict": True,
                "conflict_type": "time_overlap"
            },
            difficulty="medium",
            source_id=f"drop_t3_overlap_{row.get('query_id', 'unknown')[:20]}"
        )
    
    def _create_event_conflict_conversation(self, passage: str, question: str,
                                             answer: str, scores: List[Dict],
                                             row: pd.Series) -> Optional[ConversationalSample]:
        """创建事件冲突对话。"""
        if not scores:
            return None
        
        score = scores[0]
        
        conversation = []
        
        sentences = passage.split('. ')[:2]
        for sent in sentences:
            if sent.strip():
                conversation.append({
                    "role": "user",
                    "content": sent.strip() + "."
                })
        
        # 添加冲突事件
        conversation.append({
            "role": "user",
            "content": "Meanwhile, in the same city, a concert was scheduled at the same time."
        })
        conversation.append({
            "role": "assistant",
            "content": "A concert at the same time?"
        })
        conversation.append({
            "role": "user",
            "content": "Yes, and both events need parking. The stadium parking lot is shared."
        })
        
        conversation.append({
            "role": "user",
            "content": "What parking conflict might occur?"
        })
        
        return ConversationalSample(
            task="T3",
            sub_task="T3-Convo-Conflict",
            passage=passage[:500],
            conversation=conversation,
            query="If the game and concert happen at the same time with shared parking, what conflict emerges?",
            answer="Parking shortage - both events compete for limited parking spaces",
            state_info={
                "type": "event_conflict",
                "events": ["game", "concert"],
                "resource": "parking"
            },
            ground_truth={
                "conflict_type": "resource_conflict",
                "shared_resource": "parking"
            },
            difficulty="hard",
            source_id=f"drop_t3_conflict_{row.get('query_id', 'unknown')[:20]}"
        )
    
    # =====================================================================
    # T5: 反事实 (Counterfactual Scoring)
    # =====================================================================
    
    def _generate_t5_samples(self, passage: str, question: str,
                             answer: str, row: pd.Series) -> List[ConversationalSample]:
        """生成T5反事实样本。"""
        results = []
        
        scores, scoring_events = self.loader.extract_scores(passage)
        numbers, _ = self.loader.extract_numbers(passage, question)
        
        # T5-Convo-RuleChange: 规则改变
        conv = self._create_rule_change_conversation(passage, question, answer, scoring_events, numbers, row)
        if conv:
            results.append(conv)
        
        # T5-Convo-Counterfactual: 反事实计算
        if scoring_events:
            conv = self._create_counterfactual_scoring_conversation(passage, question, answer, scoring_events, row)
            if conv:
                results.append(conv)
        
        return results
    
    def _create_rule_change_conversation(self, passage: str, question: str,
                                          answer: str, scoring_events: List[str],
                                          numbers: List[int], row: pd.Series) -> Optional[ConversationalSample]:
        """创建规则改变对话。"""
        conversation = []
        
        # 建立上下文
        sentences = passage.split('. ')[:3]
        for sent in sentences:
            if sent.strip():
                conversation.append({
                    "role": "user",
                    "content": sent.strip() + "."
                })
        
        # 定义反事实规则
        conversation.append({
            "role": "user",
            "content": "Let's imagine a different football league with modified scoring rules."
        })
        conversation.append({
            "role": "assistant",
            "content": "Okay, what are the modified rules?"
        })
        
        # 反事实规则
        conversation.append({
            "role": "user",
            "content": "In this league:"
        })
        conversation.append({
            "role": "user",
            "content": "• Touchdown = 10 points (not 6)"
        })
        conversation.append({
            "role": "user",
            "content": "• Field goal = 1 point (not 3)"
        })
        conversation.append({
            "role": "user",
            "content": "• Extra point = 5 points (not 1)"
        })
        conversation.append({
            "role": "assistant",
            "content": "Understood: scoring is reversed in importance."
        })
        
        # 计算问题
        num_touchdowns = random.choice([1, 2, 3])
        num_field_goals = random.choice([1, 2])
        
        conversation.append({
            "role": "user",
            "content": "If a team scores 2 touchdowns and 1 field goal in THIS league, how many points?"
        })
        
        # 反事实计算
        cf_score = num_touchdowns * self.COUNTERFACTUAL_SCORING['touchdown'] + \
                   num_field_goals * self.COUNTERFACTUAL_SCORING['field_goal']
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-RuleChange",
            passage=passage[:500],
            conversation=conversation,
            query="Under the modified scoring rules, how many points is 2 touchdowns + 1 field goal?",
            answer=f"{cf_score} points",
            state_info={
                "type": "rule_change",
                "original_rules": self.NFL_SCORING,
                "counterfactual_rules": self.COUNTERFACTUAL_SCORING,
                "calculation": {
                    "touchdowns": num_touchdowns,
                    "field_goals": num_field_goals,
                    "total": cf_score
                }
            },
            ground_truth={
                "counterfactual_score": cf_score,
                "normal_score": num_touchdowns * 6 + num_field_goals * 3,
                "rule_type": "scoring_modified"
            },
            difficulty="hard",
            source_id=f"drop_t5_rule_{row.get('query_id', 'unknown')[:20]}"
        )
    
    def _create_counterfactual_scoring_conversation(self, passage: str, question: str,
                                                    answer: str, scoring_events: List[str],
                                                    row: pd.Series) -> Optional[ConversationalSample]:
        """创建反事实计分对话。"""
        conversation = []
        
        sentences = passage.split('. ')[:2]
        for sent in sentences:
            if sent.strip():
                conversation.append({
                    "role": "user",
                    "content": sent.strip() + "."
                })
        
        # 假设规则
        conversation.append({
            "role": "user",
            "content": "Now imagine this is a practice game with unusual rules."
        })
        conversation.append({
            "role": "assistant",
            "content": "What are the unusual rules?"
        })
        
        # 从passage提取得分事件并应用反事实
        event_count = len(scoring_events) if scoring_events else 2
        touch_count = event_count // 2 if event_count > 1 else 1
        
        conversation.append({
            "role": "user",
            "content": "In this practice game, touchdowns are worth DOUBLE, but field goals are FREE (0 points)."
        })
        
        conversation.append({
            "role": "user",
            "content": f"If I see {touch_count} touchdowns mentioned in the text, how many practice points?"
        })
        
        cf_points = touch_count * 12  # 双倍touchdown
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-Counterfactual",
            passage=passage[:500],
            conversation=conversation,
            query=f"With double touchdown points, how many points from {touch_count} touchdowns?",
            answer=f"{cf_points} points",
            state_info={
                "type": "counterfactual_scoring",
                "events": scoring_events,
                "touchdown_count": touch_count,
                "multiplier": 2
            },
            ground_truth={
                "counterfactual_points": cf_points,
                "original_points": touch_count * 6
            },
            difficulty="medium",
            source_id=f"drop_t5_cf_{row.get('query_id', 'unknown')[:20]}"
        )


def main():
    """主函数。"""
    print("="*60)
    print("DROP Conversational Temporal Data Converter")
    print("="*60)
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载数据
    loader = DROPLoader(DATA_DIR)
    df = loader.load()
    
    # 只使用部分数据
    df = df.head(3000)
    print(f"Using {len(df)} samples for conversion")
    
    # 转换
    converter = DROPConversationalConverter(df)
    samples = converter.convert_all(max_samples=len(df))
    
    # 保存
    output_file = OUTPUT_DIR / "drop_conversational.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
    
    print(f"\nSaved to: {output_file}")
    
    # 统计报告
    report = {
        "total_samples": len(samples),
        "task_distribution": {},
        "subtask_distribution": {},
        "difficulty_distribution": {}
    }
    
    for sample in samples:
        task = sample.task
        subtask = sample.sub_task
        diff = sample.difficulty
        
        report["task_distribution"][task] = report["task_distribution"].get(task, 0) + 1
        report["subtask_distribution"][subtask] = report["subtask_distribution"].get(subtask, 0) + 1
        report["difficulty_distribution"][diff] = report["difficulty_distribution"].get(diff, 0) + 1
    
    report_file = OUTPUT_DIR / "drop_conversational_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("Conversion Summary")
    print("="*60)
    print(f"Total samples: {len(samples)}")
    print("\nTask distribution:")
    for task, count in report["task_distribution"].items():
        print(f"  {task}: {count}")
    print("\nSubtask distribution:")
    for subtask, count in report["subtask_distribution"].items():
        print(f"  {subtask}: {count}")
    print("\nDifficulty distribution:")
    for diff, count in report["difficulty_distribution"].items():
        print(f"  {diff}: {count}")


if __name__ == "__main__":
    main()