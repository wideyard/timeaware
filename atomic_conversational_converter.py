#!/usr/bin/env python3
"""
ATOMIC Temporal Awareness Data Converter - Conversational Only
===============================================================
将ATOMIC常识知识图谱转化为对话式时间感知评测数据。

核心要求：
1. 只使用 v4_atomic_all_agg.csv
2. 严格过滤：所有字段都必须有有效值（无空值、无"none"）
3. 只生成对话式（Track B）数据

任务映射：
 - T2: 状态更新 (xNeed → event → xEffect)
 - T3: 冲突检测 (属性冲突)
 - T5: 反事实 (颠覆 oReact)

作者：TemporalAware Team
"""

import json
import pandas as pd
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from copy import deepcopy

# Configuration
DATA_DIR = Path("data/ATOMIC")
OUTPUT_DIR = Path("converted_data_v2")


@dataclass
class ConversationalSample:
    """对话式时间感知评测数据样本。"""
    task: str  # T2, T3, T5
    sub_task: str  # 细分任务
    event: str  # ATOMIC事件
    conversation: List[Dict[str, str]]  # 多轮对话
    query: str  # 最终问题
    answer: str  # 答案
    state_info: Optional[Dict[str, Any]] = None  # 状态信息
    ground_truth: Optional[Dict[str, Any]] = None  # 标准答案
    difficulty: str = "medium"  # 难度
    source_id: Optional[str] = None  # 原始ID


class ATOMICDataLoader:
    """ATOMIC数据加载与严格过滤。"""
    
    # 关键字段列表
    KEY_FIELDS = ['oEffect', 'oReact', 'oWant', 'xAttr', 'xEffect', 
                  'xIntent', 'xNeed', 'xReact', 'xWant']
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.df = None
        
    def load_and_filter(self) -> pd.DataFrame:
        """加载数据并严格过滤。"""
        print(f"Loading ATOMIC from {self.file_path}...")
        df = pd.read_csv(self.file_path, index_col=0)
        print(f"Original: {len(df)} records")
        
        # 解析JSON列表
        for col in self.KEY_FIELDS:
            df[col] = df[col].apply(self._parse_json_list)
        
        # 严格过滤：所有关键字段都必须有有效值
        valid_mask = pd.Series([True] * len(df), index=df.index)
        
        # 1. event（索引）不能为空
        valid_mask &= df.index.notna()
        valid_mask &= df.index != ''
        valid_mask &= df.index != 'nan'
        
        # 2. 所有关键字段都必须有有效值（非空列表，且至少一个非"none"元素）
        for col in self.KEY_FIELDS:
            valid_mask &= df[col].apply(self._has_valid_values)
        
        filtered_df = df[valid_mask].copy()
        # 将索引转为列
        filtered_df['event'] = filtered_df.index
        
        print(f"After strict filter: {len(filtered_df)} records ({len(filtered_df)/len(df)*100:.1f}% kept)")
        
        return filtered_df
    
    def _parse_json_list(self, val: Any) -> List[str]:
        """解析JSON列表。"""
        if pd.isna(val):
            return []
        if isinstance(val, list):
            return val
        try:
            result = json.loads(val)
            return result if isinstance(result, list) else []
        except:
            return []
    
    def _has_valid_values(self, lst: List[str]) -> bool:
        """检查列表是否至少有一个有效值（非"none"）。"""
        if not lst:
            return False
        for item in lst:
            if item and 'none' not in str(item).lower():
                return True
        return False


class ConversationalDataGenerator:
    """只生成对话式数据。"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.samples: List[ConversationalSample] = []
        
    def generate_all(self) -> List[ConversationalSample]:
        """生成所有任务的对话式数据。"""
        print("\n" + "="*60)
        print("Generating Conversational Data (Track B Only)")
        print("="*60)
        
        # T2: 状态更新
        t2_samples = self._generate_t2_samples()
        self.samples.extend(t2_samples)
        
        # T3: 冲突检测
        t3_samples = self._generate_t3_samples()
        self.samples.extend(t3_samples)
        
        # T5: 反事实
        t5_samples = self._generate_t5_samples()
        self.samples.extend(t5_samples)
        
        print(f"\nTotal generated: {len(self.samples)} conversational samples")
        return self.samples
    
    # ============================================================
    # T2: 状态更新 - 对话式
    # ============================================================
    
    def _generate_t2_samples(self) -> List[ConversationalSample]:
        """T2对话式样本：状态追踪。"""
        print("\n[T2 State Tracking] Generating...")
        samples = []
        
        for _, row in self.df.iterrows():
            event = self._clean_text(row['event'])
            x_need = self._get_valid_items(row['xNeed'])
            x_effect = self._get_valid_items(row['xEffect'])
            x_want = self._get_valid_items(row['xWant'])
            x_react = self._get_valid_items(row['xReact'])
            
            if not (x_need and x_effect):
                continue
            
            # T2-Convo-1: 信息渐进揭示
            conv1 = self._make_t2_progressive(event, x_need, x_effect)
            samples.append(conv1)
            
            # T2-Convo-2: 干扰信息过滤
            if x_want:
                conv2 = self._make_t2_noisy(event, x_need, x_effect, x_want)
                samples.append(conv2)
            
            # T2-Convo-3: 状态回滚
            conv3 = self._make_t2_rollback(event, x_need, x_effect, x_react)
            if conv3:
                samples.append(conv3)
        
        print(f"  T2 samples: {len(samples)}")
        return samples
    
    def _make_t2_progressive(self, event: str, x_need: List, x_effect: List) -> ConversationalSample:
        """T2-状态渐进揭示对话。"""
        need = x_need[0]
        effect = x_effect[0]
        
        conversation = [
            {"role": "user", "content": f"I am {self._to_action(need)}."},
            {"role": "assistant", "content": "Okay, looks like you are preparing."},
            {"role": "user", "content": f"Yes, I am going to {event}."},
            {"role": "assistant", "content": f"Got it, {event}."},
            {"role": "user", "content": "By the way, the weather is nice today."},  # Noise
            {"role": "assistant", "content": "Yes, it is."},
            {"role": "user", "content": f"After finishing this, what state will I be in?"}
        ]
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Progressive",
            event=event,
            conversation=conversation,
            query="What is the participant's state after the event?",
            answer=effect,
            state_info={
                "type": "progressive_state",
                "before": need,
                "after": effect
            },
            ground_truth={"final_state": effect},
            difficulty="medium",
            source_id=f"atomic_t2_prog_{hash(event)}"
        )
    
    def _make_t2_noisy(self, event: str, x_need: List, x_effect: List, x_want: List) -> ConversationalSample:
        """T2-干扰信息对话。"""
        need = x_need[0]
        effect = x_effect[0]
        want = x_want[0] if x_want else ""
        
        conversation = [
            {"role": "user", "content": f"I am {self._to_action(need)}."},
            {"role": "assistant", "content": "Okay, preparing."},
            {"role": "user", "content": "By the way, do you have a pet?"},  # Noise 1
            {"role": "assistant", "content": "Hmm, let's focus."},
            {"role": "user", "content": f"I want to {self._to_action(want)} after this."},
            {"role": "assistant", "content": f"Okay, {want}."},
            {"role": "user", "content": "What should I eat for dinner tomorrow?"},  # Noise 2
            {"role": "assistant", "content": "..."},
            {"role": "user", "content": f"Then I started {event}."},
            {"role": "assistant", "content": f"Noted, {event}."},
            {"role": "user", "content": "After this, what state will I be in? Ignore the irrelevant topics."}
        ]
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Noisy",
            event=event,
            conversation=conversation,
            query="Ignoring the noise, what state will the participant be in after the event?",
            answer=effect,
            state_info={"type": "noisy_state", "noise_count": 2},
            ground_truth={"filtered_state": effect},
            difficulty="hard",
            source_id=f"atomic_t2_noisy_{hash(event)}"
        )
    
    def _make_t2_rollback(self, event: str, x_need: List, x_effect: List, x_react: List) -> Optional[ConversationalSample]:
        """T2-状态回滚对话。"""
        if not x_need or not x_effect:
            return None
            
        need = x_need[0]
        effect = x_effect[0]
        react = x_react[0] if x_react else "feeling different"
        
        conversation = [
            {"role": "user", "content": f"Initially, I was {self._to_action(need)}."},
            {"role": "assistant", "content": f"Remembered, initial state is '{self._to_state(need)}'."},
            {"role": "user", "content": f"Then I started {event}."},
            {"role": "assistant", "content": f"Doing {event}..."},
            {"role": "user", "content": f"After finishing, I felt {react}."},
            {"role": "assistant", "content": f"State updated, now it's '{effect}'."},
            {"role": "user", "content": "Wait, what was my state before all this started?"}
        ]
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Rollback",
            event=event,
            conversation=conversation,
            query="What was the participant's initial state?",
            answer=self._to_state(need),
            state_info={"type": "rollback_state"},
            ground_truth={"initial_state": self._to_state(need)},
            difficulty="hard",
            source_id=f"atomic_t2_roll_{hash(event)}"
        )
    
    # ============================================================
    # T3: 冲突检测 - 对话式
    # ============================================================
    
    def _generate_t3_samples(self) -> List[ConversationalSample]:
        """T3对话式样本：冲突检测。"""
        print("\n[T3 Conflict Detection] Generating...")
        samples = []
        
        # 定义冲突对
        conflict_pairs = self._find_conflict_events()
        
        for event1, event2, conflict_type in conflict_pairs[:500]:  # 限制数量
            # T3-Convo-1: 隐藏冲突
            conv = self._make_t3_hidden_conflict(event1, event2, conflict_type)
            samples.append(conv)
        
        # 单事件属性推断
        for _, row in self.df.head(300).iterrows():
            event = self._clean_text(row['event'])
            x_attr = self._get_valid_items(row['xAttr'])
            x_need = self._get_valid_items(row['xNeed'])
            
            if x_attr:
                conv = self._make_t3_attribute(event, x_attr, x_need)
                samples.append(conv)
        
        print(f"  T3 samples: {len(samples)}")
        return samples
    
    def _find_conflict_events(self) -> List[tuple]:
        """寻找冲突事件对。"""
        conflict_pairs = []
        
        # 定义冲突关键词
        conflicts = [
            (["study", "read", "work", "quiet"], ["party", "loud", "game"], "attribute_conflict"),
            (["rest", "sleep"], ["exercise", "run", "gym"], "state_conflict"),
            (["home", "stay"], ["leave", "travel", "go out"], "location_conflict")
        ]
        
        events = self.df['event'].tolist()
        
        for e1 in events:
            e1_clean = self._clean_text(e1)
            if not e1_clean:
                continue
                
            for conflict_kw1, conflict_kw2, conflict_type in conflicts:
                has_kw1 = any(kw in e1_clean.lower() for kw in conflict_kw1)
                has_kw2 = any(kw in e1_clean.lower() for kw in conflict_kw2)
                
                if has_kw1:
                    for e2 in events:
                        has_kw2_e2 = any(kw in self._clean_text(e2).lower() for kw in conflict_kw2)
                        if has_kw2_e2:
                            conflict_pairs.append((e1_clean, self._clean_text(e2), conflict_type))
                            if len(conflict_pairs) >= 500:
                                break
                    if len(conflict_pairs) >= 500:
                        break
                elif has_kw2:
                    for e2 in events:
                        has_kw1_e2 = any(kw in self._clean_text(e2).lower() for kw in conflict_kw1)
                        if has_kw1_e2:
                            conflict_pairs.append((e1_clean, self._clean_text(e2), conflict_type))
                            if len(conflict_pairs) >= 500:
                                break
                    if len(conflict_pairs) >= 500:
                        break
            
            if len(conflict_pairs) >= 500:
                break
        
        return conflict_pairs[:500]
    
    def _make_t3_hidden_conflict(self, event1: str, event2: str, conflict_type: str) -> ConversationalSample:
        """T3-隐藏冲突对话。"""
        conversation = [
            {"role": "user", "content": f"I'm planning to {event1} tomorrow, which needs focus and quiet."},
            {"role": "assistant", "content": f"Okay, noted. {event1} needs a focused environment."},
            {"role": "user", "content": "By the way, what did I have for lunch today? Never mind."},  # Noise
            {"role": "assistant", "content": "..."},
            {"role": "user", "content": f"I also scheduled {event2} at the same time."},
            {"role": "assistant", "content": f"Also at the same time?"},
            {"role": "user", "content": "Yes, do you see any problem with this arrangement?"}
        ]
        
        conflict_explanation = {
            "attribute_conflict": f"{event1} needs quiet, but {event2} creates noise",
            "state_conflict": f"{event1} and {event2} have opposite state requirements",
            "location_conflict": f"{event1} and {event2} cannot happen at the same location"
        }
        
        return ConversationalSample(
            task="T3",
            sub_task="T3-Convo-HiddenConflict",
            event=f"{event1} & {event2}",
            conversation=conversation,
            query="What conflict exists in this arrangement?",
            answer=conflict_explanation.get(conflict_type, f"Conflict: {conflict_type}"),
            state_info={"conflict_type": conflict_type, "events": [event1, event2]},
            ground_truth={"has_conflict": True, "conflict_type": conflict_type},
            difficulty="hard",
            source_id=f"atomic_t3_conflict_{hash(event1)}"
        )
    
    def _make_t3_attribute(self, event: str, x_attr: List, x_need: List) -> ConversationalSample:
        """T3-属性推断对话。"""
        attr = x_attr[0]
        need = x_need[0] if x_need else "preparing"
        
        conversation = [
            {"role": "user", "content": f"I know someone who {event}."},
            {"role": "assistant", "content": f"Okay, {event}."},
            {"role": "user", "content": f"Before that, they were {self._to_action(need)}."},
            {"role": "assistant", "content": "Hmm, preparations."},
            {"role": "user", "content": "What personality traits do you think this person has?"}
        ]
        
        return ConversationalSample(
            task="T3",
            sub_task="T3-Convo-Attribute",
            event=event,
            conversation=conversation,
            query="Based on these behaviors, infer this person's personality traits.",
            answer=attr,
            state_info={"attribute": attr, "event": event},
            ground_truth={"inferred_attribute": attr},
            difficulty="medium",
            source_id=f"atomic_t3_attr_{hash(event)}"
        )
    
    # ============================================================
    # T5: 反事实 - 对话式
    # ============================================================
    
    def _generate_t5_samples(self) -> List[ConversationalSample]:
        """T5对话式样本：反事实推理。"""
        print("\n[T5 Counterfactual] Generating...")
        samples = []
        
        for _, row in self.df.head(1000).iterrows():
            event = self._clean_text(row['event'])
            o_react = self._get_valid_items(row['oReact'])
            o_effect = self._get_valid_items(row['oEffect'])
            o_want = self._get_valid_items(row['oWant'])
            
            if not o_react:
                continue
            
            # T5-Convo-1: 规则建立
            conv1 = self._make_t5_rule_establishment(event, o_react[0])
            samples.append(conv1)
            
            # T5-Convo-2: 规则混淆
            if o_react and o_effect:
                conv2 = self._make_t5_rule_confusion(event, o_react[0], o_effect[0])
                samples.append(conv2)
            
            # T5-Convo-3: 多规则组合
            if len(o_react) > 1:
                conv3 = self._make_t5_multi_rule(event, o_react)
                samples.append(conv3)
        
        print(f"  T5 samples: {len(samples)}")
        return samples
    
    def _make_t5_rule_establishment(self, event: str, o_react: str) -> ConversationalSample:
        """T5-规则建立对话。"""
        inverted_react = self._invert_reaction(o_react)
        
        conversation = [
            {"role": "user", "content": "Let's play a hypothetical game. In this hypothetical world:"},
            {"role": "assistant", "content": "Okay, what are the rules of this world?"},
            {"role": "user", "content": f"In this world, {event} makes people feel {inverted_react} instead of {o_react}."},
            {"role": "assistant", "content": f"Noted: Rule is {event} -> {inverted_react} (opposite to reality)."},
            {"role": "user", "content": f"So, if someone {event}, how would others react?"},
            {"role": "assistant", "content": "[Requires model to answer]"}
        ]
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-RuleEstablishment",
            event=event,
            conversation=conversation,
            query=f"In this hypothetical world, how do people react after {event}?",
            answer=f"{inverted_react} (following hypothetical rule)",
            state_info={
                "original_reaction": o_react,
                "counterfactual_reaction": inverted_react,
                "rule_type": "inverse"
            },
            ground_truth={"reaction": inverted_react, "should_follow_rule": True},
            difficulty="hard",
            source_id=f"atomic_t5_rule_{hash(event)}"
        )
    
    def _make_t5_rule_confusion(self, event: str, o_react: str, o_effect: str) -> ConversationalSample:
        """T5-规则混淆对话。"""
        inverted_react = self._invert_reaction(o_react)
        
        conversation = [
            {"role": "user", "content": "Let's imagine a fictional scenario, but first remember:"},
            {"role": "assistant", "content": "Okay."},
            {"role": "user", "content": f"[Fictional Rule] In this scenario, {event} would make people {inverted_react}."},
            {"role": "assistant", "content": f"Noted: fictional rule = {event} -> {inverted_react}."},
            {"role": "user", "content": f"[Reality Reminder] But in reality, {event} usually makes people {o_react}."},
            {"role": "assistant", "content": "Got it, these are two different worlds."},
            {"role": "user", "content": "Now back to the fictional scenario, if someone {event}, how would people react?"}
        ]
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-RuleConfusion",
            event=event,
            conversation=conversation,
            query="In this fictional scenario (not reality!), how would people react?",
            answer=f"{inverted_react} (follow fictional rule, ignore reality reminder)",
            state_info={
                "fictional_rule": f"{event} -> {inverted_react}",
                "real_rule": f"{event} -> {o_react}",
                "should_isolate": True
            },
            ground_truth={
                "should_follow_fictional": True,
                "fictional_reaction": inverted_react,
                "trap": "Reality knowledge may interfere"
            },
            difficulty="very_hard",
            source_id=f"atomic_t5_confusion_{hash(event)}"
        )
    
    def _make_t5_multi_rule(self, event: str, o_reacts: List[str]) -> ConversationalSample:
        """T5-多规则组合对话。"""
        inv1 = self._invert_reaction(o_reacts[0])
        inv2 = self._invert_reaction(o_reacts[1]) if len(o_reacts) > 1 else inv1
        
        conversation = [
            {"role": "user", "content": "This is a complex hypothetical world with two special rules:"},
            {"role": "assistant", "content": "Please go on."},
            {"role": "user", "content": f"Rule 1: First reaction to {event} is {inv1}."},
            {"role": "assistant", "content": "Rule 1 noted."},
            {"role": "user", "content": f"Rule 2: Second encounter with the same event triggers {inv2}."},
            {"role": "assistant", "content": "Rule 2 noted."},
            {"role": "user", "content": f"Someone {event} for the first time, how do people react?"},
            {"role": "assistant", "content": "[To answer]"},
            {"role": "user", "content": f"What if they {event} again for the second time?"}
        ]
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-MultiRule",
            event=event,
            conversation=conversation,
            query="According to hypothetical rules, what are the first and second reactions?",
            answer=f"First: {inv1}; Second: {inv2}",
            state_info={
                "rules": [
                    {"condition": "first", "reaction": inv1},
                    {"condition": "second", "reaction": inv2}
                ]
            },
            ground_truth={
                "first_reaction": inv1,
                "second_reaction": inv2,
                "requires_multi_step": True
            },
            difficulty="very_hard",
            source_id=f"atomic_t5_multi_{hash(event)}"
        )
    
    # ============================================================
    # 辅助方法
    # ============================================================
    
    def _clean_text(self, text: str) -> str:
        """清理文本。"""
        if pd.isna(text) or not text:
            return ""
        text = str(text).strip()
        text = text.replace("PersonX", "someone").replace("PersonY", "another person")
        return text
    
    def _get_valid_items(self, items: List) -> List[str]:
        """获取有效项（非空、非none）。"""
        if not items:
            return []
        return [item for item in items if item and 'none' not in str(item).lower()]
    
    def _to_action(self, text: str) -> str:
        """转换为动作形式。"""
        text = str(text).strip()
        if text.startswith("to "):
            return text[3:]
        return text
    
    def _to_state(self, text: str) -> str:
        """转换为状态形式。"""
        return f"doing {self._to_action(text)}"
    
    def _invert_reaction(self, reaction: str) -> str:
        """反转反应（用于反事实）。"""
        inversion_map = {
            "happy": "sad", "sad": "happy",
            "angry": "pleased", "pleased": "angry",
            "excited": "bored", "bored": "excited",
            "grateful": "ungrateful", "ungrateful": "grateful",
            "proud": "ashamed", "ashamed": "proud",
            "satisfied": "dissatisfied", "dissatisfied": "satisfied",
            "fearful": "brave", "brave": "fearful",
            "surprised": "expecting", "expecting": "surprised"
        }
        
        reaction_lower = reaction.lower()
        for orig, inv in inversion_map.items():
            if orig in reaction_lower:
                return reaction.replace(orig, inv).replace(orig.lower(), inv)
        
        # 如果没有找到反转词，返回"相反的反应"
        return f"opposite reaction (originally {reaction})"


def save_samples(samples: List[ConversationalSample], output_path: Path):
    """保存样本到JSONL文件。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
    print(f"Saved to: {output_path}")


def generate_report(samples: List[ConversationalSample]) -> Dict:
    """生成统计报告。"""
    report = {
        "total_samples": len(samples),
        "task_distribution": {},
        "difficulty_distribution": {},
        "subtask_distribution": {}
    }
    
    for sample in samples:
        # 任务分布
        report["task_distribution"][sample.task] = report["task_distribution"].get(sample.task, 0) + 1
        
        # 难度分布
        report["difficulty_distribution"][sample.difficulty] = report["difficulty_distribution"].get(sample.difficulty, 0) + 1
        
        # 子任务分布
        key = f"{sample.task}-{sample.sub_task}"
        report["subtask_distribution"][key] = report["subtask_distribution"].get(key, 0) + 1
    
    return report


def main():
    """主函数。"""
    print("="*60)
    print("ATOMIC Conversational Temporal Data Converter")
    print("Strict filtering + Conversational only")
    print("="*60)
    
    # 加载并过滤数据
    loader = ATOMICDataLoader(DATA_DIR / "v4_atomic_all_agg.csv")
    df = loader.load_and_filter()
    
    # 生成对话式数据
    generator = ConversationalDataGenerator(df)
    samples = generator.generate_all()
    
    # 保存
    output_file = OUTPUT_DIR / "atomic_conversational.jsonl"
    save_samples(samples, output_file)
    
    # 统计报告
    report = generate_report(samples)
    report_file = OUTPUT_DIR / "atomic_conversational_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("Conversion Complete")
    print("="*60)
    print(f"Total samples: {len(samples)}")
    print("\nTask distribution:")
    for task, count in report["task_distribution"].items():
        print(f"  {task}: {count}")
    print("\nDifficulty distribution:")
    for diff, count in report["difficulty_distribution"].items():
        print(f"  {diff}: {count}")
    
    return samples


if __name__ == "__main__":
    main()