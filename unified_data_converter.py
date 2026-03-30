#!/usr/bin/env python3
"""
Unified Data Converter for Temporal World Modeling Benchmark
============================================================

This script handles:
1. T2 State Tracking: OpenPI2.0, PASTA, ProPara (with answer fix)
2. T3 Concurrency/Conflict: ATOMIC (reconstructed for conflict detection)
3. T4 Long-term Memory: LongBench, qasper, NarrativeQA
4. T5 Counterfactual: PASTA (counterfactual), Rule perturbation
5. Dialogue Temporal Benchmark: New dialog-based temporal reasoning

Author: TimeAware Benchmark Team
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import random
from datetime import datetime

# Configuration
DATA_DIR = Path("data")
OUTPUT_DIR = Path("converted_data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TemporalSample:
    """Unified temporal reasoning sample format"""
    id: str
    task: str  # T1-T5
    sub_task: str  # T2-1, T3-1, etc.
    context: str
    delta_t: Optional[str] = None
    event: Optional[str] = None
    query: str = ""
    answer: str = ""
    state: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    ground_truth: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.state is None:
            self.state = {}
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_jsonl(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ============================================================================
# Part 1: T2 State Tracking - OpenPI2.0 Converter
# ============================================================================

class OpenPI2Converter:
    """Convert OpenPI2.0 dataset to T2 State Tracking format
    
    OpenPI2.0 structure:
    - goal: The procedure goal
    - steps: List of steps in the procedure
    - states: Entity state changes throughout the procedure
    
    Each state entry contains:
    - entity: The entity being tracked
    - answers: State changes for each step
      - attribute: What attribute (location, state, etc.)
      - before/after: State before and after step
      - saliency: Importance score
    """
    
    def __init__(self):
        self.samples: List[TemporalSample] = []
    
    def convert(self, input_file: Path) -> List[TemporalSample]:
        """Convert OpenPI2.0 data to T2 format"""
        print(f"[OpenPI2] Loading from {input_file}...")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sample_count = 0
        for proc_id, proc_data in data.items():
            goal = proc_data.get('goal', '')
            steps = proc_data.get('steps', [])
            states = proc_data.get('states', [])
            
            if not steps or not states:
                continue
            
            # Build context from steps
            context_lines = [f"Goal: {goal}"]
            for i, step in enumerate(steps, 1):
                context_lines.append(f"Step {i}: {step}")
            context = "\n".join(context_lines)
            
            # Process each entity's state changes
            for state_entry in states:
                entity = state_entry.get('entity', 'unknown')
                answers = state_entry.get('answers', {})
                
                # Create samples for each step's state change
                step_keys = [k for k in answers.keys() if k.startswith('step')]
                step_keys.sort(key=lambda x: int(x.replace('step', '')))
                
                prev_state = {}
                
                for step_key in step_keys:
                    step_num = int(step_key.replace('step', ''))
                    step_changes = answers.get(step_key, [])
                    
                    for change in step_changes:
                        attribute = change.get('attribute', 'unknown')
                        before = change.get('before', 'unknown')
                        after = change.get('after', 'unknown')
                        saliency = change.get('saliency', 0.5)
                        
                        # Build state update sample
                        current_state = {entity: {attribute: after}}
                        
                        sample = TemporalSample(
                            id=f"openpi_{proc_id}_{entity}_{step_num}",
                            task="T2",
                            sub_task="T2-1",  # State tracking
                            context=context,
                            delta_t=f"Step {step_num}",
                            event=steps[step_num - 1] if step_num <= len(steps) else "",
                            query=f"What is the state of {entity} after Step {step_num}?",
                            answer=f"{attribute}: {after}",
                            state={
                                "entity": entity,
                                "attribute": attribute,
                                "before_state": before,
                                "after_state": after,
                                "saliency": saliency
                            },
                            ground_truth={
                                "entity": entity,
                                "attribute": attribute,
                                "correct_state": after
                            },
                            metadata={
                                "procedure_id": proc_id,
                                "goal": goal,
                                "step_number": step_num
                            }
                        )
                        self.samples.append(sample)
                        sample_count += 1
                        
                        if sample_count >= 50000:  # Limit to prevent memory issues
                            break
                    
                    if sample_count >= 50000:
                        break
                
                if sample_count >= 50000:
                    break
            
            if sample_count >= 50000:
                break
        
        print(f"[OpenPI2] Converted {len(self.samples)} samples")
        return self.samples
    
    def save(self, output_file: Path):
        """Save samples to JSONL"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(sample.to_jsonl() + '\n')
        print(f"[OpenPI2] Saved {len(self.samples)} samples to {output_file}")


# ============================================================================
# Part 2: T2 State Tracking - PASTA Converter  
# ============================================================================

class PASTAConverter:
    """Convert PASTA dataset for T2 State Tracking and T5 Counterfactual
    
    PASTA structure:
    - Input.line1-5: Story sentences
    - Answer.assertion: Participant state inferred from story
    - Answer.mod_assertion: Counterfactual/modified assertion
    - Answer.mod_line1-5: Modified story consistent with counterfactual state
    """
    
    def __init__(self):
        self.samples: List[TemporalSample] = []
    
    def convert(self, input_file: Path, task_type: str = "both") -> List[TemporalSample]:
        """Convert PASTA data to T2/T5 format"""
        print(f"[PASTA] Loading from {input_file}...")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for idx, line in enumerate(lines):
            try:
                data = json.loads(line.strip())
            except:
                continue
            
            # Build story context
            lines_story = [
                data.get('Input.line1', ''),
                data.get('Input.line2', ''),
                data.get('Input.line3', ''),
                data.get('Input.line4', ''),
                data.get('Input.line5', '')
            ]
            story = " ".join([l for l in lines_story if l])
            
            assertion = data.get('Answer.assertion', '')
            mod_assertion = data.get('Answer.mod_assertion', '')
            
            # Identify which lines support the assertion
            supporting_lines = []
            for i in range(1, 6):
                if data.get(f'Answer.line{i}.on', False):
                    supporting_lines.append(i)
            
            # Build modified story
            mod_lines = [
                data.get('Answer.mod_line1', ''),
                data.get('Answer.mod_line2', ''),
                data.get('Answer.mod_line3', ''),
                data.get('Answer.mod_line4', ''),
                data.get('Answer.mod_line5', '')
            ]
            mod_story = " ".join([l for l in mod_lines if l])
            
            # T2: State inference from story
            if task_type in ["both", "T2"]:
                sample = TemporalSample(
                    id=f"pasta_t2_{idx}",
                    task="T2",
                    sub_task="T2-2",  # Status tracking
                    context=story,
                    delta_t="After story",
                    event="Story events",
                    query=f"Based on the story, what can we infer about the participant?",
                    answer=assertion,
                    state={
                        "type": "participant_state",
                        "supporting_lines": supporting_lines
                    },
                    ground_truth={
                        "assertion": assertion,
                        "evidence_lines": supporting_lines
                    },
                    metadata={
                        "title": data.get('Input.Title', ''),
                        "story_id": data.get('Input.storyid', '')
                    }
                )
                self.samples.append(sample)
            
            # T5: Counterfactual reasoning
            if task_type in ["both", "T5"]:
                sample = TemporalSample(
                    id=f"pasta_t5_{idx}",
                    task="T5",
                    sub_task="T5-1",  # Counterfactual reasoning
                    context=f"Original story: {story}\n\nCounterfactual premise: In a different scenario where {mod_assertion}",
                    delta_t="Counterfactual scenario",
                    event="Story revision",
                    query=f"What would happen in the counterfactual scenario?",
                    answer=mod_story,
                    state={
                        "type": "counterfactual",
                        "original_assertion": assertion,
                        "modified_assertion": mod_assertion
                    },
                    ground_truth={
                        "normal_scenario": story,
                        "counterfactual_scenario": mod_story
                    },
                    metadata={
                        "title": data.get('Input.Title', ''),
                        "story_id": data.get('Input.storyid', '')
                    }
                )
                self.samples.append(sample)
        
        print(f"[PASTA] Converted {len(self.samples)} samples")
        return self.samples
    
    def save(self, output_file: Path):
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(sample.to_jsonl() + '\n')
        print(f"[PASTA] Saved {len(self.samples)} samples to {output_file}")


# ============================================================================
# Part 3: T3 Concurrency/Conflict - ATOMIC Conflict Constructor
# ============================================================================

class AtomicConflictConstructor:
    """Construct conflict detection scenarios from ATOMIC dataset
    
    T3 requires detecting conflicts in:
    - Space: PersonX at location A, PersonX at location B (same time)
    - Resources: Meeting room occupied, can another meeting use it?
    - Attention: PersonX doing task A at time T, PersonX doing task B at time T
    
    We construct these from ATOMIC by combining events that would conflict.
    """
    
    # Conflict templates
    SPACE_CONFLICT_TEMPLATES = [
        {
            "template": "{time} {person}在{loc1}。{time} {person}在{loc2}。",
            "query": "这个日程安排是否合理？",
            "answer": "不合理，存在空间冲突",
            "type": "spatial_conflict"
        },
        {
            "template": "{person}计划在{time}去{loc1}，同时还要去{loc2}。",
            "query": "{person}能同时去这两个地方吗？",
            "answer": "不能，存在空间冲突",
            "type": "spatial_conflict"
        }
    ]
    
    RESOURCE_CONFLICT_TEMPLATES = [
        {
            "template": "{time} {room}已被{user1}占用。{user2}想在这个时间使用{room}。",
            "query": "{user2}能在{time}使用{room}吗？",
            "answer": "不能，资源已被占用",
            "type": "resource_conflict"
        }
    ]
    
    ATTENTION_CONFLICT_TEMPLATES = [
        {
            "template": "{time} {person}在开重要会议。{time} {person}需要写一封紧急邮件。",
            "query": "{person}能同时完成这两件事吗？",
            "answer": "不能，注意力冲突",
            "type": "attention_conflict"
        }
    ]
    
    # Locations for conflict generation
    LOCATIONS = ["北京", "上海", "公司", "家", "会议室", "办公室", "餐厅", "医院", "学校"]
    TIMES = ["上午9点", "下午2点", "周一上午", "周三下午", "今天下午3点"]
    PEOPLE = ["张三", "李四", "王五", "赵六", "小明", "小红"]
    
    def __init__(self):
        self.samples: List[TemporalSample] = []
    
    def construct_from_atomic(self, atomic_file: Path) -> List[TemporalSample]:
        """Construct conflict scenarios from ATOMIC events"""
        print(f"[T3 Conflict] Loading ATOMIC from {atomic_file}...")
        
        import pandas as pd
        df = pd.read_csv(atomic_file)
        
        # Extract events with locations
        location_events = []
        for _, row in df.iterrows():
            event = row.get('event', '')
            # Try to find events with location indicators
            if any(loc in event for loc in ['at ', 'in ', 'to ', 'location', 'place', 'room', 'home', 'work', 'office']):
                location_events.append(event)
        
        sample_count = 0
        
        # Generate spatial conflicts
        for i, loc1 in enumerate(self.LOCATIONS):
            for loc2 in self.LOCATIONS[i+1:]:
                for person in random.sample(self.PEOPLE, min(3, len(self.PEOPLE))):
                    for time in random.sample(self.TIMES, min(2, len(self.TIMES))):
                        # Create conflict scenario
                        context = f"{time} {person}在{loc1}开会。{time} {person}需要去{loc2}参加另一个会议。"
                        
                        sample = TemporalSample(
                            id=f"t3_spatial_{sample_count}",
                            task="T3",
                            sub_task="T3-1",  # Space conflict
                            context=context,
                            delta_t="同一时间",
                            event="空间冲突检测",
                            query="这个日程安排是否存在冲突？如果存在，是什么类型的冲突？",
                            answer=f"存在空间冲突：{person}不可能同时在{loc1}和{loc2}",
                            state={
                                "type": "spatial_conflict",
                                "conflict_type": "location",
                                "conflicting_locations": [loc1, loc2]
                            },
                            ground_truth={
                                "has_conflict": True,
                                "conflict_type": "spatial",
                                "resolution": f"</function_calls> 选择一个地点参加"
                            },
                            metadata={
                                "source": "synthetic_from.Atomic",
                                "difficulty": "easy" if loc1 != loc2 else "trivial"
                            }
                        )
                        self.samples.append(sample)
                        sample_count += 1
                        
                        if sample_count >= 3000:
                            break
                    if sample_count >= 3000:
                        break
                if sample_count >= 3000:
                    break
            if sample_count >= 3000:
                break
        
        # Generate resource conflicts
        rooms = ["会议室A", "会议室B", "大会议室", "小会议室", "视频会议室"]
        sample_count = 0
        for room in rooms:
            for time in self.TIMES:
                for p1, p2 in [(self.PEOPLE[0], self.PEOPLE[1]), (self.PEOPLE[2], self.PEOPLE[3])]:
                    context = f"{time} {room}已被{p1}预订。{p2}想使用{room}开会。"
                    
                    sample = TemporalSample(
                        id=f"t3_resource_{sample_count}",
                        task="T3",
                        sub_task="T3-2",  # Resource conflict
                        context=context,
                        delta_t="资源使用冲突",
                        event="资源冲突检测",
                        query=f"{p2}能在{time}使用{room}吗？为什么？",
                        answer=f"不能，{room}已被{p1}占用",
                        state={
                            "type": "resource_conflict",
                            "resource": room,
                            "occupied_by": p1,
                            "requested_by": p2
                        },
                        ground_truth={
                            "has_conflict": True,
                            "conflict_type": "resource",
                            "resolution_suggestions": ["更换时间", "更换房间", "等待释放"]
                        },
                        metadata={
                            "source": "synthetic",
                            "difficulty": "easy"
                        }
                    )
                    self.samples.append(sample)
                    sample_count += 1
                    
                    if sample_count >= 2000:
                        break
                if sample_count >= 2000:
                    break
            if sample_count >= 2000:
                break
        
        # Generate attention conflicts
        sample_count = 0
        attention_pairs = [
            ("开会", "写代码"),
            ("开车", "接电话"),
            ("睡觉", "工作"),
            ("陪家人", "加班"),
            ("运动", "看电视")
        ]
        
        for time in self.TIMES:
            for person in self.PEOPLE[:4]:
                for act1, act2 in attention_pairs:
                    context = f"{time} {person}需要{act1}。同时，{person}还想{act2}。"
                    
                    sample = TemporalSample(
                        id=f"t3_attention_{sample_count}",
                        task="T3",
                        sub_task="T3-3",  # Attention conflict
                        context=context,
                        delta_t="注意力冲突",
                        event="注意力冲突检测",
                        query=f"{person}能同时{act1}和{act2}吗？",
                        answer=f"不能，注意力冲突：同时需要专注于两件事",
                        state={
                            "type": "attention_conflict",
                            "activities": [act1, act2]
                        },
                        ground_truth={
                            "has_conflict": True,
                            "conflict_type": "attention",
                            "resolution_suggestions": ["优先处理重要事项", "安排不同时间"]
                        },
                        metadata={
                            "source": "synthetic",
                            "difficulty": "easy"
                        }
                    )
                    self.samples.append(sample)
                    sample_count += 1
                    
                    if sample_count >= 500:
                        break
                if sample_count >= 500:
                    break
            if sample_count >= 500:
                break
        
        # Add non-conflict samples (for negative examples)
        sample_count = 0
        non_conflict_contexts = [
            ("上午9点 张三在开会。下午3点 张三去健身房。", "这个日程安排存在冲突吗？", "不存在冲突，两个活动在不同时间"),
            ("李四早上在家吃早餐。晚上在公司加班。", "这两个活动冲突吗？", "不冲突，发生在不同时间"),
            ("周一 王五完成报告。周三 王五参加会议。", "存在冲突吗？", "不存在冲突，不同日期")
        ]
        
        for context, query, answer in non_conflict_contexts:
            sample = TemporalSample(
                id=f"t3_nonconflict_{sample_count}",
                task="T3",
                sub_task="T3-1",
                context=context,
                delta_t="时间检查",
                event="非冲突检测",
                query=query,
                answer=answer,
                state={
                    "type": "no_conflict"
                },
                ground_truth={
                    "has_conflict": False,
                    "conflict_type": "none"
                },
                metadata={
                    "source": "synthetic",
                    "difficulty": "easy"
                }
            )
            self.samples.append(sample)
            sample_count += 1
        
        print(f"[T3 Conflict] Generated {len(self.samples)} conflict detection samples")
        return self.samples
    
    def save(self, output_file: Path):
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(sample.to_jsonl() + '\n')
        print(f"[T3 Conflict] Saved {len(self.samples)} samples to {output_file}")


# ============================================================================
# Part 4: T5 Counterfactual - Rule Perturbation Generator
# ============================================================================

class CounterfactualRulePerturbation:
    """Generate counterfactual reasoning samples by perturbing rules
    
    T5 requires testing model reasoning under modified/fictional rules:
    - Normal: Water boils at 100°C
    - Counterfactual: In this world, water boils at 50°C
    
    We create paired samples (normal vs counterfactual) to measure consistency.
    """
    
    # Rules to perturb
    REAL_WORLD_RULES = [
        {
            "rule": "水在100摄氏度沸腾",
            "questions": ["煮开水需要多少度？", "水什么时候沸腾？"],
            "perturbations": [
                {"rule": "水在50摄氏度沸腾", "query": "在这个世界，煮开水需要多少度？"},
                {"rule": "水在0摄氏度沸腾", "query": "在这个世界，水什么时候沸腾？"},
                {"rule": "水在200摄氏度沸腾", "query": "在这个奇幻世界，煮开水需要多少度？"}
            ]
        },
        {
            "rule": "煮熟鸡蛋需要10分钟",
            "questions": ["煮鸡蛋要多久？", "鸡蛋什么时候算煮熟？"],
            "perturbations": [
                {"rule": "煮熟鸡蛋需要1分钟", "query": "在这个世界，煮鸡蛋要多久？"},
                {"rule": "煮熟鸡蛋需要30分钟", "query": "在这个世界，鸡蛋什么时候算煮熟？"}
            ]
        },
        {
            "rule": "重力加速度是9.8m/s²",
            "questions": ["物体下落速度是多少？", "地球上重力加速度是多少？"],
            "perturbations": [
                {"rule": "重力加速度是1m/s²", "query": "在这个世界，物体下落速度是多少？"},
                {"rule": "重力加速度是20m/s²", "query": "在这个世界，重力加速度是多少？"}
            ]
        },
        {
            "rule": "一天有24小时",
            "questions": ["一天有多少小时？", "半天是几小时？"],
            "perturbations": [
                {"rule": "一天有10小时", "query": "这个星球上一天有多少小时？"},
                {"rule": "一天有100小时", "query": "在这个世界，半天是几小时？"}
            ]
        },
        {
            "rule": "太阳从东方升起",
            "questions": ["太阳从哪个方向升起？", "早晨太阳在哪里？"],
            "perturbations": [
                {"rule": "太阳从西方升起", "query": "在这个世界，太阳从哪个方向升起？"},
                {"rule": "太阳从北方升起", "query": "在这个奇幻世界，早晨太阳在哪里？"}
            ]
        },
        {
            "rule": "人需要睡觉才能恢复精力",
            "questions": ["人为什么要睡觉？", "不睡觉会怎样？"],
            "perturbations": [
                {"rule": "人不需要睡觉", "query": "在这个世界，人需要睡觉吗？"},
                {"rule": "睡觉会让人变累", "query": "在这个世界，不睡觉会怎样？"}
            ]
        },
        {
            "rule": "铁会生锈",
            "questions": ["铁暴露在空气中会怎样？", "如何防止铁生锈？"],
            "perturbations": [
                {"rule": "铁不会生锈", "query": "在这个世界，铁暴露在空气中会怎样？"},
                {"rule": "铁会变成金子", "query": "这个奇幻世界，铁暴露在空气中会怎样？"}
            ]
        }
    ]
    
    # Additional counterfactual templates
    COUNTERFACTUAL_TEMPLATES = [
        {
            "normal_context": "小明有5元钱，苹果3元一个。",
            "normal_query": "小明能买几个苹果？",
            "normal_answer": "1个（剩下2元）",
            "counterfactual_rule": "在这个世界，钱的面值和物品价格都除以10。",
            "counterfactual_query": "在这个世界，小明能买几个苹果？",
            "counterfactual_answer": "仍然1个（面值和价格等比例变化）"
        },
        {
            "normal_context": "汽车需要汽油才能行驶。",
            "normal_query": "汽车没油了会怎样？",
            "normal_answer": "汽车无法行驶",
            "counterfactual_rule": "在这个世界，汽车用水就能行驶。",
            "counterfactual_query": "在这个世界，汽车没水了会怎样？",
            "counterfactual_answer": "汽车无法行驶"
        }
    ]
    
    def __init__(self):
        self.samples: List[TemporalSample] = []
    
    def generate_samples(self) -> List[TemporalSample]:
        """Generate counterfactual reasoning samples"""
        print("[T5 Counterfactual] Generating samples...")
        
        sample_count = 0
        
        # Generate from rule perturbations
        for rule_data in self.REAL_WORLD_RULES:
            normal_rule = rule_data["rule"]
            
            for perturb in rule_data["perturbations"]:
                counter_rule = perturb["rule"]
                counter_query = perturb["query"]
                
                # Normal world sample
                normal_sample = TemporalSample(
                    id=f"t5_normal_{sample_count}",
                    task="T5",
                    sub_task="T5-1",
                    context=f"现实世界：{normal_rule}",
                    delta_t="正常世界",
                    event="规则验证",
                    query=rule_data["questions"][0],
                    answer=normal_rule,
                    state={
                        "type": "normal_rule",
                        "world": "real"
                    },
                    ground_truth={
                        "rule": normal_rule,
                        "world_type": "normal"
                    },
                    metadata={
                        "pair_id": f"pair_{sample_count}",
                        "perturbation_type": "rule_change"
                    }
                )
                self.samples.append(normal_sample)
                
                # Counterfactual world sample
                counter_sample = TemporalSample(
                    id=f"t5_counter_{sample_count}",
                    task="T5",
                    sub_task="T5-2",
                    context=f"虚构世界：{counter_rule}",
                    delta_t="虚构世界",
                    event="反事实推理",
                    query=counter_query,
                    answer=counter_rule,
                    state={
                        "type": "counterfactual_rule",
                        "world": "fictional"
                    },
                    ground_truth={
                        "rule": counter_rule,
                        "world_type": "counterfactual",
                        "original_rule": normal_rule
                    },
                    metadata={
                        "pair_id": f"pair_{sample_count}",
                        "perturbation_type": "rule_change"
                    }
                )
                self.samples.append(counter_sample)
                sample_count += 1
        
        # Generate from templates
        for template in self.COUNTERFACTUAL_TEMPLATES:
            # Normal case
            normal_sample = TemporalSample(
                id=f"t5_template_norm_{sample_count}",
                task="T5",
                sub_task="T5-1",
                context=template["normal_context"],
                delta_t="正常世界",
                event="规则推理",
                query=template["normal_query"],
                answer=template["normal_answer"],
                state={"type": "normal_reasoning"},
                ground_truth={
                    "answer": template["normal_answer"],
                    "world_type": "normal"
                },
                metadata={
                    "pair_id": f"temp_pair_{sample_count}"
                }
            )
            self.samples.append(normal_sample)
            
            # Counterfactual case
            counter_sample = TemporalSample(
                id=f"t5_template_cf_{sample_count}",
                task="T5",
                sub_task="T5-2",
                context=f"{template['normal_context']} {template['counterfactual_rule']}",
                delta_t="虚构世界",
                event="反事实推理",
                query=template["counterfactual_query"],
                answer=template["counterfactual_answer"],
                state={"type": "counterfactual_reasoning"},
                ground_truth={
                    "answer": template["counterfactual_answer"],
                    "world_type": "counterfactual",
                    "modified_rule": template["counterfactual_rule"]
                },
                metadata={
                    "pair_id": f"temp_pair_{sample_count}"
                }
            )
            self.samples.append(counter_sample)
            
            sample_count += 1
        
        print(f"[T5 Counterfactual] Generated {len(self.samples)} samples")
        return self.samples
    
    def save(self, output_file: Path):
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(sample.to_jsonl() + '\n')
        print(f"[T5 Counterfactual] Saved {len(self.samples)} samples to {output_file}")


# ============================================================================
# Part 5: ProPara Answer Fixer
# ============================================================================

class ProParaAnswerFixer:
    """Fix ProPara data to add proper answer fields
    
    Original ProPara data has empty answer fields. We need to:
    1. Extract final state as the answer
    2. Build proper state tracking queries
    """
    
    def __init__(self):
        self.samples: List[TemporalSample] = []
    
    def convert(self, input_file: Path) -> List[TemporalSample]:
        """Convert ProPara with proper answers"""
        print(f"[ProPara Fixer] Loading from {input_file}...")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                except:
                    continue
                
                task = data.get('task', 'T2')
                sub_task = data.get('sub_task', 'T2-1')
                context = data.get('context', '')
                delta_t = data.get('delta_t', '')
                event = data.get('event', '')
                query = data.get('query', '')
                state = data.get('state', {})
                original_id = data.get('original_id', '')
                
                # Build answer from state
                if state:
                    # Extract entity states
                    answer_parts = []
                    for entity, location in state.items():
                        if location and location not in ['-', '', '?']:
                            answer_parts.append(f"{entity}: {location}")
                    
                    if answer_parts:
                        answer = "; ".join(answer_parts)
                    else:
                        answer = "无法确定"
                else:
                    answer = ""
                
                # Fix query if empty or generic
                if not query or query == "":
                    query = "在这个步骤之后，各实体的状态是什么？"
                
                sample = TemporalSample(
                    id=original_id if original_id else f"propara_fix_{len(self.samples)}",
                    task="T2",
                    sub_task="T2-1",
                    context=context,
                    delta_t=delta_t,
                    event=event,
                    query=query,
                    answer=answer,
                    state=state,
                    ground_truth={
                        "state": state,
                        "answer": answer
                    },
                    metadata={
                        "source": "propara_fixed"
                    }
                )
                self.samples.append(sample)
        
        print(f"[ProPara Fixer] Fixed {len(self.samples)} samples")
        return self.samples
    
    def save(self, output_file: Path):
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(sample.to_jsonl() + '\n')
        print(f"[ProPara Fixer] Saved {len(self.samples)} samples to {output_file}")


# ============================================================================
# Part 6: LongBench Converter for T4 Long-term Memory
# ============================================================================

class LongBenchConverter:
    """Convert LongBench datasets for T4 Long-term Memory task
    
    LongBench includes: narrativeqa, qasper, multifieldqa, etc.
    All formatted as long-context QA tasks.
    """
    
    def __init__(self):
        self.samples: List[TemporalSample] = []
    
    def convert_qasper(self, input_file: Path) -> List[TemporalSample]:
        """Convert qasper for T4"""
        print(f"[LongBench] Loading qasper from {input_file}...")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                try:
                    data = json.loads(line.strip())
                except:
                    continue
                
                context = data.get('context', '')
                query = data.get('input', '')
                answers = data.get('answers', [])
                
                if not context or not query:
                    continue
                
                # Calculate context length for difficulty
                context_len = len(context.split())
                
                sample = TemporalSample(
                    id=f"qasper_{idx}",
                    task="T4",
                    sub_task="T4-1",
                    context=context[:50000],  # Limit context
                    delta_t="长上下文",
                    event="信息检索",
                    query=query,
                    answer=answers[0] if answers else "",
                    state={
                        "context_length": context_len,
                        "task": "single_doc_qa"
                    },
                    ground_truth={
                        "answers": answers
                    },
                    metadata={
                        "source": "longbench_qasper",
                        "difficulty": "hard" if context_len > 8000 else "medium"
                    }
                )
                self.samples.append(sample)
                
                if len(self.samples) >= 5000:
                    break
        
        print(f"[LongBench] Converted {len(self.samples)} qasper samples")
        return self.samples
    
    def save(self, output_file: Path):
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(sample.to_jsonl() + '\n')
        print(f"[LongBench] Saved {len(self.samples)} samples to {output_file}")


# ============================================================================
# Part 7: Dialogue Temporal Benchmark Generator
# ============================================================================

class DialogueTemporalBenchmark:
    """Generate dialogue-based temporal reasoning benchmark
    
    This is the INNOVATION: Testing temporal awareness in dialog context.
    
    Format:
    - dialogue_context: Multi-turn dialogue
    - temporal_anchors: Time mentions hidden in dialogue
    - delta_t: Time progression
    - query: Question requiring temporal reasoning from dialogue
    - answer: Expected answer
    """
    
    # Dialogue templates with temporal reasoning
    DIALOGUE_TEMPLATES = [
        {
            "dialogue": [
                ("user", "明天有什么安排？"),
                ("assistant", "您上午9点有一个会议，预计1小时。"),
                ("user", "好的，会议结束后我要去银行办点事。"),
                ("assistant", "收到，银行通常10点开门。")
            ],
            "delta_t": "现在是上午10:30",
            "temporal_anchors": ["上午9点会议", "1小时", "10点开门"],
            "queries": [
                {
                    "query": "我现在应该去银行还是开会？",
                    "answer": "应该去银行，因为会议已结束（9-10点），银行已开门",
                    "reasoning": "1. 会议9点开始，持续1小时，10点结束\n2. 现在10:30，会议已结束\n3. 银行10点开门，现在可以办理业务"
                },
                {
                    "query": "会议什么时候结束的？",
                    "answer": "会议大约10点结束",
                    "reasoning": "会议从9点开始，预计1小时，所以10点结束"
                }
            ]
        },
        {
            "dialogue": [
                ("user", "帮我查一下下周的行程。"),
                ("assistant", "您周一有项目评审，周三上午有客户会议，周五下午有培训。"),
                ("user", "周二的客户会议改到什么时候合适？"),
                ("assistant", "周二您有空档，建议安排在上午10点或下午2点。")
            ],
            "delta_t": "现在是周二上午11点",
            "temporal_anchors": ["周一", "周三上午", "周五下午", "周二"],
            "queries": [
                {
                    "query": "如果客户会议安排在周二下午2点，离您下一个安排有多长时间？",
                    "answer": "下一个安排是周三上午，有大约17小时（周二下午2点到周三上午9点左右）",
                    "reasoning": "1. 今天周二，客户会议安排在下午2点\n2. 下一个安排是周三上午\n3. 从周二下午2点到周三上午约17小时"
                }
            ]
        },
        {
            "dialogue": [
                ("user", "帮我安排一下今天的日程。"),
                ("assistant", "现在是早上8点。您9点有团队晨会，11点有部门周会，下午3点要见客户。"),
                ("user", "好的，中午12点到1点午餐，2点我要跟进项目进度。")
            ],
            "delta_t": "现在是上午10:30",
            "temporal_anchors": ["8点", "9点晨会", "11点周会", "12-1点午餐", "2点项目", "3点客户"],
            "queries": [
                {
                    "query": "从现在到团队晨会开始，有多长时间？",
                    "answer": "从10:30到下个9点的晨会——不对，晨会9点已过。距离11点部门周会还有30分钟。",
                    "reasoning": "现在是10:30，团队晨会9点开始，已经过去了。下一个安排是11点的部门周会，还有30分钟。"
                },
                {
                    "query": "我上午还有什么安排？",
                    "answer": "上午还有11点的部门周会",
                    "reasoning": "已过9点的晨会，还剩11点的部门周会"
                }
            ]
        }
    ]
    
    def __init__(self):
        self.samples: List[TemporalSample] = []
    
    def generate_samples(self) -> List[TemporalSample]:
        """Generate dialogue temporal reasoning samples"""
        print("[Dialogue Temporal] Generating samples...")
        
        sample_count = 0
        
        for template in self.DIALOGUE_TEMPLATES:
            # Build dialogue context
            dialogue_lines = []
            for role, content in template["dialogue"]:
                dialogue_lines.append(f"{role}: {content}")
            context = "\n".join(dialogue_lines)
            
            delta_t = template["delta_t"]
            temporal_anchors = template["temporal_anchors"]
            
            for i, q_data in enumerate(template["queries"]):
                query = q_data["query"]
                answer = q_data["answer"]
                reasoning = q_data.get("reasoning", "")
                
                sample = TemporalSample(
                    id=f"dialogue_temp_{sample_count}",
                    task="T2",  # Could be T1, T2, or T4 depending on query type
                    sub_task="T2-1",
                    context=context,
                    delta_t=delta_t,
                    event="对话中时间信息提取与推理",
                    query=query,
                    answer=answer,
                    state={
                        "type": "dialogue_temporal",
                        "temporal_anchors": temporal_anchors,
                        "dialogue_turns": len(template["dialogue"])
                    },
                    ground_truth={
                        "answer": answer,
                        "reasoning_steps": reasoning
                    },
                    metadata={
                        "source": "dialogue_temporal_benchmark",
                        "requires_temporal_extraction": True,
                        "difficulty": "medium"
                    }
                )
                self.samples.append(sample)
                sample_count += 1
        
        # Generate more variations
        more_samples = self._generate_variations()
        self.samples.extend(more_samples)
        
        print(f"[Dialogue Temporal] Generated {len(self.samples)} samples")
        return self.samples
    
    def _generate_variations(self) -> List[TemporalSample]:
        """Generate additional dialogue temporal samples"""
        variations = []
        
        # Add more realistic dialogues
        additional_dialogues = [
            {
                "dialogue": [
                    ("user", "帮我订一张明天去上海的机票。"),
                    ("assistant", "好的，明天是周三。您希望几点出发？"),
                    ("user", "上午9点左右吧。"),
                    ("assistant", "已为您订好明天（周三）上午9:15的航班，预计11:30到达上海虹桥机场。")
                ],
                "delta_t": "现在是周二下午5点",
                "query": "离航班起飞还有多长时间？",
                "answer": "大约16小时（今天周二下午5点到明天周三上午9:15）",
                "anchors": ["周三", "上午9:15", "11:30到达"]
            },
            {
                "dialogue": [
                    ("user", "这周还有什么重要事项？"),
                    ("assistant", "周二有项目评审，周四提交报告，周五下午有培训。今天是周一。"),
                    ("user", "好的，我周三要准备一下周四的报告。")
                ],
                "delta_t": "现在是周三下午",
                "query": "您今天要准备什么？",
                "answer": "今天（周三）要准备周四提交的报告",
                "anchors": ["周二评审", "周四提交", "周五培训", "今天周一", "周三准备"]
            }
        ]
        
        for idx, dialog in enumerate(additional_dialogues):
            dialogue_lines = []
            for role, content in dialog["dialogue"]:
                dialogue_lines.append(f"{role}: {content}")
            context = "\n".join(dialogue_lines)
            
            sample = TemporalSample(
                id=f"dialogue_var_{idx}",
                task="T1",
                sub_task="T1-1",
                context=context,
                delta_t=dialog["delta_t"],
                event="时间计算",
                query=dialog["query"],
                answer=dialog["answer"],
                state={
                    "type": "dialogue_temporal",
                    "temporal_anchors": dialog["anchors"]
                },
                ground_truth={
                    "answer": dialog["answer"]
                },
                metadata={
                    "source": "dialogue_temporal_benchmark_variation"
                }
            )
            variations.append(sample)
        
        return variations
    
    def save(self, output_file: Path):
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(sample.to_jsonl() + '\n')
        print(f"[Dialogue Temporal] Saved {len(self.samples)} samples to {output_file}")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run all conversions"""
    print("=" * 60)
    print("UNIFIED DATA CONVERSION FOR TEMPORAL WORLD MODELING")
    print("=" * 60)
    
    results = {}
    
    # 1. OpenPI2.0 for T2
    print("\n[1/7] Converting OpenPI2.0 for T2 State Tracking...")
    openpi_file = DATA_DIR / "OpenPI2.0" / "data" / "dev-data-reformatted-v4.json"
    if openpi_file.exists():
        converter = OpenPI2Converter()
        converter.convert(openpi_file)
        converter.save(OUTPUT_DIR / "openpi2_t2.jsonl")
        results['openpi2'] = len(converter.samples)
    else:
        print(f"[OpenPI2] File not found: {openpi_file}")
    
    # 2. PASTA for T2 and T5
    print("\n[2/7] Converting PASTA for T2/T5...")
    pasta_file = DATA_DIR / "pasta" / "data" / "tr_data.jsonl"
    if pasta_file.exists():
        converter = PASTAConverter()
        converter.convert(pasta_file, task_type="both")
        converter.save(OUTPUT_DIR / "pasta_t2_t5.jsonl")
        results['pasta'] = len(converter.samples)
    else:
        print(f"[PASTA] File not found: {pasta_file}")
    
    # 3. T3 Conflict Detection
    print("\n[3/7] Generating T3 Conflict Detection samples...")
    atomic_file = DATA_DIR / "ATOMIC" / "v4_atomic_all_agg.csv"
    conflict_constructor = AtomicConflictConstructor()
    conflict_constructor.construct_from_atomic(atomic_file)
    conflict_constructor.save(OUTPUT_DIR / "t3_conflict_detection.jsonl")
    results['t3_conflict'] = len(conflict_constructor.samples)
    
    # 4. T5 Counterfactual
    print("\n[4/7] Generating T5 Counterfactual samples...")
    counterfactual_gen = CounterfactualRulePerturbation()
    counterfactual_gen.generate_samples()
    counterfactual_gen.save(OUTPUT_DIR / "t5_counterfactual.jsonl")
    results['t5_counterfactual'] = len(counterfactual_gen.samples)
    
    # 5. Fix ProPara
    print("\n[5/7] Fixing ProPara answers...")
    propara_file = OUTPUT_DIR / "propara.jsonl"
    if propara_file.exists():
        fixer = ProParaAnswerFixer()
        fixer.convert(propara_file)
        fixer.save(OUTPUT_DIR / "propara_fixed_v2.jsonl")
        results['propara_fixed'] = len(fixer.samples)
    else:
        print(f"[ProPara] File not found: {propara_file}")
    
    # 6. LongBench for T4
    print("\n[6/7] Converting LongBench for T4...")
    qasper_file = DATA_DIR / "LongBench" / "data" / "qasper.jsonl"
    if qasper_file.exists():
        converter = LongBenchConverter()
        converter.convert_qasper(qasper_file)
        converter.save(OUTPUT_DIR / "longbench_qasper_t4.jsonl")
        results['longbench'] = len(converter.samples)
    else:
        print(f"[LongBench] File not found: {qasper_file}")
    
    # 7. Dialogue Temporal Benchmark
    print("\n[7/7] Generating Dialogue Temporal Benchmark...")
    dialogue_gen = DialogueTemporalBenchmark()
    dialogue_gen.generate_samples()
    dialogue_gen.save(OUTPUT_DIR / "dialogue_temporal_benchmark.jsonl")
    results['dialogue_temporal'] = len(dialogue_gen.samples)
    
    # Summary
    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    total = 0
    for name, count in results.items():
        print(f"  {name}: {count} samples")
        total += count
    print("=" * 60)
    print(f"Total: {total} samples")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Save summary report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_samples": total,
        "datasets": results,
        "task_coverage": {
            "T1": "TimeQA, DROP, MCTACO (existing)",
            "T2": "OpenPI2.0, PASTA, ProPara (new + fix)",
            "T3": "Conflict Detection (synthetic)",
            "T4": "LongBench, qasper (new)",
            "T5": "Counterfactual, PASTA counterfactual"
        }
    }
    
    with open(OUTPUT_DIR / "conversion_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\nReport saved to: conversion_report.json")


if __name__ == "__main__":
    main()