"""Noise injection module for the Timeaware Benchmark Experiment.

Injects three types of noise (HistNoise, ConfusionNoise, NumNoise) into
clean conversation data, following the patterns observed in tempreason L1.
"""

import copy
import random
from typing import Dict, List, Any, Optional

# Noise templates - modeled after tempreason L1 patterns
HIST_NOISE_TEMPLATES = [
    {"user": "顺便提一下，1440年古腾堡发明活字印刷术，推动了欧洲文艺复兴。", "assistant": "好的，我了解了这个历史背景。"},
    {"user": "你知道吗，2001年中国加入世界贸易组织，成为全球经济的重要参与者。", "assistant": "好的，我了解了这个历史背景。"},
    {"user": "1969年人类首次登月，这是人类历史上的重要里程碑。", "assistant": "好的，我了解了这个历史背景。"},
    {"user": "我昨天买了一本关于历史的书。", "assistant": "好的，这与当前任务无关，但我会记住这个信息。"},
    {"user": "1776年美国独立宣言发表，标志着美利坚合众国的诞生。", "assistant": "好的，我了解了这个历史背景。"},
    {"user": "1989年柏林墙倒塌，结束了冷战时期的分裂局面。", "assistant": "好的，我了解了这个历史背景。"},
    {"user": "我最近在看一本关于二战历史的书，非常有意思。", "assistant": "好的，这与当前任务无关，但我会记住这个信息。"},
    {"user": "1492年哥伦布发现美洲大陆，开启了大航海时代。", "assistant": "好的，我了解了这个历史背景。"},
]

CONFUSION_NOISE_TEMPLATES = [
    {"user": "（不同来源对具体时间有不同说法）", "assistant": "我注意到这里有关于时间的混淆信息。"},
    {"user": "（有些记录显示时间可能有所不同）", "assistant": "我注意到这里有关于时间的混淆信息。"},
    {"user": "（注意：不同资料对这一时间点的描述存在差异）", "assistant": "我注意到这里有关于时间的混淆信息。"},
    {"user": "（历史上的时间记录有时会有误差）", "assistant": "我注意到这里有关于时间的混淆信息。"},
    {"user": "（需要注意的是，不同来源给出的时间可能不一致）", "assistant": "我注意到这里有关于时间的混淆信息。"},
    {"user": "（有说法认为这个时间可能存在争议）", "assistant": "我注意到这里有关于时间的混淆信息。"},
]

NUM_NOISE_TEMPLATES = [
    {"user": "顺便提一下，这段历史持续了5年，涉及99个重要人物。忽略这些数字，它们与此题无关。", "assistant": "我会忽略无关的数字，专注于当前任务。"},
    {"user": "对了，这个事件发生在3月15日，有256人参加。这些数字与问题无关。", "assistant": "我会忽略无关的数字，专注于当前任务。"},
    {"user": "顺便说一下，这个项目有42个阶段，涉及128个团队。这些数字不需要关注。", "assistant": "我会忽略无关的数字，专注于当前任务。"},
    {"user": "另外，这个过程中涉及7个步骤和36个变量。这些数字与问题无关。", "assistant": "我会忽略无关的数字，专注于当前任务。"},
    {"user": "顺便提一下，总共有88个参与者，分成了12个小组。这些数字与此题无关。", "assistant": "我会忽略无关的数字，专注于当前任务。"},
    {"user": "对了，这个任务需要3次迭代，每次处理64条数据。这些数字不需要关注。", "assistant": "我会忽略无关的数字，专注于当前任务。"},
]


def inject_hist_noise(conversation: List[Dict[str, str]],
                       num_rounds: int = 2,
                       seed: Optional[int] = None) -> List[Dict[str, str]]:
    """Inject historical noise into conversation.
    
    Inserts random historical fact exchanges before the final query turn.
    """
    if seed is not None:
        random.seed(seed)
    
    conv = copy.deepcopy(conversation)
    
    # Find the position to insert noise (before the last user turn that contains the query)
    insert_pos = max(1, len(conv) - 1)
    
    # Pick random noise templates
    noise_rounds = random.sample(HIST_NOISE_TEMPLATES, min(num_rounds, len(HIST_NOISE_TEMPLATES)))
    
    for i, noise in enumerate(noise_rounds):
        insert_idx = insert_pos + i * 2
        conv.insert(insert_idx, {"role": "user", "content": noise["user"]})
        conv.insert(insert_idx + 1, {"role": "assistant", "content": noise["assistant"]})
    
    return conv


def inject_confusion_noise(conversation: List[Dict[str, str]],
                            num_rounds: int = 2,
                            seed: Optional[int] = None) -> List[Dict[str, str]]:
    """Inject confusion noise into conversation.
    
    Inserts time-related confusion statements.
    """
    if seed is not None:
        random.seed(seed)
    
    conv = copy.deepcopy(conversation)
    insert_pos = max(1, len(conv) - 1)
    
    noise_rounds = random.sample(CONFUSION_NOISE_TEMPLATES, min(num_rounds, len(CONFUSION_NOISE_TEMPLATES)))
    
    for i, noise in enumerate(noise_rounds):
        insert_idx = insert_pos + i * 2
        conv.insert(insert_idx, {"role": "user", "content": noise["user"]})
        conv.insert(insert_idx + 1, {"role": "assistant", "content": noise["assistant"]})
    
    return conv


def inject_num_noise(conversation: List[Dict[str, str]],
                      num_rounds: int = 2,
                      seed: Optional[int] = None) -> List[Dict[str, str]]:
    """Inject numeric noise into conversation.
    
    Inserts irrelevant numbers.
    """
    if seed is not None:
        random.seed(seed)
    
    conv = copy.deepcopy(conversation)
    insert_pos = max(1, len(conv) - 1)
    
    noise_rounds = random.sample(NUM_NOISE_TEMPLATES, min(num_rounds, len(NUM_NOISE_TEMPLATES)))
    
    for i, noise in enumerate(noise_rounds):
        insert_idx = insert_pos + i * 2
        conv.insert(insert_idx, {"role": "user", "content": noise["user"]})
        conv.insert(insert_idx + 1, {"role": "assistant", "content": noise["assistant"]})
    
    return conv


NOISE_INJECTORS = {
    "hist_noise": inject_hist_noise,
    "confusion_noise": inject_confusion_noise,
    "num_noise": inject_num_noise,
}


def inject_noise(sample: Dict[str, Any], noise_type: str,
                  num_rounds: int = 2, seed: Optional[int] = None) -> Dict[str, Any]:
    """Inject noise into a sample's conversation.
    
    Args:
        sample: The data sample dict (from jsonl)
        noise_type: One of 'hist_noise', 'confusion_noise', 'num_noise'
        num_rounds: Number of noise exchange rounds to insert
        seed: Random seed for reproducibility
    
    Returns:
        A new sample dict with modified conversation
    """
    injector = NOISE_INJECTORS.get(noise_type)
    if not injector:
        raise ValueError(f"Unknown noise type: {noise_type}. Choose from {list(NOISE_INJECTORS.keys())}")
    
    new_sample = copy.deepcopy(sample)
    conversation = sample.get('conversation', [])
    
    if not conversation:
        return new_sample
    
    new_sample['conversation'] = injector(conversation, num_rounds=num_rounds, seed=seed)
    new_sample['_noise_type'] = noise_type
    new_sample['_noise_rounds'] = num_rounds
    
    return new_sample


def inject_all_noise_types(sample: Dict[str, Any],
                            num_rounds: int = 2,
                            seed: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
    """Inject all three noise types into a sample.
    
    Returns:
        {noise_type: noisy_sample_dict}
    """
    results = {}
    for noise_type in NOISE_INJECTORS.keys():
        results[noise_type] = inject_noise(sample, noise_type, num_rounds=num_rounds, 
                                            seed=hash(noise_type) + (seed or 0))
    return results
