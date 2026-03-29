"""五大时间推理任务的生成器

基于 arich.md 的设计，实现:
- T1: 时间计算 (Temporal Calculation)
- T2: 状态更新 (State Tracking)  
- T3: 并发冲突 (Concurrency)
- T4: 长期记忆 (Long-term Memory)
- T5: 反事实 (Counterfactual)
"""

import json
import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from .task_schema import TemporalSample, TaskType, DifficultyLevel, ALL_SUBTASKS
from llm_client import call_llm_json


@dataclass
class TaskConfig:
    """任务配置"""
    task_type: TaskType
    difficulty: DifficultyLevel = DifficultyLevel.EASY
    num_samples: int = 100
    seed: int = 42
    
    def __post_init__(self):
        random.seed(self.seed)


class BaseTaskGenerator:
    """任务生成器基类"""
    
    PROMPT_TEMPLATE = ""
    
    def __init__(self, config: TaskConfig):
        self.config = config
        self.rng = random.Random(config.seed)
    
    def generate(self) -> List[TemporalSample]:
        """生成样本"""
        raise NotImplementedError
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> Optional[Dict]:
        """调用LLM生成"""
        try:
            return call_llm_json(prompt, system_prompt or self.SYSTEM_PROMPT)
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return None
    
    def _format_sample(self, sample_id: int, data: Dict) -> TemporalSample:
        """格式化样本"""
        raise NotImplementedError


class T1TemporalCalculationGenerator(BaseTaskGenerator):
    """T1: 时间计算生成器
    
    子任务:
    - T1-1 Duration: 持续时间计算
    - T1-2 Offset: 时间偏移计算
    - T1-3 Ordering: 事件排序
    """
    
    SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器，专门生成时间计算类题目。

核心要求：
1. 测试基础时间运算能力（duration/offset/ordering）
2. 题目必须基于真实世界的时间规律
3. 确保答案唯一且正确
4. 错误选项应该有明确的错误原因

输出格式：
{
    "context": "上下文描述",
    "delta_t": "时间推进量（如有）",
    "event": "事件描述（如有）",
    "query": "问题",
    "answer": "正确答案",
    "ground_truth": {
        "calculation": "计算过程",
        "time_unit": "时间单位"
    }
}"""
    
    def generate(self, subtask: str = "duration") -> List[TemporalSample]:
        """生成时间计算类样本
        
        Args:
            subtask: 子任务类型 ("duration", "offset", "ordering")
        """
        samples = []
        
        subtask_config = ALL_SUBTASKS[TaskType.T1_TEMPORAL_CALCULATION].get(subtask)
        if not subtask_config:
            return samples
        
        difficulty_config = subtask_config.difficulty_settings.get(self.config.difficulty, {})
        steps = difficulty_config.get("steps", 1)
        
        for i in range(self.config.num_samples):
            prompt = self._build_prompt(subtask, steps, difficulty_config)
            result = self._call_llm(prompt)
            
            if result:
                sample = self._format_sample(f"t1_{subtask}_{i:04d}", result, subtask)
                if sample:
                    samples.append(sample)
        
        return samples
    
    def _build_prompt(self, subtask: str, steps: int, difficulty_config: Dict) -> str:
        """构建prompt"""
        if subtask == "duration":
            return self._build_duration_prompt(steps, difficulty_config)
        elif subtask == "offset":
            return self._build_offset_prompt(steps, difficulty_config)
        elif subtask == "ordering":
            return self._build_ordering_prompt(steps, difficulty_config)
        return ""
    
    def _build_duration_prompt(self, steps: int, config: Dict) -> str:
        """构建持续时间计算prompt"""
        unit_mix = config.get("unit_mix", False)
        nested = config.get("nested", False)
        
        unit_info = "（时间单位可以混合：分钟、小时、天）" if unit_mix else ""
        nested_info = "可以包含嵌套的时间计算" if nested else ""
        
        return f"""生成一道持续时间计算题目。

要求：
- 步数: {steps} 步计算{unit_info}{nested_info}
- 场景贴近日常生活
- 答案必须唯一

请生成JSON格式：
{{
    "context": "场景描述（如：会议安排、烹饪步骤等）",
    "delta_t": "总时间或各步骤时间",
    "query": "什么时候结束/需要多久等问题",
    "answer": "正确答案",
    "ground_truth": {{
        "calculation": "具体计算过程",
        "time_unit": "时间单位"
    }}
}}"""
    
    def _build_offset_prompt(self, steps: int, config: Dict) -> str:
        """构建时间偏移计算prompt"""
        unit_mix = config.get("unit_mix", False)
        
        unit_info = "（时间单位可以混合）" if unit_mix else ""
        
        return f"""生成一道时间偏移计算题目。

要求：
- 步数: {steps} 步计算{unit_info}
- 给定当前时间，计算未来/过去的时间
- 答案必须唯一

请生成JSON格式：
{{
    "context": "当前时间或日期",
    "delta_t": "时间偏移量",
    "query": "计算后的时间/日期",
    "answer": "正确答案",
    "ground_truth": {{
        "calculation": "计算过程"
    }}
}}"""
    
    def _build_ordering_prompt(self, steps: int, config: Dict) -> str:
        """构建事件排序prompt"""
        events = config.get("events", 3)
        
        return f"""生成一道事件排序题目。

要求：
- 包含 {events} 个事件
- 事件之间有明确的时间先后关系
- 问题问谁最早/最晚/在谁之前/之后等

请生成JSON格式：
{{
    "context": "事件列表及其关系描述",
    "query": "排序问题",
    "answer": "正确答案",
    "ground_truth": {{
        "correct_order": ["事件1", "事件2", ...],
        "reasoning": "推理过程"
    }}
}}"""
    
    def _format_sample(self, sample_id: str, data: Dict, subtask: str) -> Optional[TemporalSample]:
        """格式化样本"""
        if not all(k in data for k in ["context", "query", "answer"]):
            return None
        
        return TemporalSample(
            id=sample_id,
            task_type=TaskType.T1_TEMPORAL_CALCULATION,
            context=data.get("context", ""),
            delta_t=data.get("delta_t"),
            event=data.get("event"),
            query=data.get("query", ""),
            answer=data.get("answer"),
            ground_truth=data.get("ground_truth"),
            metadata={"subtask": subtask, "difficulty": self.config.difficulty.value}
        )


class T2StateTrackingGenerator(BaseTaskGenerator):
    """T2: 状态更新生成器
    
    测试模型是否能随着时间正确更新世界状态
    """
    
    SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器，专门生成状态更新类题目。

核心要求：
1. 给定初始状态和一系列带时间戳的事件
2. 测试模型是否能正确追踪状态变化
3. 状态可以是位置、属性、关系等
4. 确保状态更新逻辑一致

输出格式：
{
    "context": "初始状态和事件序列",
    "query": "查询状态的问题",
    "answer": "正确答案",
    "state": {"关键状态字段": "值"},
    "ground_truth": {
        "timeline": [...],
        "final_state": {...}
    }
}"""
    
    def generate(self, subtask: str = "location") -> List[TemporalSample]:
        """生成状态更新类样本"""
        samples = []
        
        subtask_config = ALL_SUBTASKS[TaskType.T2_STATE_TRACKING].get(subtask)
        if not subtask_config:
            return samples
        
        difficulty_config = subtask_config.difficulty_settings.get(self.config.difficulty, {})
        steps = difficulty_config.get("steps", 3)
        entities = difficulty_config.get("entities", 1)
        
        for i in range(self.config.num_samples):
            prompt = self._build_prompt(subtask, steps, entities, difficulty_config)
            result = self._call_llm(prompt)
            
            if result:
                sample = self._format_sample(f"t2_{subtask}_{i:04d}", result, subtask)
                if sample:
                    samples.append(sample)
        
        return samples
    
    def _build_prompt(self, subtask: str, steps: int, entities: int, config: Dict) -> str:
        """构建prompt"""
        return f"""生成一道状态追踪题目。

要求：
- 步数: {steps} 步状态变化
- 实体数: {entities} 个
- 场景：{subtask}

请生成JSON格式：
{{
    "context": "初始状态和{steps}个事件的时间序列",
    "query": "某个时间点的状态查询",
    "answer": "正确答案",
    "state": {{"location": "...", "status": "..."}},
    "ground_truth": {{
        "timeline": [
            {{"time": "时间1", "state": {{...}}}},
            ...
        ],
        "final_state": {{...}}
    }}
}}"""
    
    def _format_sample(self, sample_id: str, data: Dict, subtask: str) -> Optional[TemporalSample]:
        """格式化样本"""
        if not all(k in data for k in ["context", "query", "answer"]):
            return None
        
        return TemporalSample(
            id=sample_id,
            task_type=TaskType.T2_STATE_TRACKING,
            context=data.get("context", ""),
            query=data.get("query", ""),
            answer=data.get("answer"),
            state=data.get("state"),
            ground_truth=data.get("ground_truth"),
            metadata={"subtask": subtask, "difficulty": self.config.difficulty.value}
        )


class T3ConcurrencyGenerator(BaseTaskGenerator):
    """T3: 并发冲突生成器
    
    测试模型是否理解现实世界约束（不能同时做两件冲突的事）
    
    子任务:
    - T3-1: 空间冲突
    - T3-2: 资源冲突
    - T3-3: 注意力冲突
    """
    
    SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器，专门生成并发冲突类题目。

核心要求：
1. 测试模型对现实世界物理约束的理解
2. 包含空间冲突、资源冲突、注意力冲突等类型
3. 要求模型识别冲突或给出合理的冲突解决方案
4. 场景要贴近真实生活

输出格式：
{
    "context": "场景描述",
    "event": "当前/计划的事件",
    "query": "冲突检测/解决相关问题",
    "answer": "答案",
    "ground_truth": {
        "conflict_type": "冲突类型",
        "is_conflict": true/false,
        "reasoning": "推理过程"
    }
}"""
    
    def generate(self, subtask: str = "space_conflict") -> List[TemporalSample]:
        """生成并发冲突类样本"""
        samples = []
        
        subtask_config = ALL_SUBTASKS[TaskType.T3_CONCURRENCY].get(subtask)
        if not subtask_config:
            return samples
        
        difficulty_config = subtask_config.difficulty_settings.get(self.config.difficulty, {})
        
        for i in range(self.config.num_samples):
            prompt = self._build_prompt(subtask, difficulty_config)
            result = self._call_llm(prompt)
            
            if result:
                sample = self._format_sample(f"t3_{subtask}_{i:04d}", result, subtask)
                if sample:
                    samples.append(sample)
        
        return samples
    
    def _build_prompt(self, subtask: str, config: Dict) -> str:
        """构建prompt"""
        explicit = "显式冲突" if config.get("explicit", True) else "隐含冲突"
        
        if subtask == "space_conflict":
            scenario = "同一个人同时出现在不同地点"
        elif subtask == "resource_conflict":
            scenario = "共享资源被占用"
        elif subtask == "attention_conflict":
            scenario = "需要高度注意力同时进行的多任务"
        else:
            scenario = "并发事件冲突"
        
        return f"""生成一道{ALL_SUBTASKS[TaskType.T3_CONCURRENCY][subtask].name}题目。

要求：
- 冲突类型: {scenario}
- 难度: {explicit}
- 场景贴近真实生活

请生成JSON格式：
{{
    "context": "场景描述，包含冲突事件",
    "query": "是否合理/如何解决等问题",
    "answer": "答案",
    "ground_truth": {{
        "conflict_type": "{subtask}",
        "is_conflict": true/false,
        "resolution": "解决方案（如有）"
    }}
}}"""
    
    def _format_sample(self, sample_id: str, data: Dict, subtask: str) -> Optional[TemporalSample]:
        """格式化样本"""
        if not all(k in data for k in ["context", "query", "answer"]):
            return None
        
        return TemporalSample(
            id=sample_id,
            task_type=TaskType.T3_CONCURRENCY,
            context=data.get("context", ""),
            event=data.get("event"),
            query=data.get("query", ""),
            answer=data.get("answer"),
            ground_truth=data.get("ground_truth"),
            metadata={"subtask": subtask, "difficulty": self.config.difficulty.value}
        )


class T4LongTermMemoryGenerator(BaseTaskGenerator):
    """T4: 长期记忆生成器
    
    测试模型是否能在长上下文中维持时间信息
    """
    
    SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器，专门生成长期记忆类题目。

核心要求：
1. 测试模型在长上下文中检索和推理时间信息的能力
2. 关键信息可能埋藏在大量无关内容中
3. 需要区分"找不到"、"找到了但错"、"前后不一致"三种失败模式
4. 场景设计要能区分不同类型的失败

输出格式：
{
    "context": "长上下文，包含关键信息和干扰信息",
    "query": "时间相关问题",
    "answer": "正确答案",
    "ground_truth": {
        "key_info_location": "关键信息在原文中的位置",
        "failure_type": "预期可能的失败类型"
    }
}"""
    
    def generate(self, subtask: str = "retrieval") -> List[TemporalSample]:
        """生成长期记忆类样本"""
        samples = []
        
        subtask_config = ALL_SUBTASKS[TaskType.T4_LONG_TERM_MEMORY].get(subtask)
        if not subtask_config:
            return samples
        
        difficulty_config = subtask_config.difficulty_settings.get(self.config.difficulty, {})
        context_length = difficulty_config.get("context_length", "2k")
        noise_ratio = difficulty_config.get("noise_ratio", 0.0)
        
        for i in range(self.config.num_samples):
            prompt = self._build_prompt(context_length, noise_ratio, difficulty_config)
            result = self._call_llm(prompt)
            
            if result:
                sample = self._format_sample(f"t4_{subtask}_{i:04d}", result)
                if sample:
                    samples.append(sample)
        
        return samples
    
    def _build_prompt(self, context_length: str, noise_ratio: float, config: Dict) -> str:
        """构建prompt"""
        return f"""生成一道长期记忆检索题目。

要求：
- 上下文长度: {context_length} tokens
- 噪声比例: {noise_ratio*100:.0f}%
- 包含关键时间信息和大量干扰信息

请生成JSON格式：
{{
    "context": "长上下文文本",
    "query": "关于时间的问题",
    "answer": "正确答案",
    "ground_truth": {{
        "key_info": "关键信息原文",
        "retrieval_hint": "检索提示"
    }}
}}"""
    
    def _format_sample(self, sample_id: str, data: Dict) -> Optional[TemporalSample]:
        """格式化样本"""
        if not all(k in data for k in ["context", "query", "answer"]):
            return None
        
        return TemporalSample(
            id=sample_id,
            task_type=TaskType.T4_LONG_TERM_MEMORY,
            context=data.get("context", ""),
            query=data.get("query", ""),
            answer=data.get("answer"),
            ground_truth=data.get("ground_truth"),
            metadata={"difficulty": self.config.difficulty.value}
        )


class T5CounterfactualGenerator(BaseTaskGenerator):
    """T5: 反事实推理生成器
    
    测试模型是否依赖训练数据还是真正推理
    """
    
    SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器，专门生成反事实/虚构规则类题目。

核心要求：
1. 定义一套与现实不同的虚构规则
2. 在虚构规则下提问
3. 测试模型是否能切换到虚构规则而非依赖训练记忆
4. 对照组包括Normal（现实规则）和Sandbox（虚构规则）

输出格式：
{
    "context": "世界设定和规则描述",
    "query": "在虚构规则下的问题",
    "answer": "虚构规则下的答案",
    "ground_truth": {
        "fictional_rules": ["规则1", "规则2"],
        "normal_answer": "现实规则下的答案（对照组）"
    }
}"""
    
    def generate(self, subtask: str = "sandbox") -> List[TemporalSample]:
        """生成反事实推理类样本"""
        samples = []
        
        subtask_config = ALL_SUBTASKS[TaskType.T5_COUNTERFACTUAL].get(subtask)
        if not subtask_config:
            return samples
        
        difficulty_config = subtask_config.difficulty_settings.get(self.config.difficulty, {})
        rule_changes = difficulty_config.get("rule_changes", 1)
        
        for i in range(self.config.num_samples):
            prompt = self._build_prompt(rule_changes, difficulty_config)
            result = self._call_llm(prompt)
            
            if result:
                sample = self._format_sample(f"t5_{subtask}_{i:04d}", result)
                if sample:
                    samples.append(sample)
        
        return samples
    
    def _build_prompt(self, rule_changes: int, config: Dict) -> str:
        """构建prompt"""
        return f"""生成一道反事实推理题目。

要求：
- 虚构规则数: {rule_changes} 条
- 规则必须与现实世界不同但内部一致
- 问题必须在虚构规则下回答

请生成JSON格式：
{{
    "context": "虚构世界的规则设定",
    "query": "在虚构规则下的问题",
    "answer": "虚构规则下的正确答案",
    "ground_truth": {{
        "fictional_rules": ["规则1", "规则2"],
        "reasoning": "在虚构规则下的推理过程"
    }}
}}"""
    
    def _format_sample(self, sample_id: str, data: Dict) -> Optional[TemporalSample]:
        """格式化样本"""
        if not all(k in data for k in ["context", "query", "answer"]):
            return None
        
        return TemporalSample(
            id=sample_id,
            task_type=TaskType.T5_COUNTERFACTUAL,
            context=data.get("context", ""),
            query=data.get("query", ""),
            answer=data.get("answer"),
            ground_truth=data.get("ground_truth"),
            metadata={"difficulty": self.config.difficulty.value}
        )


class TaskGeneratorFactory:
    """任务生成器工厂"""
    
    GENERATORS = {
        TaskType.T1_TEMPORAL_CALCULATION: T1TemporalCalculationGenerator,
        TaskType.T2_STATE_TRACKING: T2StateTrackingGenerator,
        TaskType.T3_CONCURRENCY: T3ConcurrencyGenerator,
        TaskType.T4_LONG_TERM_MEMORY: T4LongTermMemoryGenerator,
        TaskType.T5_COUNTERFACTUAL: T5CounterfactualGenerator,
    }
    
    @classmethod
    def create(cls, task_type: TaskType, config: Optional[TaskConfig] = None) -> BaseTaskGenerator:
        """创建任务生成器"""
        generator_class = cls.GENERATORS.get(task_type)
        if not generator_class:
            raise ValueError(f"Unknown task type: {task_type}")
        
        if config is None:
            config = TaskConfig(task_type=task_type)
        
        return generator_class(config)
    
    @classmethod
    def generate_all_tasks(
        cls,
        num_samples_per_task: int = 50,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        seed: int = 42
    ) -> Dict[TaskType, List[TemporalSample]]:
        """生成所有任务类型的样本"""
        results = {}
        
        for task_type in TaskType:
            print(f"生成 {task_type.value}...")
            config = TaskConfig(
                task_type=task_type,
                difficulty=difficulty,
                num_samples=num_samples_per_task,
                seed=seed
            )
            generator = cls.create(task_type, config)
            samples = generator.generate()
            results[task_type] = samples
            print(f"  生成 {len(samples)} 个样本")
        
        return results
