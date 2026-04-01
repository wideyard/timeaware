#!/usr/bin/env python3
"""
Choice-75 Temporal Awareness Data Converter - Conversational Only
===================================================================
将Choice-75（ProScript分支选择）数据转化为对话式时间感知评测数据。

核心特点：
- 脚本步骤间有强时间序（Chronological Order）
- branching提供二选一决策点
- scenario提供选择理由

任务映射：
- T1: 时间计算（为步骤分配时长）
- T2: 状态更新（步骤序列的状态追踪）
- T3: 冲突检测（选项时间冲突）
- T5: 反事实（改变选择理由）

作者：TemporalAware Team
"""

import json
import random
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Configuration
DATA_DIR = Path("data/choice-75/data/choice-75")
OUTPUT_DIR = Path("converted_data_v2")

# 步骤时长估计（分钟）
STEP_DURATION_ESTIMATES = {
    # 个人准备
    "shower": 15, "take a shower": 15, "bath": 20,
    "get ready": 10, "prepare": 10, "get dressed": 5,
    "wake up": 5, "breakfast": 15, "lunch": 30, "dinner": 45,
    
    # 出行相关
    "drive": 30, "walk": 15, "bus": 25, "car": 20,
    "park": 5, "park the car": 5,
    "go to": 20, "travel": 30, "commute": 25,
    
    # 购物相关
    "buy": 15, "purchase": 15, "shop": 45,
    "pay": 5, "checkout": 10,
    
    # 社交相关
    "call": 10, "meet": 30, "interview": 45,
    "apply": 15, "submit": 10,
    
    # 默认
    "default": 10
}


@dataclass
class ConversationalSample:
    """对话式时间感知评测数据样本。"""
    task: str  # T1, T2, T3, T5
    sub_task: str  # 细分任务
    goal: str  # 原始目标
    conversation: List[Dict[str, str]]  # 多轮对话
    query: str  # 最终问题
    answer: str  # 答案
    state_info: Optional[Dict[str, Any]] = None
    ground_truth: Optional[Dict[str, Any]] = None
    difficulty: str = "medium"
    source_id: Optional[str] = None


class Choice75Loader:
    """加载Choice-75数据集。"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.samples = []
        
    def load_all(self) -> List[Dict]:
        """加载所有数据。"""
        all_data = []
        
        # 加载train和dev
        for split in ['train', 'dev']:
            for subdir in ['verb_phrase_manual', 'verb_phrase_machine', 'user_profile']:
                split_dir = self.data_dir / subdir / split
                if split_dir.exists():
                    for file_path in split_dir.glob('*.json'):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                data['source_file'] = str(file_path)
                                all_data.append(data)
                        except Exception as e:
                            print(f"Error loading {file_path}: {e}")
        
        print(f"Loaded {len(all_data)} Choice-75 samples")
        return all_data
    
    def validate_sample(self, sample: Dict) -> bool:
        """验证样本是否完整。"""
        if not sample.get('goal'):
            return False
        if not sample.get('steps') or len(sample['steps']) < 2:
            return False
        bi = sample.get('branching_info', {})
        if not bi.get('branching_idx') and bi.get('branching_idx') != 0:
            return False
        if not bi.get('option 1') or not bi.get('option 2'):
            return False
        return True


class Choice75ConversationalConverter:
    """Choice-75对话式数据转换器。"""
    
    def __init__(self, samples: List[Dict]):
        self.samples = samples
        self.converted = []
        
    def convert_all(self) -> List[ConversationalSample]:
        """转换所有数据。"""
        print("\n" + "="*60)
        print("Converting Choice-75 to Conversational Temporal Data")
        print("="*60)
        
        for sample in self.samples:
            if not self._validate(sample):
                continue
                
            # T2: 状态更新
            t2_samples = self._generate_t2_samples(sample)
            self.converted.extend(t2_samples)
            
            # T3: 冲突检测
            t3_samples = self._generate_t3_samples(sample)
            self.converted.extend(t3_samples)
            
            # T1: 时间计算
            t1_samples = self._generate_t1_samples(sample)
            self.converted.extend(t1_samples)
            
            # T5: 反事实
            t5_samples = self._generate_t5_samples(sample)
            self.converted.extend(t5_samples)
        
        print(f"\nTotal converted: {len(self.converted)} samples")
        return self.converted
    
    def _validate(self, sample: Dict) -> bool:
        """验证样本。"""
        if not sample.get('goal'):
            return False
        if not sample.get('steps') or len(sample['steps']) < 3:
            return False
        bi = sample.get('branching_info', {})
        if bi.get('branching_idx') is None:
            return False
        if not bi.get('option 1') or not bi.get('option 2'):
            return False
        return True
    
    # =====================================================================
    # T2: 状态更新 (State Tracking)
    # =====================================================================
    
    def _generate_t2_samples(self, sample: Dict) -> List[ConversationalSample]:
        """生成T2状态更新样本。"""
        results = []
        
        goal = sample['goal']
        steps = sample['steps']
        branching_idx = sample['branching_info']['branching_idx']
        branching_step = sample['branching_info']['branching_step']
        
        # T2-Convo-Progressive: 步骤渐进对话
        if branching_idx >= 1:
            conv = self._create_progressive_conversation(goal, steps, branching_idx)
            results.append(conv)
        
        # T2-Convo-State: 状态推断
        if branching_idx >= 2:
            conv = self._create_state_inference_conversation(goal, steps, branching_idx)
            results.append(conv)
        
        # T2-Convo-Rollback: 状态回滚
        if branching_idx >= 2:
            conv = self._create_rollback_conversation(goal, steps, branching_idx)
            results.append(conv)
        
        # T2-Convo-Branch: 分支状态
        conv = self._create_branch_state_conversation(sample)
        results.append(conv)
        
        return results
    
    def _create_progressive_conversation(self, goal: str, steps: List[str], branch_idx: int) -> ConversationalSample:
        """创建步骤渐进对话。"""
        completed_steps = steps[:branch_idx]
        current_step = steps[branch_idx] if branch_idx < len(steps) else "unknown"
        remaining_steps = steps[branch_idx+1:] if branch_idx+1 < len(steps) else []
        
        conversation = []
        
        # 构建对话历史，逐步揭示步骤
        for i, step in enumerate(completed_steps[:3]):  # 最多显示3个已完成步骤
            conversation.append({
                "role": "user",
                "content": f"I already {step}."
            })
            conversation.append({
                "role": "assistant",
                "content": f"Got it, {step} is done."
            })
        
        # 插入干扰
        conversation.append({
            "role": "user",
            "content": "By the way, do you know what time it is?"
        })
        conversation.append({
            "role": "assistant",
            "content": "I don't have that information."
        })
        
        # 当前状态
        conversation.append({
            "role": "user",
            "content": f"Now I am {current_step}."
        })
        
        # 问题：下一步是什么
        question = f"What should I do after '{current_step}'?"
        answer = remaining_steps[0] if remaining_steps else "Complete the goal"
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Progressive",
            goal=goal,
            conversation=conversation,
            query=question,
            answer=answer,
            state_info={
                "type": "progressive_steps",
                "completed": completed_steps,
                "current": current_step,
                "remaining": remaining_steps
            },
            ground_truth={
                "next_step": answer,
                "current_index": branch_idx
            },
            difficulty="medium",
            source_id=f"choice75_t2_prog_{hash(goal)}"
        )
    
    def _create_state_inference_conversation(self, goal: str, steps: List[str], branch_idx: int) -> ConversationalSample:
        """创建状态推断对话。"""
        # 中间状态推断
        mid_idx = branch_idx // 2
        completed = steps[:mid_idx]
        current = steps[mid_idx]
        next_step = steps[mid_idx + 1] if mid_idx + 1 < len(steps) else "complete"
        
        conversation = []
        
        # 对话中逐步描述状态
        conversation.append({
            "role": "user",
            "content": f"My goal is to {goal}."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Okay, planning to {goal}."
        })
        
        for i, step in enumerate(completed[:2]):
            conversation.append({
                "role": "user",
                "content": f"I've {step}."
            })
        
        # 核心问题
        question = f"After '{current}', what am I doing?"
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-State",
            goal=goal,
            conversation=conversation,
            query=question,
            answer=current,
            state_info={
                "type": "state_inference",
                "state_history": completed
            },
            ground_truth={
                "current_state": current,
                "state_index": mid_idx
            },
            difficulty="hard",
            source_id=f"choice75_t2_state_{hash(goal)}"
        )
    
    def _create_rollback_conversation(self, goal: str, steps: List[str], branch_idx: int) -> ConversationalSample:
        """创建状态回滚对话。"""
        completed = steps[:branch_idx-1]
        previous_state = steps[branch_idx-2] if branch_idx >= 2 else steps[0]
        
        conversation = []
        
        # 从头开始描述
        conversation.append({
            "role": "user",
            "content": f"I want to {goal}."
        })
        
        for i, step in enumerate(steps[:branch_idx]):
            conversation.append({
                "role": "user",
                "content": f"I {step}."
            })
            if i < branch_idx - 1:
                conversation.append({
                    "role": "assistant",
                    "content": f"Step {i+1} completed."
                })
        
        # 问初始状态
        question = "What was my state at the very beginning?"
        answer = steps[0]
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Rollback",
            goal=goal,
            conversation=conversation,
            query=question,
            answer=answer,
            state_info={
                "type": "state_rollback",
                "all_steps": steps,
                "branch_point": branch_idx
            },
            ground_truth={
                "initial_state": answer,
                "final_branch_state": steps[branch_idx-1]
            },
            difficulty="hard",
            source_id=f"choice75_t2_roll_{hash(goal)}"
        )
    
    def _create_branch_state_conversation(self, sample: Dict) -> ConversationalSample:
        """创建分支状态对话。"""
        goal = sample['goal']
        steps = sample['steps']
        bi = sample['branching_info']
        
        opt1 = bi['option 1']
        opt2 = bi['option 2']
        branch_step = bi['branching_step']
        
        conversation = []
        
        # 描述到分支点
        conversation.append({
            "role": "user",
            "content": f"I'm trying to {goal}."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Okay, to {goal}."
        })
        
        # 描述已完成的步骤
        for step in steps[:bi['branching_idx']]:
            conversation.append({
                "role": "user",
                "content": f"I {step}."
            })
        
        # 核心问题：在当前状态下应该做什么
        question = f"I'm at '{branch_step}'. What should I do?"
        answer = f"Choose between: {opt1} OR {opt2}"
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Branch",
            goal=goal,
            conversation=conversation,
            query=question,
            answer=answer,
            state_info={
                "type": "branch_point",
                "branch_step": branch_step,
                "options": [opt1, opt2]
            },
            ground_truth={
                "branch_index": bi['branching_idx'],
                "valid_options": [opt1, opt2]
            },
            difficulty="medium",
            source_id=f"choice75_t2_branch_{hash(goal)}"
        )
    
    # =====================================================================
    # T3: 冲突检测 (Conflict Detection)
    # =====================================================================
    
    def _generate_t3_samples(self, sample: Dict) -> List[ConversationalSample]:
        """生成T3冲突检测样本。"""
        results = []
        
        goal = sample['goal']
        bi = sample['branching_info']
        scenarios = bi.get('freeform_ra', [])
        
        opt1 = bi['option 1']
        opt2 = bi['option 2']
        branch_step = bi['branching_step']
        
        # T3-Convo-Conflict: 从scenario构造冲突
        for scenario_data in scenarios[:2]:  # 每个样本最多2个scenario
            if len(scenario_data) >= 2:
                scenario = scenario_data[0]
                ground_truth = scenario_data[1]  # 1或2
                
                conv = self._create_conflict_conversation(
                    goal, branch_step, opt1, opt2, scenario, ground_truth
                )
                results.append(conv)
        
        # T3-Convo-TimeConflict: 时间冲突
        conv = self._create_time_conflict_conversation(sample)
        results.append(conv)
        
        return results
    
    def _create_conflict_conversation(self, goal: str, branch_step: str, 
                                      opt1: str, opt2: str, 
                                      scenario: str, ground_truth: int) -> ConversationalSample:
        """创建冲突检测对话。"""
        correct_option = opt1 if ground_truth == 1 else opt2
        other_option = opt2 if ground_truth == 1 else opt1
        
        conversation = []
        
        # 设置情境
        conversation.append({
            "role": "user",
            "content": f"I'm trying to {goal}."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Okay, {goal}."
        })
        
        # 提供背景信息
        conversation.append({
            "role": "user",
            "content": f"Here's my situation: {scenario}."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Noted: {scenario}."
        })
        
        # 插入干扰
        conversation.append({
            "role": "user",
            "content": "I saw a movie yesterday, it was great."
        })
        conversation.append({
            "role": "assistant",
            "content": "I see."
        })
        
        # 核心问题
        question = f"At the step '{branch_step}', should I choose: {opt1} or {opt2}?"
        
        return ConversationalSample(
            task="T3",
            sub_task="T3-Convo-Conflict",
            goal=goal,
            conversation=conversation,
            query=question,
            answer=f"Choose {correct_option} because {scenario}",
            state_info={
                "type": "scenario_conflict",
                "scenario": scenario,
                "options": [opt1, opt2]
            },
            ground_truth={
                "correct_option": ground_truth,
                "reasoning": scenario
            },
            difficulty="medium",
            source_id=f"choice75_t3_conflict_{hash(goal)}"
        )
    
    def _create_time_conflict_conversation(self, sample: Dict) -> ConversationalSample:
        """创建时间冲突对话。"""
        goal = sample['goal']
        steps = sample['steps']
        bi = sample['branching_info']
        
        opt1 = bi['option 1']
        opt2 = bi['option 2']
        branch_step = bi['branching_step']
        
        # 构造时间冲突
        conversation = []
        
        conversation.append({
            "role": "user",
            "content": f"I'm planning to {goal}."
        })
        
        # 描述分支前的步骤
        for step in steps[:bi['branching_idx']]:
            conversation.append({
                "role": "user",
                "content": f"I need to {step}."
            })
        
        # 设定时间冲突
        conversation.append({
            "role": "user",
            "content": f"At the step '{branch_step}', I have two options:"
        })
        conversation.append({
            "role": "user",
            "content": f"Option A: {opt1} (takes about 10 minutes)"
        })
        conversation.append({
            "role": "user",
            "content": f"Option B: {opt2} (takes about 30 minutes)"
        })
        
        # 设定时间约束
        conversation.append({
            "role": "user",
            "content": "But I need to finish everything within 1 hour from now."
        })
        
        question = "Which option should I choose considering the time constraint?"
        
        return ConversationalSample(
            task="T3",
            sub_task="T3-Convo-TimeConflict",
            goal=goal,
            conversation=conversation,
            query=question,
            answer=f"Choose the faster option based on time constraint",
            state_info={
                "type": "time_conflict",
                "options": [opt1, opt2],
                "remaining_steps": steps[bi['branching_idx']+1:]
            },
            ground_truth={
                "branch_step": branch_step,
                "options": [opt1, opt2]
            },
            difficulty="hard",
            source_id=f"choice75_t3_time_{hash(goal)}"
        )
    
    # =====================================================================
    # T1: 时间计算 (Time Calculation)
    # =====================================================================
    
    def _generate_t1_samples(self, sample: Dict) -> List[ConversationalSample]:
        """生成T1时间计算样本。"""
        results = []
        
        goal = sample['goal']
        steps = sample['steps']
        
        # T1-Convo-Duration: 计算总时长
        conv = self._create_duration_conversation(goal, steps)
        results.append(conv)
        
        # T1-Convo-Parallel: 并行任务时间
        conv = self._create_parallel_conversation(goal, steps)
        results.append(conv)
        
        return results
    
    def _estimate_step_duration(self, step: str) -> int:
        """估算步骤时长（分钟）。"""
        step_lower = step.lower()
        for keyword, duration in STEP_DURATION_ESTIMATES.items():
            if keyword in step_lower:
                return duration
        return STEP_DURATION_ESTIMATES['default']
    
    def _create_duration_conversation(self, goal: str, steps: List[str]) -> ConversationalSample:
        """创建时长计算对话。"""
        conversation = []
        
        # 计算每个步骤的时长
        step_durations = []
        for step in steps:
            duration = self._estimate_step_duration(step)
            step_durations.append((step, duration))
        
        total_duration = sum(d for _, d in step_durations)
        
        conversation.append({
            "role": "user",
            "content": f"I want to {goal}."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Okay, {goal}."
        })
        
        # 列出步骤和时长
        for step, duration in step_durations[:4]:  # 最多列4个
            conversation.append({
                "role": "user",
                "content": f"Step: {step} ({duration} minutes)."
            })
        
        remaining_duration = sum(d for _, d in step_durations[4:])
        if remaining_duration > 0:
            conversation.append({
                "role": "user",
                "content": f"And some remaining steps."
            })
        
        # 干扰
        conversation.append({
            "role": "user",
            "content": "I had coffee this morning."
        })
        conversation.append({
            "role": "assistant",
            "content": "I see."
        })
        
        question = "If I start now, approximately how long will it take to complete everything?"
        answer = f"About {total_duration} minutes"
        
        return ConversationalSample(
            task="T1",
            sub_task="T1-Convo-Duration",
            goal=goal,
            conversation=conversation,
            query=question,
            answer=answer,
            state_info={
                "type": "duration_calculation",
                "step_durations": step_durations
            },
            ground_truth={
                "total_minutes": total_duration
            },
            difficulty="medium",
            source_id=f"choice75_t1_dur_{hash(goal)}"
        )
    
    def _create_parallel_conversation(self, goal: str, steps: List[str]) -> ConversationalSample:
        """创建并行任务时间对话。"""
        conversation = []
        
        if len(steps) < 3:
            # 不足够的步骤
            return None
        
        # 选择中间两个步骤作为并行示例
        parallel_steps = steps[1:3]
        d1 = self._estimate_step_duration(parallel_steps[0])
        d2 = self._estimate_step_duration(parallel_steps[1])
        non_parallel_time = d1 + d2
        parallel_time = max(d1, d2)
        
        conversation.append({
            "role": "user",
            "content": f"I'm planning to {goal}."
        })
        
        for i, step in enumerate(steps[:3]):
            conversation.append({
                "role": "user",
                "content": f"I need to: {step}."
            })
        
        conversation.append({
            "role": "user",
            "content": f"Wait, can I do '{parallel_steps[0]}' and '{parallel_steps[1]}' at the same time?"
        })
        conversation.append({
            "role": "assistant",
            "content": "If they can be done in parallel..."
        })
        
        question = f"If '{parallel_steps[0]}' ({d1}min) and '{parallel_steps[1]}' ({d2}min) can be done in parallel, how much time do they take together?"
        answer = f"{parallel_time} minutes (parallel: {max(d1, d2)} min)"
        
        return ConversationalSample(
            task="T1",
            sub_task="T1-Convo-Parallel",
            goal=goal,
            conversation=conversation,
            query=question,
            answer=answer,
            state_info={
                "type": "parallel_time",
                "parallel_steps": parallel_steps,
                "durations": [d1, d2]
            },
            ground_truth={
                "sequential_time": non_parallel_time,
                "parallel_time": parallel_time
            },
            difficulty="hard",
            source_id=f"choice75_t1_par_{hash(goal)}"
        )
    
    # =====================================================================
    # T5: 反事实 (Counterfactual)
    # =====================================================================
    
    def _generate_t5_samples(self, sample: Dict) -> List[ConversationalSample]:
        """生成T5反事实样本。"""
        results = []
        
        goal = sample['goal']
        bi = sample['branching_info']
        scenarios = bi.get('freeform_ra', [])
        
        opt1 = bi['option 1']
        opt2 = bi['option 2']
        
        # T5-Convo-Counterfactual: 颠覆选择理由
        for scenario_data in scenarios[:2]:
            if len(scenario_data) >= 2:
                scenario = scenario_data[0]
                ground_truth = scenario_data[1]
                
                conv = self._create_counterfactual_conversation(
                    goal, bi['branching_step'], opt1, opt2, scenario, ground_truth
                )
                if conv:
                    results.append(conv)
        
        # T5-Convo-RuleChange: 规则改变
        conv = self._create_rule_change_conversation(sample)
        if conv:
            results.append(conv)
        
        return results
    
    def _create_counterfactual_conversation(self, goal: str, branch_step: str,
                                             opt1: str, opt2: str,
                                             scenario: str, ground_truth: int) -> Optional[ConversationalSample]:
        """创建反事实对话。"""
        correct_option = opt1 if ground_truth == 1 else opt2
        wrong_option = opt2 if ground_truth == 1 else opt1
        
        conversation = []
        
        # 正常情境
        conversation.append({
            "role": "user",
            "content": f"I'm {goal}."
        })
        conversation.append({
            "role": "user",
            "content": f"At '{branch_step}', I have options: {opt1} or {opt2}."
        })
        
        # 正常规则
        conversation.append({
            "role": "user",
            "content": f"Given that {scenario}, I should choose: {correct_option}."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Understood. {scenario} leads to {correct_option}."
        })
        
        # 反事实规则
        conversation.append({
            "role": "user",
            "content": f"But wait! What if the opposite was true?"
        })
        conversation.append({
            "role": "user",
            "content": f"Let's say: NOT ({scenario})."
        })
        
        question = f"In this opposite scenario, which option should I choose?"
        answer = f"Choose {wrong_option} (because the reasoning is reversed)"
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-Counterfactual",
            goal=goal,
            conversation=conversation,
            query=question,
            answer=answer,
            state_info={
                "type": "counterfactual_reasoning",
                "original_scenario": scenario,
                "original_choice": correct_option
            },
            ground_truth={
                "counterfactual_choice": wrong_option,
                "reasoning_reversed": True
            },
            difficulty="hard",
            source_id=f"choice75_t5_cf_{hash(goal)}"
        )
    
    def _create_rule_change_conversation(self, sample: Dict) -> Optional[ConversationalSample]:
        """创建规则改变对话。"""
        goal = sample['goal']
        bi = sample['branching_info']
        steps = sample['steps']
        
        opt1 = bi['option 1']
        opt2 = bi['option 2']
        
        # 获取原本应该选择的选项（从scenario推断）
        scenarios = bi.get('freeform_ra', [])
        if not scenarios or len(scenarios[0]) < 2:
            original_choice = opt1
        else:
            ground_truth = scenarios[0][1]
            original_choice = opt1 if ground_truth == 1 else opt2
        
        conversation = []
        
        conversation.append({
            "role": "user",
            "content": f"Let's imagine a hypothetical world."
        })
        conversation.append({
            "role": "assistant",
            "content": "Okay, what are the rules of this world?"
        })
        
        # 设定反事实规则
        conversation.append({
            "role": "user",
            "content": f"In this world, {opt1} takes 2 hours and is very expensive."
        })
        conversation.append({
            "role": "user",
            "content": f"But {opt2} is quick and free."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Noted: {opt2} is better in this world."
        })
        
        # 现实对比
        conversation.append({
            "role": "user",
            "content": f"In reality, people usually choose {original_choice} for this situation."
        })
        conversation.append({
            "role": "assistant",
            "content": f"In reality: {original_choice}."
        })
        
        question = f"In the HYPOTHETICAL world, which should I choose?"
        answer = f"Choose {opt2} (quick and free in the hypothetical world)"
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-RuleChange",
            goal=goal,
            conversation=conversation,
            query=question,
            answer=answer,
            state_info={
                "type": "rule_change",
                "hypothetical_rules": {
                    opt1: "slow and expensive",
                    opt2: "quick and free"
                }
            },
            ground_truth={
                "hypothetical_choice": opt2,
                "real_choice": original_choice
            },
            difficulty="very_hard",
            source_id=f"choice75_t5_rule_{hash(goal)}"
        )


def main():
    """主函数。"""
    print("="*60)
    print("Choice-75 Conversational Temporal Data Converter")
    print("="*60)
    
    # 加载数据
    loader = Choice75Loader(DATA_DIR)
    samples = loader.load_all()
    
    # 过滤有效样本
    valid_samples = [s for s in samples if loader.validate_sample(s)]
    print(f"Valid samples after filtering: {len(valid_samples)}")
    
    # 转换
    converter = Choice75ConversationalConverter(valid_samples)
    converted = converter.convert_all()
    
    # 保存
    output_file = OUTPUT_DIR / "choice75_conversational.jsonl"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
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
    
    report_file = OUTPUT_DIR / "choice75_conversational_report.json"
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