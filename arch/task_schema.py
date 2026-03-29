"""统一的时间推理任务框架配置

基于 arich.md 的设计，统一所有任务的输入输出格式和评测标准。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
import json


class TaskType(Enum):
    """五大任务类型"""
    T1_TEMPORAL_CALCULATION = "t1_temporal_calculation"  # 时间计算
    T2_STATE_TRACKING = "t2_state_tracking"  # 状态更新
    T3_CONCURRENCY = "t3_concurrency"  # 并发冲突
    T4_LONG_TERM_MEMORY = "t4_long_term_memory"  # 长期记忆
    T5_COUNTERFACTUAL = "t5_counterfactual"  # 反事实


class DifficultyLevel(Enum):
    """难度级别"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class TemporalSample:
    """统一的时间推理样本格式
    
    所有任务必须遵循此格式。
    """
    id: str
    task_type: TaskType
    
    # ===== 输入格式 =====
    context: str  # 对话历史/上下文
    delta_t: Optional[str] = None  # 时间推进量 (如 "3天", "2小时")
    event: Optional[str] = None  # 事件描述 (如 "张三去北京")
    query: str = ""  # 问题
    
    # ===== 输出格式 =====
    answer: Optional[str] = None
    state: Optional[Dict[str, Any]] = None  # 状态信息
    reasoning: Optional[str] = None  # 推理过程
    
    # ===== 元数据 =====
    ground_truth: Optional[Dict[str, Any]] = None  # 真实答案
    metadata: Dict[str, Any] = field(default_factory=dict)  # 其他信息
    
    def to_input_format(self) -> str:
        """转换为统一输入格式"""
        parts = []
        if self.context:
            parts.append(f"[Context]\n{self.context}")
        if self.delta_t:
            parts.append(f"[时间推进]\n{self.delta_t}")
        if self.event:
            parts.append(f"[事件]\n{self.event}")
        if self.query:
            parts.append(f"[问题]\n{self.query}")
        return "\n\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "task_type": self.task_type.value,
            "input": self.to_input_format(),
            "context": self.context,
            "delta_t": self.delta_t,
            "event": self.event,
            "query": self.query,
            "answer": self.answer,
            "state": self.state,
            "reasoning": self.reasoning,
            "ground_truth": self.ground_truth,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemporalSample":
        """从字典创建"""
        task_type = data.get("task_type", "")
        if isinstance(task_type, str):
            task_type = TaskType(task_type)
        return cls(
            id=data.get("id", ""),
            task_type=task_type,
            context=data.get("context", ""),
            delta_t=data.get("delta_t"),
            event=data.get("event"),
            query=data.get("query", ""),
            answer=data.get("answer"),
            state=data.get("state"),
            reasoning=data.get("reasoning"),
            ground_truth=data.get("ground_truth"),
            metadata=data.get("metadata", {})
        )


@dataclass
class SubTaskConfig:
    """子任务配置"""
    name: str
    description: str
    prompt_template: str
    difficulty_settings: Dict[DifficultyLevel, Dict[str, Any]]


# ===== T1: 时间计算 子任务配置 =====
T1_SUBTASKS = {
    "duration": SubTaskConfig(
        name="T1-1 Duration",
        description="持续时间计算",
        prompt_template="会议{start_time}开始，持续{duration}，什么时候结束？",
        difficulty_settings={
            DifficultyLevel.EASY: {"steps": 1, "unit_mix": False, "nested": False},
            DifficultyLevel.MEDIUM: {"steps": 2, "unit_mix": True, "nested": False},
            DifficultyLevel.HARD: {"steps": 3, "unit_mix": True, "nested": True},
        }
    ),
    "offset": SubTaskConfig(
        name="T1-2 Temporal Offset",
        description="时间偏移计算",
        prompt_template="如果现在是{current_time}，{delta}后是？",
        difficulty_settings={
            DifficultyLevel.EASY: {"steps": 1, "unit_mix": False, "nested": False},
            DifficultyLevel.MEDIUM: {"steps": 2, "unit_mix": True, "nested": False},
            DifficultyLevel.HARD: {"steps": 3, "unit_mix": True, "nested": True},
        }
    ),
    "ordering": SubTaskConfig(
        name="T1-3 Ordering",
        description="事件排序",
        prompt_template="A发生在B之前，B发生在C之后，谁最早？",
        difficulty_settings={
            DifficultyLevel.EASY: {"steps": 1, "events": 3},
            DifficultyLevel.MEDIUM: {"steps": 2, "events": 5},
            DifficultyLevel.HARD: {"steps": 3, "events": 7},
        }
    ),
}

# ===== T2: 状态更新 子任务配置 =====
T2_SUBTASKS = {
    "location": SubTaskConfig(
        name="T2-1 Location Tracking",
        description="位置状态跟踪",
        prompt_template="{time} {person}在{location}。{delta}后在哪里？",
        difficulty_settings={
            DifficultyLevel.EASY: {"steps": 3, "entities": 1},
            DifficultyLevel.MEDIUM: {"steps": 5, "entities": 2},
            DifficultyLevel.HARD: {"steps": 10, "entities": 3},
        }
    ),
    "status": SubTaskConfig(
        name="T2-2 Status Tracking",
        description="状态属性跟踪",
        prompt_template="{person}是{initial_status}。{events}。现在{time}，{person}的状态是？",
        difficulty_settings={
            DifficultyLevel.EASY: {"steps": 3, "entities": 1},
            DifficultyLevel.MEDIUM: {"steps": 5, "entities": 2},
            DifficultyLevel.HARD: {"steps": 10, "entities": 3},
        }
    ),
}

# ===== T3: 并发冲突 子任务配置 =====
T3_SUBTASKS = {
    "space_conflict": SubTaskConfig(
        name="T3-1 Space Conflict",
        description="空间冲突检测",
        prompt_template="{time} {person}在A地。{time} {person}在B地。是否合理？",
        difficulty_settings={
            DifficultyLevel.EASY: {"explicit": True},
            DifficultyLevel.HARD: {"explicit": False},
        }
    ),
    "resource_conflict": SubTaskConfig(
        name="T3-2 Resource Conflict",
        description="资源冲突检测",
        prompt_template="{resource}已被占用。{person}还能用吗？",
        difficulty_settings={
            DifficultyLevel.EASY: {"explicit": True},
            DifficultyLevel.HARD: {"explicit": False},
        }
    ),
    "attention_conflict": SubTaskConfig(
        name="T3-3 Attention Conflict",
        description="注意力冲突检测",
        prompt_template="{time} {person}在做{activity1}。{time} {person}在做{activity2}。是否合理？",
        difficulty_settings={
            DifficultyLevel.EASY: {"explicit": True},
            DifficultyLevel.HARD: {"explicit": False},
        }
    ),
}

# ===== T4: 长期记忆 子任务配置 =====
T4_SUBTASKS = {
    "retrieval": SubTaskConfig(
        name="T4-1 Information Retrieval",
        description="信息检索",
        prompt_template="{early_event}...(大量无关内容)...{query}",
        difficulty_settings={
            DifficultyLevel.EASY: {"context_length": "2k", "noise_ratio": 0.0},
            DifficultyLevel.MEDIUM: {"context_length": "8k", "noise_ratio": 0.5},
            DifficultyLevel.HARD: {"context_length": "32k", "noise_ratio": 0.8},
        }
    ),
}

# ===== T5: 反事实 子任务配置 =====
T5_SUBTASKS = {
    "sandbox": SubTaskConfig(
        name="T5-1 Counterfactual Reasoning",
        description="反事实推理",
        prompt_template="在{alternate_world}中：{fictional_rules}。问：{question}",
        difficulty_settings={
            DifficultyLevel.EASY: {"rule_changes": 1},
            DifficultyLevel.MEDIUM: {"rule_changes": 2},
            DifficultyLevel.HARD: {"rule_changes": 3},
        }
    ),
}

# 所有子任务配置
ALL_SUBTASKS = {
    TaskType.T1_TEMPORAL_CALCULATION: T1_SUBTASKS,
    TaskType.T2_STATE_TRACKING: T2_SUBTASKS,
    TaskType.T3_CONCURRENCY: T3_SUBTASKS,
    TaskType.T4_LONG_TERM_MEMORY: T4_SUBTASKS,
    TaskType.T5_COUNTERFACTUAL: T5_SUBTASKS,
}


# ===== 统一输出格式 Prompt =====
UNIFIED_OUTPUT_PROMPT = """请用JSON格式回答，格式如下：
{
    "answer": "答案",
    "state": {{"字段": "值"}},  // 可选，用于状态追踪任务
    "reasoning": "推理过程"  // 可选，用于一致性分析
}
"""


# ===== 难度级别对应 =====
DIFFICULTY_LABELS = {
    DifficultyLevel.EASY: "简单",
    DifficultyLevel.MEDIUM: "中等",
    DifficultyLevel.HARD: "困难",
}


def get_task_description(task_type: TaskType) -> str:
    """获取任务描述"""
    descriptions = {
        TaskType.T1_TEMPORAL_CALCULATION: "时间计算 - 测试基础时间运算能力",
        TaskType.T2_STATE_TRACKING: "状态更新 - 测试随时间更新世界状态的能力",
        TaskType.T3_CONCURRENCY: "并发冲突 - 测试理解现实世界约束的能力",
        TaskType.T4_LONG_TERM_MEMORY: "长期记忆 - 测试在长上下文中维持时间信息的能力",
        TaskType.T5_COUNTERFACTUAL: "反事实推理 - 测试在虚构规则下的推理能力",
    }
    return descriptions.get(task_type, "")


def get_task_metrics(task_type: TaskType) -> List[str]:
    """获取任务对应的评测指标"""
    metrics_map = {
        TaskType.T1_TEMPORAL_CALCULATION: ["accuracy", "step_accuracy"],
        TaskType.T2_STATE_TRACKING: ["final_accuracy", "state_accuracy", "consistency"],
        TaskType.T3_CONCURRENCY: ["conflict_detection_rate", "resolution_accuracy"],
        TaskType.T4_LONG_TERM_MEMORY: ["retrieval_accuracy", "final_accuracy", "memory_consistency"],
        TaskType.T5_COUNTERFACTUAL: ["accuracy", "consistency"],
    }
    return metrics_map.get(task_type, ["accuracy"])
