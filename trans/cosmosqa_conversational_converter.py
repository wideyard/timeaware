#!/usr/bin/env python3
"""
CosmosQA Temporal Awareness Data Converter - Conversational Only
====================================================================
将CosmosQA叙事性问答数据转化为对话式时间感知评测数据。

核心特点：
- 叙事性Context充满主观感受、模糊时间词
- 适合T4（长期记忆）和T5（反事实）
- 利用动词时态作为时间标签

任务映射：
- T2: 状态更新（从过去时态推断当前状态）
- T4: 长期记忆（在叙事中埋藏时间钩子）
- T5: 反事实（改变情感-行为关系）

作者：TemporalAware Team
"""

import json
import pandas as pd
import re
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Configuration
DATA_DIR = Path("data/CosmosQA/data")
OUTPUT_DIR = Path("converted_data_v3")


@dataclass
class ConversationalSample:
    """对话式时间感知评测数据样本。"""
    task: str  # T2, T4, T5
    sub_task: str  # 细分任务
    context: str  # 原始叙事上下文
    conversation: List[Dict[str, str]]  # 多轮对话
    query: str  # 最终问题
    answer: str  # 答案
    state_info: Optional[Dict[str, Any]] = None
    ground_truth: Optional[Dict[str, Any]] = None
    difficulty: str = "medium"
    source_id: Optional[str] = None


class CosmosQALoader:
    """加载CosmosQA数据集。"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        
    def load(self, split: str = "train") -> pd.DataFrame:
        """加载数据。"""
        file_path = self.data_dir / f"{split}.csv"
        print(f"Loading CosmosQA from {file_path}...")
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} samples")
        return df
    
    def analyze_tense(self, text: str) -> Dict[str, List[str]]:
        """分析文本中的时态标记。"""
        # 过去时动词
        past_verbs = re.findall(r'\b(saw|played|went|did|was|were|had|made|said|got|left|came|took|gave|found|thought|knew|became|showed|heard|brought|wrote|sat|stood|ran|ate|drank|drove|flew|grew|knew|tore|wore)\b', text.lower())
        
        # 时间标记
        time_markers = re.findall(r'\b(yesterday|last\s+\w+|ago|before|earlier|previously|\d+\s+(days?|hours?|weeks?|months?|years?)\s+ago|on\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)|in\s+(january|february|march|april|may|june|july|august|september|october|november|december))\b', text.lower())
        
        # 将来时标记
        future_markers = re.findall(r'\b(will|going\s+to|going\s+to\s+be|plan\s+to|want\s+to|next\s+\w+|in\s+the\s+future|tomorrow)\b', text.lower())
        
        return {
            "past_tense": past_verbs,
            "time_markers": time_markers,
            "future_markers": future_markers
        }
    
    def extract_time_anchor(self, context: str) -> Optional[str]:
        """从上下文提取时间锚点。"""
        # 常见的时间模式
        patterns = [
            r'(on\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday))',
            r'(last\s+(night|week|month|year))',
            r'(yesterday)',
            r'(\d+[:\d]*\s*(am|pm|o\'clock))',
            r'(in\s+the\s+(morning|afternoon|evening|night))',
            r'(at\s+\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context.lower())
            if match:
                return match.group(0)
        
        return None
    
    def detect_emotion_pattern(self, context: str) -> List[Dict[str, str]]:
        """检测情感-行为模式。"""
        emotions = {
            "happy": ["happy", "glad", "pleased", "delighted", "excited", "thrilled", "enjoyed", "loved", "smile", "laugh"],
            "sad": ["sad", "unhappy", "disappointed", "upset", "depressed", "sorry", "regret"],
            "angry": ["angry", "furious", "mad", "annoyed", "frustrated", "irritated"],
            "surprised": ["surprised", "shocked", "amazed", "stunned", "blown away"],
            "scared": ["scared", "afraid", "frightened", "terrified", "worried"]
        }
        
        actions = {
            "go_again": ["go back", "return", "see again", "visit again", "come back"],
            "avoid": ["avoid", "never again", "not go", "stay away"],
            "recommend": ["recommend", "suggest", "tell others", "share"],
            "regret": ["regret", "wish I hadn't", "shouldn't have"]
        }
        
        found_emotions = []
        context_lower = context.lower()
        
        for emotion, keywords in emotions.items():
            for kw in keywords:
                if kw in context_lower:
                    found_emotions.append({"emotion": emotion, "keyword": kw})
                    break
        
        return found_emotions


class CosmosQAConversationalConverter:
    """CosmosQA对话式数据转换器。"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.loader = CosmosQALoader(DATA_DIR)
        self.samples: List[ConversationalSample] = []
        
    def convert_all(self) -> List[ConversationalSample]:
        """转换所有数据。"""
        print("\n" + "="*60)
        print("Converting CosmosQA to Conversational Temporal Data")
        print("="*60)
        
        for idx, row in self.df.iterrows():
            context = row.get('context', '')
            question = row.get('question', '')
            answers = [row.get(f'answer{i}', '') for i in range(4)]
            label = row.get('label', 0)
            sample_id = row.get('id', f'sample_{idx}')
            
            if not context or not question:
                continue
            
            # T2: 状态更新（时态推断）
            t2_samples = self._generate_t2_samples(context, question, answers, label, sample_id)
            self.samples.extend(t2_samples)
            
            # T4: 长期记忆（叙事埋藏）
            t4_samples = self._generate_t4_samples(context, question, answers, label, sample_id)
            self.samples.extend(t4_samples)
            
            # T5: 反事实（情感反转）
            t5_samples = self._generate_t5_samples(context, question, answers, label, sample_id)
            self.samples.extend(t5_samples)
            
            # 限制数量
            if len(self.samples) >= 15000:
                break
        
        print(f"\nTotal converted: {len(self.samples)} samples")
        return self.samples
    
    # =====================================================================
    # T2: 状态更新 (State Update from Tense)
    # =====================================================================
    
    def _generate_t2_samples(self, context: str, question: str, 
                            answers: List[str], label: int,
                            sample_id: str) -> List[ConversationalSample]:
        """生成T2状态更新样本。"""
        results = []
        
        # 分析时态
        tense_info = self.loader.analyze_tense(context)
        time_anchor = self.loader.extract_time_anchor(context)
        
        # T2-Convo-Tense: 从时态推断状态
        if tense_info["past_tense"]:
            conv = self._create_tense_inference_conversation(
                context, question, answers, label, tense_info, time_anchor, sample_id
            )
            results.append(conv)
        
        # T2-Convo-StateTimeline: 时间线状态
        if time_anchor:
            conv = self._create_timeline_conversation(
                context, question, answers, label, time_anchor, sample_id
            )
            results.append(conv)
        
        return results
    
    def _create_tense_inference_conversation(self, context: str, question: str,
                                              answers: List[str], label: int,
                                              tense_info: Dict, time_anchor: Optional[str],
                                              sample_id: str) -> ConversationalSample:
        """创建时态推断对话。"""
        past_verbs = tense_info.get("past_tense", [])[:3]  # 取前3个
        
        conversation = []
        
        # 第一人称转化
        context_first_person = context.replace("This person", "I").replace("this person", "I")
        
        # 提供叙事上下文
        sentences = context_first_person.split('. ')[:3]
        for sentence in sentences:
            if sentence.strip():
                conversation.append({
                    "role": "user",
                    "content": sentence.strip() + "."
                })
        
        # 干扰对话
        conversation.append({
            "role": "user",
            "content": "Anyway, what do you think about the weather today?"
        })
        conversation.append({
            "role": "assistant",
            "content": "I don't have access to current weather information."
        })
        
        # 核心问题：基于时态推断状态
        if past_verbs:
            question_text = f"I mentioned that I {', '.join(past_verbs[:2])}. Is this something that already happened or will happen?"
            answer_text = f"Already happened (past tense verbs: {', '.join(past_verbs[:2])})"
        else:
            question_text = "Based on what I described, what is my current state?"
            answer_text = answers[label] if label < len(answers) else "Unknown"
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Tense",
            context=context,
            conversation=conversation,
            query=question_text,
            answer=answer_text,
            state_info={
                "type": "tense_inference",
                "past_verbs": past_verbs,
                "time_anchor": time_anchor
            },
            ground_truth={
                "tense": "past",
                "verbs": past_verbs
            },
            difficulty="medium",
            source_id=f"cosmos_t2_tense_{sample_id[:20]}"
        )
    
    def _create_timeline_conversation(self, context: str, question: str,
                                       answers: List[str], label: int,
                                       time_anchor: str, sample_id: str) -> ConversationalSample:
        """创建时间线状态对话。"""
        conversation = []
        
        # 提取时间锚点相关的状态
        context_first_person = context.replace("This person", "I").replace("this person", "I")
        
        conversation.append({
            "role": "user",
            "content": f"Let me tell you what happened {time_anchor}."
        })
        
        # 分段叙述
        sentences = context_first_person.split('. ')
        for i, sentence in enumerate(sentences[:4]):
            if sentence.strip():
                conversation.append({
                    "role": "user",
                    "content": sentence.strip() + "."
                })
                if i == 1:
                    conversation.append({
                        "role": "assistant",
                        "content": "I see, that's interesting."
                    })
        
        # 干扰
        conversation.append({
            "role": "user",
            "content": "By the way, I had pizza for lunch."
        })
        conversation.append({
            "role": "assistant",
            "content": "I see."
        })
        
        # 问题：时间点状态
        question_text = f"At the time '{time_anchor}', what was I doing?"
        
        # 从上下文推断状态
        answer_text = "Based on the context, I was engaged in the described activity."
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Timeline",
            context=context,
            conversation=conversation,
            query=question_text,
            answer=answer_text,
            state_info={
                "type": "timeline_state",
                "time_anchor": time_anchor
            },
            ground_truth={
                "time_anchor": time_anchor,
                "context_summary": context[:200]
            },
            difficulty="hard",
            source_id=f"cosmos_t2_timeline_{sample_id[:20]}"
        )
    
    # =====================================================================
    # T4: 长期记忆 (Long-context Retrieval)
    # =====================================================================
    
    def _generate_t4_samples(self, context: str, question: str,
                             answers: List[str], label: int,
                             sample_id: str) -> List[ConversationalSample]:
        """生成T4长期记忆样本。"""
        results = []
        
        time_anchor = self.loader.extract_time_anchor(context)
        
        # T4-Convo-Buried: 埋藏时间钩子
        conv = self._create_buried_time_conversation(
            context, question, answers, label, time_anchor, sample_id
        )
        results.append(conv)
        
        # T4-Convo-Noisy: 噪声叙事中的信息提取
        conv = self._create_noisy_retrieval_conversation(
            context, question, answers, label, sample_id
        )
        results.append(conv)
        
        return results
    
    def _create_buried_time_conversation(self, context: str, question: str,
                                         answers: List[str], label: int,
                                         time_anchor: Optional[str],
                                         sample_id: str) -> ConversationalSample:
        """创建埋藏时间钩子对话。"""
        conversation = []
        
        # 在对话开头插入时间信息
        if time_anchor:
            conversation.append({
                "role": "user",
                "content": f"By the way, {time_anchor} I had something planned."
            })
        else:
            conversation.append({
                "role": "user",
                "content": "Last week, I had an important event."
            })
        
        # 大量叙事背景（作为噪声）
        context_first_person = context.replace("This person", "I").replace("this person", "I")
        sentences = context_first_person.split('. ')
        
        # 前6-8轮是叙事背景
        for i, sentence in enumerate(sentences[:6]):
            if sentence.strip():
                conversation.append({
                    "role": "user",
                    "content": sentence.strip() + "."
                })
                if i % 2 == 1:
                    conversation.append({
                        "role": "assistant",
                        "content": "I understand, please continue."
                    })
        
        # 更多的无关对话（噪声）
        conversation.append({
            "role": "user",
            "content": "That reminds me, I also watched a movie recently."
        })
        conversation.append({
            "role": "assistant",
            "content": "What movie was it?"
        })
        conversation.append({
            "role": "user",
            "content": "Just a random comedy, nothing special."
        })
        conversation.append({
            "role": "assistant",
            "content": "I see."
        })
        
        # 关键问题：测试是否能记住开头的时间信息
        if time_anchor:
            question_text = f"Earlier I mentioned something about {time_anchor}. What was it?"
        else:
            question_text = "What important event did I mention earlier?"
        
        return ConversationalSample(
            task="T4",
            sub_task="T4-Convo-Buried",
            context=context,
            conversation=conversation,
            query=question_text,
            answer="I had something planned" if time_anchor else "I had an important event",
            state_info={
                "type": "buried_time",
                "time_anchor": time_anchor,
                "narrative_length": len(sentences)
            },
            ground_truth={
                "time_info": time_anchor,
                "position": "beginning"
            },
            difficulty="hard",
            source_id=f"cosmos_t4_buried_{sample_id[:20]}"
        )
    
    def _create_noisy_retrieval_conversation(self, context: str, question: str,
                                             answers: List[str], label: int,
                                             sample_id: str) -> ConversationalSample:
        """创建噪声叙事中的信息提取对话。"""
        conversation = []
        
        context_first_person = context.replace("This person", "I").replace("this person", "I")
        sentences = context_first_person.split('. ')
        
        # 分多次输入，中间插入噪声
        for i, sentence in enumerate(sentences[:5]):
            if sentence.strip():
                conversation.append({
                    "role": "user",
                    "content": sentence.strip() + "."
                })
            
            # 每隔一句插入噪声
            if i % 2 == 1:
                noise = random.choice([
                    "Oh, and I also need to buy groceries later.",
                    "By the way, what's your favorite color?",
                    "I was thinking about dinner too.",
                    "The weather has been strange lately.",
                    "I need to call my friend tomorrow."
                ])
                conversation.append({
                    "role": "user",
                    "content": noise
                })
                conversation.append({
                    "role": "assistant",
                    "content": random.choice([
                        "Okay, noted.",
                        "I see.",
                        "That's interesting.",
                        "Got it."
                    ])
                })
        
        # 问原始问题（来自CosmosQA）
        conversation.append({
            "role": "user",
            "content": question
        })
        
        answer_text = answers[label] if label < len(answers) else "Unknown"
        
        return ConversationalSample(
            task="T4",
            sub_task="T4-Convo-Noisy",
            context=context,
            conversation=conversation,
            query=question,
            answer=answer_text,
            state_info={
                "type": "noisy_retrieval",
                "original_question": question,
                "noise_count": 3
            },
            ground_truth={
                "correct_answer": label,
                "options": answers
            },
            difficulty="very_hard",
            source_id=f"cosmos_t4_noisy_{sample_id[:20]}"
        )
    
    # =====================================================================
    # T5: 反事实 (Counterfactual Emotion-Behavior)
    # =====================================================================
    
    def _generate_t5_samples(self, context: str, question: str,
                             answers: List[str], label: int,
                             sample_id: str) -> List[ConversationalSample]:
        """生成T5反事实样本。"""
        results = []
        
        emotion_patterns = self.loader.detect_emotion_pattern(context)
        
        # T5-Convo-Emotion: 情感-行为反转
        if emotion_patterns:
            conv = self._create_emotion_reverse_conversation(
                context, question, answers, label, emotion_patterns, sample_id
            )
            results.append(conv)
        
        # T5-Convo-Rule: 反事实规则
        conv = self._create_counterfactual_rule_conversation(
            context, question, answers, label, sample_id
        )
        results.append(conv)
        
        return results
    
    def _create_emotion_reverse_conversation(self, context: str, question: str,
                                              answers: List[str], label: int,
                                              emotion_patterns: List[Dict],
                                              sample_id: str) -> ConversationalSample:
        """创建情感-行为反转对话。"""
        conversation = []
        
        context_first_person = context.replace("This person", "I").replace("this person", "I")
        
        # 描述情绪场景
        emotion = emotion_patterns[0]["emotion"]
        keyword = emotion_patterns[0]["keyword"]
        
        conversation.append({
            "role": "user",
            "content": f"Let me tell you about my experience. {context_first_person}"
        })
        conversation.append({
            "role": "assistant",
            "content": f"I see, you felt {emotion}."
        })
        
        # 正常规则
        conversation.append({
            "role": "user",
            "content": f"I {keyword} about this experience."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Normal reaction: when feeling {emotion}, people respond accordingly."
        })
        
        # 反事实规则
        inverted_emotion = self._invert_emotion(emotion)
        conversation.append({
            "role": "user",
            "content": f"But wait! In this hypothetical world, feeling {emotion} means the OPPOSITE."
        })
        conversation.append({
            "role": "assistant",
            "content": f"Noted: in this world, {emotion} → {inverted_emotion}."
        })
        
        # 核心问题
        question_text = f"In this hypothetical world where {emotion} means {inverted_emotion}, how should I interpret my feeling?"
        answer_text = f"You are feeling {inverted_emotion} (not {emotion})"
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-Emotion",
            context=context,
            conversation=conversation,
            query=question_text,
            answer=answer_text,
            state_info={
                "type": "emotion_reverse",
                "original_emotion": emotion,
                "inverted_emotion": inverted_emotion
            },
            ground_truth={
                "emotion_pattern": emotion_patterns,
                "is_counterfactual": True
            },
            difficulty="hard",
            source_id=f"cosmos_t5_emotion_{sample_id[:20]}"
        )
    
    def _create_counterfactual_rule_conversation(self, context: str, question: str,
                                                  answers: List[str], label: int,
                                                  sample_id: str) -> ConversationalSample:
        """创建反事实规则对话。"""
        conversation = []
        
        context_first_person = context.replace("This person", "I").replace("this person", "I")
        
        # 假设规则
        conversation.append({
            "role": "user",
            "content": "Let's imagine a world with different social rules."
        })
        conversation.append({
            "role": "assistant",
            "content": "Okay, what are the rules?"
        })
        
        # 插入上下文
        conversation.append({
            "role": "user",
            "content": f"In this world: {context_first_person[:150]}..."
        })
        
        # 反事实规则
        conversation.append({
            "role": "user",
            "content": "But in REALITY, people react normally. In this HYPOTHETICAL world:"
        })
        conversation.append({
            "role": "user",
            "content": "If something makes you happy → You should avoid it."
        })
        conversation.append({
            "role": "user",
            "content": "If something makes you sad → You should seek more of it."
        })
        conversation.append({
            "role": "assistant",
            "content": "Understood: emotions are reversed in this world."
        })
        
        # 核心问题
        question_text = "In this hypothetical world, what behavior should I choose?"
        answer_text = "Follow the reversed emotional rules (opposite of normal behavior)"
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-Rule",
            context=context,
            conversation=conversation,
            query=question_text,
            answer=answer_text,
            state_info={
                "type": "counterfactual_rule",
                "rule": "emotions_reversed"
            },
            ground_truth={
                "is_counterfactual": True,
                "rule_type": "emotion_behavior"
            },
            difficulty="very_hard",
            source_id=f"cosmos_t5_rule_{sample_id[:20]}"
        )
    
    def _invert_emotion(self, emotion: str) -> str:
        """反转情感。"""
        inversion_map = {
            "happy": "sad",
            "sad": "happy",
            "angry": "pleased",
            "surprised": "expecting",
            "scared": "brave"
        }
        return inversion_map.get(emotion, emotion)


def main():
    """主函数。"""
    print("="*60)
    print("CosmosQA Conversational Temporal Data Converter")
    print("="*60)
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载数据
    loader = CosmosQALoader(DATA_DIR)
    df = loader.load("train")
    
    # 只使用部分数据（太大）
    df = df.head(5000)
    print(f"Using {len(df)} samples for conversion")
    
    # 转换
    converter = CosmosQAConversationalConverter(df)
    samples = converter.convert_all()
    
    # 保存
    output_file = OUTPUT_DIR / "cosmosqa_conversational.jsonl"
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
    
    report_file = OUTPUT_DIR / "cosmosqa_conversational_report.json"
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