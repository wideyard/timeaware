"""Prompt builder for the Timeaware Benchmark Experiment.

Constructs prompts for three conversation modes:
1. single_turn: context + query (or just query if context is forbidden)
2. multi_turn: full conversation history
3. multi_turn_noise: conversation + injected noise turns
"""

from typing import Dict, List, Any, Optional
from experiment.subtask_config import SUBTASK_CONFIG


def _should_include_context(subtask_key: str) -> bool:
    """Determine if context should be included in single-turn mode."""
    config = SUBTASK_CONFIG.get(subtask_key, {})
    mode = config.get('context_mode', 'optional')
    # 'required' and 'optional' → include context
    # 'forbidden' → don't include
    return mode != 'forbidden'


def build_single_turn_prompt(sample: Dict[str, Any], subtask_key: str) -> str:
    """Build a single-turn prompt.
    
    For retrieval-type tasks (T4, T2-StateTrack with required context):
        context + query
    
    For self-contained tasks (T1-TimeCalc, T2-Progressive, etc.):
        query (context is metadata or already embedded in query)
    """
    include_context = _should_include_context(subtask_key)
    context = sample.get('context', '').strip()
    query = sample.get('query', '').strip()
    
    parts = []
    
    if include_context and context:
        # Check if context is just a short metadata string vs substantive content
        if len(context) > 50:
            parts.append(f"以下是相关背景信息：\n{context}\n")
        else:
            # Short context is likely metadata, include it
            parts.append(f"背景：{context}\n")
    
    parts.append(f"问题：{query}")
    
    return "\n".join(parts)


def build_multi_turn_messages(sample: Dict[str, Any]) -> List[Dict[str, str]]:
    """Build multi-turn messages from the conversation field.
    
    Returns the full conversation history as messages.
    """
    conversation = sample.get('conversation', [])
    if not conversation:
        # Fallback: create a single-turn from query
        return [{"role": "user", "content": sample.get('query', '')}]
    
    return copy_messages(conversation)


def build_multi_turn_noise_messages(sample: Dict[str, Any]) -> List[Dict[str, str]]:
    """Build multi-turn messages with injected noise.
    
    The sample should already have noise injected via noise_injector.
    """
    conversation = sample.get('conversation', [])
    if not conversation:
        return [{"role": "user", "content": sample.get('query', '')}]
    
    return copy_messages(conversation)


def copy_messages(conversation: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Deep copy conversation messages."""
    return [{"role": msg["role"], "content": msg["content"]} for msg in conversation]


def build_system_prompt(subtask_key: str, sample: Dict[str, Any]) -> str:
    """Build a system prompt tailored to the subtask type."""
    config = SUBTASK_CONFIG.get(subtask_key, {})
    dimension = config.get('dimension', '')
    
    base_prompt = "你是一个时间推理和状态追踪方面的专家。请仔细分析问题，给出准确答案。"
    
    dimension_prompts = {
        "T1": "你擅长时间计算，包括时长计算、事件排序、时间偏移等。请仔细计算并给出答案。",
        "T2": "你擅长状态追踪，需要跟踪人物、物品或事件在不同时间点的状态变化。请仔细分析状态历史。",
        "T3": "你擅长冲突检测与消解，需要识别时间、空间或资源上的冲突。请仔细分析冲突情况。",
        "T4": "你擅长从长文本中检索和回忆关键信息。请仔细阅读材料，准确回忆相关信息。",
        "T5": "你擅长反事实推理，需要在假设或反转的规则下进行推理。请仔细理解规则变化。",
    }
    
    return dimension_prompts.get(dimension, base_prompt)


def build_messages_for_mode(sample: Dict[str, Any], subtask_key: str, 
                             mode: str) -> List[Dict[str, str]]:
    """Build messages for a given conversation mode.
    
    Args:
        sample: The data sample
        subtask_key: The merged subtask key (e.g., "T1-Ordering")
        mode: One of 'single_turn', 'multi_turn', 'multi_turn_noise'
    
    Returns:
        List of message dicts for the LLM API
    """
    system_prompt = build_system_prompt(subtask_key, sample)
    
    if mode == "single_turn":
        user_content = build_single_turn_prompt(sample, subtask_key)
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
    
    elif mode == "multi_turn":
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(build_multi_turn_messages(sample))
        return messages
    
    elif mode == "multi_turn_noise":
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(build_multi_turn_noise_messages(sample))
        return messages
    
    else:
        raise ValueError(f"Unknown mode: {mode}")


def extract_answer_format(sample: Dict[str, Any]) -> str:
    """Determine the expected answer format for a sample.
    
    Returns guidance for the LLM on how to format its answer.
    """
    answer = sample.get('answer', '')
    ground_truth = sample.get('ground_truth', {})
    
    # Check if it's a multiple choice question
    options = ground_truth.get('options', [])
    if options:
        return "multiple_choice"
    
    # Check if the ground_truth has letter-based answers
    correct_letter = ground_truth.get('correct_letter', '')
    if correct_letter:
        return "multiple_choice_letter"
    
    # Check if answer is short (likely exact match)
    if len(answer) < 50:
        return "short_answer"
    
    return "open_ended"
