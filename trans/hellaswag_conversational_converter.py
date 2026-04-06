#!/usr/bin/env python3
"""
HellaSwag Temporal Awareness Data Converter - Conversational Only
====================================================================
将HellaSwag常识性连续推理数据转化为对话式时间感知评测数据。

核心特点：
- 常识性连续推理（物理世界时序逻辑）
- WikiHow生活指南 + ActivityNet视频描述
- 动作序列的因果推理

任务映射：
- T2: 状态更新（极高匹配）- 动作进行中推断状态
- T3: 并发冲突（中匹配）- 互斥动作冲突
- T5: 反事实（极高匹配）- 反转常识规则

作者：TemporalAware Team
"""

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Configuration
DATA_DIR = Path("data/HellaSwag/data")
OUTPUT_DIR = Path("converted_data_v3")


@dataclass
class ConversationalSample:
    """对话式时间感知评测数据样本。"""
    task: str  # T2, T3, T5
    sub_task: str  # 细分任务
    context: str  # 原始上下文
    conversation: List[Dict[str, str]]  # 多轮对话
    query: str  # 最终问题
    answer: str  # 答案
    state_info: Optional[Dict[str, Any]] = None
    ground_truth: Optional[Dict[str, Any]] = None
    difficulty: str = "medium"
    source_id: Optional[str] = None


class HellaSwagLoader:
    """加载HellaSwag数据集。"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        
    def load(self, split: str = "train") -> List[Dict]:
        """加载数据。"""
        file_path = self.data_dir / f"hellaswag_{split}.jsonl"
        print(f"Loading HellaSwag from {file_path}...")
        
        samples = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                samples.append(json.loads(line))
        
        print(f"Loaded {len(samples)} samples")
        return samples
    
    def extract_activity_keywords(self, activity_label: str) -> List[str]:
        """提取活动关键词。"""
        # 常见活动关键词
        keywords = re.findall(r'\b(removing|cleaning|baking|cooking|cutting|washing|driving|walking|running|jumping|swimming|eating|drinking|sleeping|working|playing|watching|reading|writing|fixing|building|painting|moving|lifting|carrying)\b', activity_label.lower())
        return keywords
    
    def classify_activity_location(self, activity_label: str) -> Optional[str]:
        """分类活动地点。"""
        location_keywords = {
            "indoor": ["baking", "cooking", "cleaning", "washing", "sleeping", "watching", "reading", "writing", "fixing"],
            "outdoor": ["removing", "driving", "walking", "running", "jumping", "swimming", "playing", "moving"],
            "vehicle": ["driving", "car", "bus", "train", "bike"]
        }
        
        activity_lower = activity_label.lower()
        for location, keywords in location_keywords.items():
            for kw in keywords:
                if kw in activity_lower:
                    return location
        return None


class HellaSwagConversationalConverter:
    """HellaSwag对话式数据转换器。"""
    
    def __init__(self, samples: List[Dict]):
        self.samples = samples
        self.loader = HellaSwagLoader(DATA_DIR)
        self.converted: List[ConversationalSample] = []

    def _normalize_ending(self, text: str) -> str:
        """Normalize ending text for readable options/answers."""
        clean = (text or "").strip()
        clean = re.sub(r"^[,\s]+", "", clean)
        clean = re.sub(r"\s+", " ", clean)
        return clean

    def _option_letter(self, idx: int) -> str:
        return chr(ord("A") + idx)

    def _build_mc_question(self, prefix: str, endings: List[str]) -> str:
        """Build a multiple-choice question from endings."""
        option_lines = []
        for idx, ending in enumerate(endings):
            option_lines.append(f"{self._option_letter(idx)}. {self._normalize_ending(ending)}")
        options_block = "\n".join(option_lines)
        return f"{prefix}\n\n{options_block}\n\nAnswer with the option letter only."
        
    def convert_all(self, max_samples: int = 5000) -> List[ConversationalSample]:
        """转换所有数据。"""
        print("\n" + "="*60)
        print("Converting HellaSwag to Conversational Temporal Data")
        print("="*60)
        
        count = 0
        for sample in self.samples:
            if count >= max_samples:
                break
            
            context = sample.get('ctx', '')
            endings = sample.get('endings', [])
            label = sample.get('label', 0)
            activity = sample.get('activity_label', '')
            source_id = sample.get('ind', f'sample_{count}')
            
            if not context or not endings:
                continue
            
            correct_ending = endings[label] if label < len(endings) else endings[0]
            wrong_endings = [e for i, e in enumerate(endings) if i != label]
            
            # T2: 状态更新
            t2_samples = self._generate_t2_samples(context, endings, label, activity, source_id)
            self.converted.extend(t2_samples)
            
            # T3: 并发冲突
            t3_samples = self._generate_t3_samples(context, endings, label, activity, source_id)
            self.converted.extend(t3_samples)
            
            # T5: 反事实
            t5_samples = self._generate_t5_samples(context, correct_ending, wrong_endings, activity, source_id)
            self.converted.extend(t5_samples)
            
            count += 1
        
        print(f"\nTotal converted: {len(self.converted)} samples")
        return self.converted
    
    # =====================================================================
    # T2: 状态更新 (State Update)
    # =====================================================================
    
    def _generate_t2_samples(self, context: str, endings: List[str], label: int,
                            activity: str, source_id: str) -> List[ConversationalSample]:
        """生成T2状态更新样本。"""
        results = []
        correct_ending = endings[label] if label < len(endings) else endings[0]
        
        # T2-Convo-State: 状态推断
        conv = self._create_state_inference_conversation(
            context,
            correct_ending,
            endings,
            label,
            activity,
            source_id,
        )
        results.append(conv)
        
        # T2-Convo-Progressive: 动作进展
        conv = self._create_progressive_conversation(
            context,
            correct_ending,
            endings,
            label,
            activity,
            source_id,
        )
        results.append(conv)
        
        return results
    
    def _create_state_inference_conversation(self, context: str, correct_ending: str,
                                            endings: List[str], label: int,
                                            activity: str, source_id: str) -> ConversationalSample:
        """创建状态推断对话。"""
        conversation = []
        
        # 描述当前正在进行的动作
        conversation.append({
            "role": "user",
            "content": f"I'm currently {activity.lower()}."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Okay, so you're {activity.lower()}."
        })
        
        # 提供上下文细节
        context_clean = context.replace("[", "").replace("]", "").strip()
        if context_clean:
            conversation.append({
                "role": "user",
                "content": f"More specifically: {context_clean[:150]}..."
            })
        
        # 干扰
        conversation.append({
            "role": "user",
            "content": "By the way, I had coffee this morning."
        })
        conversation.append({
            "role": "assistant",
            "content": "I see."
        })
        
        # 核心问题：基于HellaSwag endings的多选推理
        question = self._build_mc_question(
            "Which ending is the most plausible next event in this activity?",
            endings,
        )
        
        # 从正确答案推断状态
        correct_ending_clean = self._normalize_ending(correct_ending)
        answer_text = self._option_letter(label)
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-State",
            context=context,
            conversation=conversation,
            query=question,
            answer=answer_text,
            state_info={
                "type": "state_inference",
                "activity": activity,
                "action_progress": "in_progress"
            },
            ground_truth={
                "current_state": "in_progress",
                "next_action": correct_ending_clean[:80],
                "correct_option": self._option_letter(label),
                "correct_option_index": label,
                "options": [self._normalize_ending(e) for e in endings],
            },
            difficulty="medium",
            source_id=f"hellaswag_t2_state_{source_id}"
        )
    
    def _create_progressive_conversation(self, context: str, correct_ending: str,
                                         endings: List[str], label: int,
                                         activity: str, source_id: str) -> ConversationalSample:
        """创建动作进展对话。"""
        conversation = []
        
        # 时间推进
        conversation.append({
            "role": "user",
            "content": f"I started {activity.lower()} a few minutes ago."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Got it, you began {activity.lower()}."
        })
        
        # 状态描述
        context_clean = context.replace("[", "").replace("]", "").strip()
        conversation.append({
            "role": "user",
            "content": f"{context_clean[:120]}..."
        })
        
        # 问进展
        conversation.append({
            "role": "user",
            "content": "What's my progress status?"
        })
        
        question = self._build_mc_question(
            "Given the context, which option best describes the next logical step?",
            endings,
        )
        answer_text = self._option_letter(label)
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Progressive",
            context=context,
            conversation=conversation,
            query=question,
            answer=answer_text,
            state_info={
                "type": "action_progressive",
                "activity": activity,
                "status": "in_progress"
            },
            ground_truth={
                "progress": "ongoing",
                "next_step": self._normalize_ending(correct_ending)[:80],
                "correct_option": self._option_letter(label),
                "correct_option_index": label,
                "options": [self._normalize_ending(e) for e in endings],
            },
            difficulty="easy",
            source_id=f"hellaswag_t2_prog_{source_id}"
        )
    
    # =====================================================================
    # T3: 并发冲突 (Conflict Detection)
    # =====================================================================
    
    def _generate_t3_samples(self, context: str, endings: List[str], label: int,
                             activity: str, source_id: str) -> List[ConversationalSample]:
        """生成T3并发冲突样本。"""
        results = []
        
        location = self.loader.classify_activity_location(activity)
        
        # T3-Convo-Conflict: 活动冲突
        conv = self._create_activity_conflict_conversation(context, endings, label, activity, location, source_id)
        results.append(conv)
        
        # T3-Convo-TimeConflict: 时间冲突
        conv = self._create_time_conflict_conversation(context, activity, source_id)
        results.append(conv)
        
        return results
    
    def _create_activity_conflict_conversation(self, context: str, endings: List[str],
                                               label: int, activity: str, location: Optional[str],
                                               source_id: str) -> ConversationalSample:
        """创建活动冲突对话。"""
        conversation = []
        
        # 正确的答案
        correct_ending = endings[label] if label < len(endings) else endings[0]
        
        # 第一个活动
        conversation.append({
            "role": "user",
            "content": f"I'm planning to {activity.lower()} this afternoon."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Okay, planning to {activity.lower()}."
        })
        
        # 根据地点添加冲突活动
        if location == "indoor":
            conflict_activity = random.choice(["go swimming outside", "work in the garden", "take a walk in the park"])
        elif location == "outdoor":
            conflict_activity = random.choice(["watch a movie at home", "cook dinner", "take a bath"])
        else:
            conflict_activity = random.choice(["attend a meeting downtown", "visit a friend"])
        
        conversation.append({
            "role": "user",
            "content": f"But I also scheduled to {conflict_activity} at the same time."
        })
        
        # 干扰
        conversation.append({
            "role": "user",
            "content": "By the way, do you know what day it is?"
        })
        conversation.append({
            "role": "assistant",
            "content": "I don't track days."
        })
        
        question = "Is there a potential conflict between these two activities?"
        answer_text = f"Yes - both activities require your attention at the same time and may be in different locations."
        
        return ConversationalSample(
            task="T3",
            sub_task="T3-Convo-Conflict",
            context=context,
            conversation=conversation,
            query=question,
            answer=answer_text,
            state_info={
                "type": "activity_conflict",
                "activity_1": activity,
                "activity_2": conflict_activity,
                "location": location
            },
            ground_truth={
                "has_conflict": True,
                "conflict_type": "location_time"
            },
            difficulty="medium",
            source_id=f"hellaswag_t3_conflict_{source_id}"
        )
    
    def _create_time_conflict_conversation(self, context: str, activity: str,
                                          source_id: str) -> ConversationalSample:
        """创建时间冲突对话。"""
        conversation = []
        
        # 设定时间场景
        start_time = random.choice(["2 PM", "3 PM", "10 AM", "11 AM"])
        duration = random.choice(["30 minutes", "1 hour", "2 hours"])
        
        conversation.append({
            "role": "user",
            "content": f"I scheduled {activity.lower()} for {start_time}."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Noted, {activity.lower()} at {start_time}."
        })
        
        conversation.append({
            "role": "user",
            "content": f"It will take about {duration}."
        })
        
        # 与另一个活动冲突
        another_time = random.choice(["2:30 PM", "3 PM", "11 AM", "2 PM"])
        conversation.append({
            "role": "user",
            "content": f"But I also have a meeting at {another_time}."
        })
        
        conversation.append({
            "role": "user",
            "content": "The weather is nice today. Anyway..."
        })
        conversation.append({
            "role": "assistant",
            "content": "I don't have weather information."
        })
        
        question = f"If {activity.lower()} takes {duration} starting at {start_time}, and I have another event at {another_time}, is there a conflict?"
        
        # 判断时间重叠 - 解析时间
        def parse_hour(time_str):
            # Handle formats like "2:30 PM", "3 PM", "11 AM"
            time_part = time_str.split()[0]  # Get the time part before AM/PM
            hour_part = time_part.split(':')[0]  # Get the hour part
            return int(hour_part)
        
        start_h = parse_hour(start_time)
        another_h = parse_hour(another_time)
        has_conflict = abs(start_h - another_h) < 2
        
        answer_text = "Yes, there's a time overlap." if has_conflict else "No, these times don't overlap."
        
        return ConversationalSample(
            task="T3",
            sub_task="T3-Convo-TimeConflict",
            context=context,
            conversation=conversation,
            query=question,
            answer=answer_text,
            state_info={
                "type": "time_conflict",
                "activity_1": f"{activity} at {start_time}",
                "activity_2": f"meeting at {another_time}",
                "duration": duration
            },
            ground_truth={
                "has_conflict": has_conflict,
                "time_overlap": abs(start_h - another_h)
            },
            difficulty="hard",
            source_id=f"hellaswag_t3_time_{source_id}"
        )
    
    # =====================================================================
    # T5: 反事实 (Counterfactual)
    # =====================================================================
    
    def _generate_t5_samples(self, context: str, correct_ending: str,
                             wrong_endings: List[str], activity: str,
                             source_id: str) -> List[ConversationalSample]:
        """生成T5反事实样本。"""
        results = []
        
        # T5-Convo-RuleReversal: 规则反转
        if wrong_endings:
            conv = self._create_rule_reversal_conversation(context, correct_ending, wrong_endings[0], activity, source_id)
            results.append(conv)
        
        # T5-Convo-WrongToEnding: 错误选项变正确
        if len(wrong_endings) >= 2:
            conv = self._create_wrong_to_right_conversation(context, correct_ending, wrong_endings, activity, source_id)
            results.append(conv)
        
        return results
    
    def _create_rule_reversal_conversation(self, context: str, correct_ending: str,
                                            wrong_ending: str, activity: str,
                                            source_id: str) -> ConversationalSample:
        """创建规则反转对话。"""
        conversation = []
        
        # 建立反事实世界
        conversation.append({
            "role": "user",
            "content": "In this hypothetical world, things work differently."
        })
        conversation.append({
            "role": "assistant",
            "content": "Okay, what's different?"
        })
        
        # 反事实规则
        conversation.append({
            "role": "user",
            "content": f"Normally, when {activity.lower()}, people continue with the logical next step."
        })
        conversation.append({
            "role": "user",
            "content": "But in THIS world, they do the OPPOSITE - they stop or do something completely unrelated."
        })
        
        # 提供上下文
        context_clean = context.replace("[", "").replace("]", "").strip()
        conversation.append({
            "role": "user",
            "content": f"Context: {context_clean[:100]}..."
        })
        
        conversation.append({
            "role": "user",
            "content": "What happens next in THIS hypothetical world?"
        })
        
        # 错误答案变成正确
        wrong_clean = wrong_ending.strip()
        if wrong_clean.startswith((",", "and", "then")):
            wrong_clean = wrong_clean[1:].strip()
        
        answer_text = f"In this world, they do: {wrong_clean[:80]}"
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-RuleReversal",
            context=context,
            conversation=conversation,
            query="In this world where physical rules are reversed, what happens next?",
            answer=answer_text,
            state_info={
                "type": "rule_reversal",
                "normal_outcome": correct_ending[:80],
                "counterfactual_outcome": wrong_clean[:80]
            },
            ground_truth={
                "is_counterfactual": True,
                "correct_in_normal_world": correct_ending[:80],
                "correct_in_counterfactual": wrong_clean[:80]
            },
            difficulty="hard",
            source_id=f"hellaswag_t5_rule_{source_id}"
        )
    
    def _create_wrong_to_right_conversation(self, context: str, correct_ending: str,
                                            wrong_endings: List[str], activity: str,
                                            source_id: str) -> ConversationalSample:
        """创建错误到正确对话。"""
        conversation = []
        
        # 选择一个原本错误的选项
        original_wrong = wrong_endings[0] if wrong_endings else "something else"
        another_wrong = wrong_endings[1] if len(wrong_endings) > 1 else original_wrong
        
        conversation.append({
            "role": "user",
            "content": f"I'm {activity.lower()}."
        })
        
        context_clean = context.replace("[", "").replace("]", "").strip()
        conversation.append({
            "role": "user",
            "content": f"{context_clean[:100]}..."
        })
        
        # 反事实规则
        conversation.append({
            "role": "user",
            "content": "In the REAL world, normally one would continue logically."
        })
        conversation.append({
            "role": "assistant",
            "content": "Understood, normal rules apply."
        })
        
        conversation.append({
            "role": "user",
            "content": "But in THIS scenario, the 'wrong' answer becomes 'right'."
        })
        conversation.append({
            "role": "user",
            "content": f"What would normally be wrong is: {original_wrong[:60]}..."
        })
        
        conversation.append({
            "role": "user",
            "content": "What should I do in THIS scenario?"
        })
        
        original_wrong_clean = original_wrong.strip()
        if original_wrong_clean.startswith((",", "and")):
            original_wrong_clean = original_wrong_clean[1:].strip()
        
        answer_text = f"Follow the 'wrong' action: {original_wrong_clean[:80]}"
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-WrongToRight",
            context=context,
            conversation=conversation,
            query="If the normally wrong answer becomes right, what should I do?",
            answer=answer_text,
            state_info={
                "type": "wrong_to_right",
                "normally_correct": correct_ending[:80],
                "normally_wrong": original_wrong_clean[:80]
            },
            ground_truth={
                "is_counterfactual": True,
                "normal_correct": correct_ending[:80],
                "counterfactual_correct": original_wrong_clean[:80]
            },
            difficulty="very_hard",
            source_id=f"hellaswag_t5_wrong_{source_id}"
        )


def main():
    """主函数。"""
    print("="*60)
    print("HellaSwag Conversational Temporal Data Converter")
    print("="*60)
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载数据
    loader = HellaSwagLoader(DATA_DIR)
    samples = loader.load("train")
    
    # 使用部分数据（太大）
    max_samples = 5000
    samples = samples[:max_samples]
    print(f"Using {len(samples)} samples for conversion")
    
    # 转换
    converter = HellaSwagConversationalConverter(samples)
    converted = converter.convert_all(max_samples=len(samples))
    
    # 保存
    output_file = OUTPUT_DIR / "hellaswag_conversational.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for sample in converted:
            f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
    
    print(f"\nSaved to: {output_file}")
    
    # 统计报告
    report = {
        "total_samples": len(converted),
        "task_distribution": {},
        "subtask_distribution": {},
        "difficulty_distribution": {}
    }
    
    for sample in converted:
        task = sample.task
        subtask = sample.sub_task
        diff = sample.difficulty
        
        report["task_distribution"][task] = report["task_distribution"].get(task, 0) + 1
        report["subtask_distribution"][subtask] = report["subtask_distribution"].get(subtask, 0) + 1
        report["difficulty_distribution"][diff] = report["difficulty_distribution"].get(diff, 0) + 1
    
    report_file = OUTPUT_DIR / "hellaswag_conversational_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("Conversion Summary")
    print("="*60)
    print(f"Total samples: {len(converted)}")
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