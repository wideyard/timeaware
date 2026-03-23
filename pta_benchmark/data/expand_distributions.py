"""从MCTACO数据扩充活动分布配置"""

import json
import re
import os
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# 时间范围限制（分钟）
MIN_DURATION_MINUTES = 1
MAX_DURATION_MINUTES = 480  # 8小时


@dataclass
class ActivityCandidate:
    """候选活动"""
    original_event: str
    cleaned_event: str
    source_sentence: str
    min_minutes: float
    max_minutes: float
    distribution_type: str  # uniform, normal, lognormal
    distribution_params: Dict[str, float]
    num_samples: int
    quality_score: float
    issues: List[str]
    approved: bool = False


def seconds_to_minutes(seconds: float) -> float:
    """秒转分钟"""
    return seconds / 60.0


def clean_event_name(event: str) -> str:
    """清洗事件名称"""
    # 转小写
    event = event.lower().strip()
    
    # 移除常见问题前缀
    prefixes_to_remove = [
        r'^how long (?:does|did|is|was|has|have)\s+',
        r'^for how long (?:does|did|is|was|has|have)\s+',
        r'^how many (?:hours|minutes|seconds|days|weeks|months|years)\s+(?:does|did|is|was|has|have)\s+',
        r'^how long\s+',
        r'^how many\s+\w+\s+',
    ]
    
    for prefix in prefixes_to_remove:
        event = re.sub(prefix, '', event)
    
    # 移除结尾的问号和"take"/"last"
    event = re.sub(r'\?$', '', event)
    event = re.sub(r'\s+(?:take|last|endure|continue)\s*$', '', event)
    
    # 移除开头的代词+动词组合
    pronoun_patterns = [
        r'^(?:it|he|she|they|we)\s+(?:take|takes|took|does|did|is|was|are|were|has|have|had)\s+(?:him|her|them|us)?\s*(?:to\s+)?',
        r'^(?:it|he|she|they|we)\s+',
        r'^(?:to|for)\s+',
    ]
    
    for pattern in pronoun_patterns:
        event = re.sub(pattern, '', event)
    
    # 移除 "for" 开头的介词短语
    event = re.sub(r'^for\s+', '', event)
    
    # 清理特殊字符（保留字母和空格）
    event = re.sub(r'[^a-z\s]', '', event)
    
    # 清理多余空格
    event = re.sub(r'\s+', ' ', event).strip()
    
    return event


def compute_distribution_params(
    all_seconds: List[float],
    min_seconds: float,
    max_seconds: float
) -> Tuple[str, Dict[str, float], float]:
    """
    计算分布参数
    
    Returns:
        (distribution_type, params, quality_score)
    """
    min_min = seconds_to_minutes(min_seconds)
    max_min = seconds_to_minutes(max_seconds)
    
    issues = []
    quality_score = 1.0
    
    # 只有一个数据点
    if len(all_seconds) <= 1 or min_seconds == max_seconds:
        center = (min_min + max_min) / 2
        return "uniform", {
            "low": round(center * 0.5, 1),
            "high": round(center * 1.5, 1)
        }, 0.6
    
    # 有多个数据点
    values_minutes = [seconds_to_minutes(s) for s in all_seconds]
    mean = np.mean(values_minutes)
    std = np.std(values_minutes)
    
    # 判断分布类型
    if std < mean * 0.1:
        # 标准差很小，接近确定性
        return "uniform", {
            "low": round(min_min, 1),
            "high": round(max_min, 1)
        }, 0.8
    
    # 检查是否右偏（适合LogNormal）
    # 如果max远大于mean，可能是右偏分布
    if max_min > mean * 2:
        return "lognormal", {
            "mean": round(mean, 1),
            "std": round(std, 1)
        }, 0.7
    
    # 默认使用Uniform
    return "uniform", {
        "low": round(min_min, 1),
        "high": round(max_min, 1)
    }, 0.9


def validate_duration_range(min_minutes: float, max_minutes: float) -> Tuple[bool, List[str]]:
    """验证时间范围是否合适"""
    issues = []
    valid = True
    
    if min_minutes < MIN_DURATION_MINUTES:
        issues.append(f"最小时间 {min_minutes:.1f} 分钟太短 (< {MIN_DURATION_MINUTES} 分钟)")
    
    if max_minutes > MAX_DURATION_MINUTES:
        issues.append(f"最大时间 {max_minutes:.1f} 分钟太长 (> {MAX_DURATION_MINUTES} 分钟)")
    
    if min_minutes > max_minutes:
        issues.append(f"最小时间 {min_minutes:.1f} > 最大时间 {max_minutes:.1f}")
        valid = False
    
    if min_minutes < MIN_DURATION_MINUTES or max_minutes > MAX_DURATION_MINUTES:
        valid = False
    
    return valid, issues


def validate_event_name(event: str) -> Tuple[float, List[str]]:
    """验证事件名称质量"""
    issues = []
    score = 1.0
    
    # 长度检查
    if len(event) < 3:
        issues.append("事件名称太短")
        score -= 0.5
    
    if len(event) > 50:
        issues.append("事件名称太长")
        score -= 0.2
    
    # 检查是否为空或无意义
    if not event or event in ['', 'the', 'a', 'an']:
        issues.append("事件名称为空或无意义")
        score = 0.0
    
    # 包含问题词残留
    question_words = ['does ', 'did ', 'is ', 'was ', 'are ', 'were ']
    if any(qw in event for qw in question_words):
        issues.append("包含疑问词残留")
        score -= 0.3
    
    # 检查是否是完整的短语（至少有一个名词或动词）
    common_words = ['the', 'a', 'an', 'to', 'for', 'in', 'on', 'at']
    words = event.split()
    meaningful_words = [w for w in words if w not in common_words]
    if len(meaningful_words) < 1:
        issues.append("缺少有意义的词汇")
        score -= 0.4
    
    return max(0, score), issues


def process_mctaco_data(
    input_path: str,
    output_path: str,
    review_path: str
) -> Dict[str, Any]:
    """处理MCTACO数据，生成扩充的活动分布配置"""
    
    # 读取数据
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"读取到 {len(data)} 条事件-持续时间对")
    
    candidates = []
    rejected = []
    
    for item in data:
        # 提取数据
        original_event = item['event']
        sentence = item['sentence']
        min_seconds = item['min_seconds']
        max_seconds = item['max_seconds']
        all_seconds = item.get('all_seconds', [min_seconds])
        
        # 转换为分钟
        min_minutes = seconds_to_minutes(min_seconds)
        max_minutes = seconds_to_minutes(max_seconds)
        
        # 验证时间范围
        duration_valid, duration_issues = validate_duration_range(min_minutes, max_minutes)
        
        # 清洗事件名称
        cleaned_event = clean_event_name(original_event)
        
        # 验证事件名称
        name_score, name_issues = validate_event_name(cleaned_event)
        
        # 综合评估
        all_issues = duration_issues + name_issues
        
        if not duration_valid:
            rejected.append({
                'original_event': original_event,
                'cleaned_event': cleaned_event,
                'min_minutes': round(min_minutes, 1),
                'max_minutes': round(max_minutes, 1),
                'issues': all_issues,
                'reason': 'duration_out_of_range'
            })
            continue
        
        # 计算分布参数
        dist_type, dist_params, dist_quality = compute_distribution_params(
            all_seconds, min_seconds, max_seconds
        )
        
        # 综合质量分数
        quality_score = name_score * dist_quality
        
        # 标记需要审核的
        needs_review = len(all_issues) > 0 or quality_score < 0.7
        
        candidate = ActivityCandidate(
            original_event=original_event,
            cleaned_event=cleaned_event,
            source_sentence=sentence[:100] + '...' if len(sentence) > 100 else sentence,
            min_minutes=round(min_minutes, 1),
            max_minutes=round(max_minutes, 1),
            distribution_type=dist_type,
            distribution_params=dist_params,
            num_samples=len(all_seconds),
            quality_score=round(quality_score, 2),
            issues=all_issues,
            approved=not needs_review  # 高质量的自动通过
        )
        
        candidates.append(candidate)
    
    # 按质量分数排序
    candidates.sort(key=lambda x: x.quality_score, reverse=True)
    
    # 去重（合并相似的事件）
    unique_candidates = deduplicate_candidates(candidates)
    
    # 生成输出
    print(f"\n处理结果:")
    print(f"  总数据: {len(data)}")
    print(f"  候选活动: {len(candidates)}")
    print(f"  去重后: {len(unique_candidates)}")
    print(f"  自动通过: {sum(1 for c in unique_candidates if c.approved)}")
    print(f"  需要审核: {sum(1 for c in unique_candidates if not c.approved)}")
    print(f"  拒绝: {len(rejected)}")
    
    # 生成ACTIVITY_DISTRIBUTIONS格式
    distributions = {}
    for candidate in unique_candidates:
        key = candidate.cleaned_event.replace(' ', '_')
        distributions[key] = {
            "type": candidate.distribution_type,
            "params": candidate.distribution_params,
            "source": "mctaco",
            "quality_score": candidate.quality_score
        }
    
    # 保存结果
    output_data = {
        "metadata": {
            "source": "MCTACO",
            "total_processed": len(data),
            "candidates": len(candidates),
            "unique_candidates": len(unique_candidates),
            "auto_approved": sum(1 for c in unique_candidates if c.approved),
            "needs_review": sum(1 for c in unique_candidates if not c.approved),
            "rejected": len(rejected),
            "time_range": f"{MIN_DURATION_MINUTES}-{MAX_DURATION_MINUTES} minutes"
        },
        "distributions": distributions
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\n扩充配置已保存到: {output_path}")
    
    # 生成审核列表
    review_data = {
        "needs_review": [asdict(c) for c in unique_candidates if not c.approved],
        "auto_approved": [asdict(c) for c in unique_candidates if c.approved],
        "rejected": rejected
    }
    
    with open(review_path, 'w', encoding='utf-8') as f:
        json.dump(review_data, f, indent=2, ensure_ascii=False)
    print(f"审核列表已保存到: {review_path}")
    
    # 打印示例
    print("\n=== 自动通过的示例 ===")
    for c in unique_candidates[:5]:
        if c.approved:
            print(f"  {c.cleaned_event}")
            print(f"    范围: {c.min_minutes}-{c.max_minutes} 分钟")
            print(f"    分布: {c.distribution_type}({c.distribution_params})")
            print(f"    质量: {c.quality_score}")
    
    print("\n=== 需要审核的示例 ===")
    for c in unique_candidates[:5]:
        if not c.approved:
            print(f"  {c.cleaned_event}")
            print(f"    问题: {', '.join(c.issues)}")
            print(f"    质量: {c.quality_score}")
    
    return output_data


def deduplicate_candidates(candidates: List[ActivityCandidate]) -> List[ActivityCandidate]:
    """去重：合并相似的事件"""
    seen_events = {}
    unique = []
    
    for candidate in candidates:
        # 标准化事件名称用于比较
        normalized = candidate.cleaned_event.lower()
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        if normalized in seen_events:
            # 已存在，保留质量更高的
            existing = seen_events[normalized]
            if candidate.quality_score > existing.quality_score:
                unique.remove(existing)
                unique.append(candidate)
                seen_events[normalized] = candidate
        else:
            seen_events[normalized] = candidate
            unique.append(candidate)
    
    return unique


def merge_with_existing_distributions(
    new_distributions: Dict[str, Any],
    existing_config_path: str
) -> Dict[str, Any]:
    """与现有配置合并"""
    # 读取现有配置的模板
    from pta_benchmark.config import ACTIVITY_DISTRIBUTIONS
    
    merged = {}
    
    # 先添加现有的
    for key, value in ACTIVITY_DISTRIBUTIONS.items():
        merged[key] = value
    
    # 再添加新的（不覆盖现有）
    for key, value in new_distributions.get("distributions", {}).items():
        if key not in merged:
            merged[key] = {
                "type": value["type"],
                "params": value["params"]
            }
    
    return merged


if __name__ == "__main__":
    # 项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    input_path = os.path.join(project_root, "output", "mctaco_event_durations.json")
    output_path = os.path.join(project_root, "output", "expanded_distributions.json")
    review_path = os.path.join(project_root, "output", "distribution_review.json")
    
    print(f"输入文件: {input_path}")
    print(f"输出文件: {output_path}")
    print(f"审核文件: {review_path}")
    
    result = process_mctaco_data(input_path, output_path, review_path)
