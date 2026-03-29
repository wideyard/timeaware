"""三层评测模块

基于 arich.md 的设计，实现:
1. Answer-level: 答案级别的准确率评测
2. State-level: 状态级别的评测（用于状态追踪任务）
3. Chain-level: 一致性评测（检查前后回答是否一致）
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

from .task_schema import TemporalSample, TaskType, DifficultyLevel


@dataclass
class EvaluationResult:
    """评测结果"""
    sample_id: str
    task_type: TaskType
    
    answer_correct: bool = False
    answer_level_score: float = 0.0
    
    state_correct: bool = False
    state_accuracy: float = 0.0
    state_level_scores: Dict[str, float] = field(default_factory=dict)
    
    chain_consistent: bool = False
    consistency_score: float = 0.0
    
    overall_score: float = 0.0
    
    details: Dict[str, Any] = field(default_factory=dict)
    error_type: Optional[str] = None


class AnswerLevelEvaluator:
    """Answer-level 评测器
    
    评估模型输出的答案是否正确
    """
    
    def __init__(self, tolerance: float = 0.0):
        self.tolerance = tolerance
    
    def evaluate(self, sample: TemporalSample, prediction: Dict[str, Any]) -> Tuple[bool, float, Dict]:
        """评估答案正确性
        
        Args:
            sample: 原始样本
            prediction: 模型预测结果 {"answer": "...", "reasoning": "..."}
        
        Returns:
            (is_correct, score, details)
        """
        predicted_answer = prediction.get("answer", "")
        ground_truth = sample.answer or sample.ground_truth.get("answer", "")
        
        if not predicted_answer or not ground_truth:
            return False, 0.0, {"error": "Missing answer"}
        
        is_correct = self._check_answer_match(predicted_answer, ground_truth)
        score = 1.0 if is_correct else 0.0
        
        details = {
            "predicted": predicted_answer,
            "ground_truth": ground_truth,
            "match_type": "exact" if is_correct else "mismatch"
        }
        
        return is_correct, score, details
    
    def _check_answer_match(self, predicted: str, ground_truth: str) -> bool:
        """检查答案是否匹配"""
        predicted = predicted.strip().lower()
        ground_truth = ground_truth.strip().lower()
        
        if predicted == ground_truth:
            return True
        
        if self._check_numeric_equivalence(predicted, ground_truth):
            return True
        
        if self._check_temporal_equivalence(predicted, ground_truth):
            return True
        
        if ground_truth in predicted or predicted in ground_truth:
            return True
        
        return False
    
    def _check_numeric_equivalence(self, pred: str, truth: str) -> bool:
        """检查数值等价"""
        pred_nums = self._extract_numbers(pred)
        truth_nums = self._extract_numbers(truth)
        
        if not pred_nums or not truth_nums:
            return False
        
        return all(
            any(abs(p - t) <= self.tolerance for p in pred_nums)
            for t in truth_nums
        )
    
    def _check_temporal_equivalence(self, pred: str, truth: str) -> bool:
        """检查时间表达等价"""
        time_patterns = [
            (r'(\d+)\s*(分钟|min)', 'minute'),
            (r'(\d+)\s*(小时|hour)', 'hour'),
            (r'(\d+)\s*(天|day)', 'day'),
            (r'(\d+)\s*(周|week)', 'week'),
            (r'(\d+)\s*(月|month)', 'month'),
            (r'(\d+)\s*(年|year)', 'year'),
        ]
        
        pred_times = self._extract_time_units(pred, time_patterns)
        truth_times = self._extract_time_units(truth, time_patterns)
        
        if pred_times == truth_times:
            return True
        
        pred_minutes = self._to_minutes(pred_times)
        truth_minutes = self._to_minutes(truth_times)
        
        if pred_minutes and truth_minutes:
            ratio = min(pred_minutes, truth_minutes) / max(pred_minutes, truth_minutes)
            return ratio >= 0.9
        
        return False
    
    def _extract_numbers(self, text: str) -> List[float]:
        """提取数字"""
        return [float(n) for n in re.findall(r'\d+\.?\d*', text)]
    
    def _extract_time_units(self, text: str, patterns: List[Tuple[str, str]]) -> Dict[str, float]:
        """提取时间单位"""
        result = {}
        for pattern, unit in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    value = float(match[0])
                else:
                    value = float(match)
                result[unit] = value
        return result
    
    def _to_minutes(self, time_units: Dict[str, float]) -> Optional[float]:
        """转换为分钟"""
        if not time_units:
            return None
        
        total = 0.0
        multipliers = {
            'minute': 1,
            'hour': 60,
            'day': 1440,
            'week': 10080,
            'month': 43200,
            'year': 525600,
        }
        
        for unit, value in time_units.items():
            total += value * multipliers.get(unit, 1)
        
        return total if total > 0 else None


class StateLevelEvaluator:
    """State-level 评测器
    
    用于状态追踪任务，评估每个状态字段是否正确
    """
    
    def __init__(self):
        self.answer_evaluator = AnswerLevelEvaluator()
    
    def evaluate(self, sample: TemporalSample, prediction: Dict[str, Any]) -> Tuple[bool, float, Dict[str, float]]:
        """评估状态正确性
        
        Args:
            sample: 原始样本
            prediction: 模型预测结果，包含 "state": {...}
        
        Returns:
            (is_correct, overall_score, field_scores)
        """
        predicted_state = prediction.get("state", {})
        ground_truth_state = sample.state or sample.ground_truth.get("final_state", {})
        
        if not predicted_state or not ground_truth_state:
            if sample.task_type == TaskType.T2_STATE_TRACKING:
                answer_correct, _, _ = self.answer_evaluator.evaluate(sample, prediction)
                return answer_correct, 1.0 if answer_correct else 0.0, {}
            return True, 1.0, {}
        
        field_scores = {}
        correct_fields = 0
        total_fields = len(ground_truth_state)
        
        for field_name, gt_value in ground_truth_state.items():
            pred_value = predicted_state.get(field_name)
            
            if pred_value is None:
                field_scores[field_name] = 0.0
            else:
                is_match = self._check_field_match(field_name, pred_value, gt_value)
                field_scores[field_name] = 1.0 if is_match else 0.0
                if is_match:
                    correct_fields += 1
        
        overall_score = correct_fields / total_fields if total_fields > 0 else 1.0
        
        return overall_score == 1.0, overall_score, field_scores
    
    def _check_field_match(self, field_name: str, pred: Any, truth: Any) -> bool:
        """检查字段匹配"""
        if field_name in ["location", "place", "position"]:
            return self._check_location_match(pred, truth)
        elif field_name in ["status", "state", "condition"]:
            return self._check_status_match(pred, truth)
        else:
            pred_str = str(pred).strip().lower()
            truth_str = str(truth).strip().lower()
            return pred_str == truth_str or truth_str in pred_str
    
    def _check_location_match(self, pred: str, truth: str) -> bool:
        """检查位置匹配"""
        pred = pred.strip().lower()
        truth = truth.strip().lower()
        
        if pred == truth:
            return True
        
        common_locations = {
            "home": ["家里", "家", "home"],
            "office": ["办公室", "公司", "office"],
            "school": ["学校", "school"],
            "hospital": ["医院", "hospital"],
        }
        
        pred_key = None
        truth_key = None
        
        for key, variants in common_locations.items():
            if any(v in pred for v in variants):
                pred_key = key
            if any(v in truth for v in variants):
                truth_key = key
        
        return pred_key is not None and pred_key == truth_key
    
    def _check_status_match(self, pred: str, truth: str) -> bool:
        """检查状态匹配"""
        pred = pred.strip().lower()
        truth = truth.strip().lower()
        return pred == truth or truth in pred


class ChainLevelEvaluator:
    """Chain-level 评测器
    
    评估多次回答的一致性（Consistency）
    """
    
    def __init__(self):
        self.answer_evaluator = AnswerLevelEvaluator()
    
    def evaluate_chain(
        self, 
        samples: List[TemporalSample], 
        predictions: List[Dict[str, Any]],
        window_size: int = 3
    ) -> List[Dict[str, Any]]:
        """评估回答链的一致性
        
        Args:
            samples: 原始样本列表
            predictions: 预测结果列表
            window_size: 用于一致性检查的窗口大小
        
        Returns:
            每对样本的一致性评估结果
        """
        results = []
        
        for i in range(len(predictions) - 1):
            pred1 = predictions[i]
            pred2 = predictions[i + 1]
            
            is_consistent, score, details = self._check_consistency(
                samples[i], pred1,
                samples[i + 1], pred2
            )
            
            results.append({
                "index": i,
                "sample_id_1": samples[i].id,
                "sample_id_2": samples[i + 1].id,
                "is_consistent": is_consistent,
                "consistency_score": score,
                "details": details
            })
        
        return results
    
    def _check_consistency(
        self,
        sample1: TemporalSample,
        pred1: Dict[str, Any],
        sample2: TemporalSample,
        pred2: Dict[str, Any]
    ) -> Tuple[bool, float, Dict]:
        """检查两次回答的一致性"""
        details = {}
        
        state1 = pred1.get("state", {})
        state2 = pred2.get("state", {})
        
        if state1 and state2:
            state_consistent, state_score = self._check_state_consistency(state1, state2)
            details["state_consistency"] = {
                "is_consistent": state_consistent,
                "score": state_score,
                "state1": state1,
                "state2": state2
            }
        else:
            state_consistent = True
            state_score = 1.0
        
        temporal_consistent, temporal_score = self._check_temporal_consistency(
            sample1, pred1, sample2, pred2
        )
        details["temporal_consistency"] = {
            "is_consistent": temporal_consistent,
            "score": temporal_score
        }
        
        overall_score = (state_score + temporal_score) / 2
        is_consistent = state_consistent and temporal_consistent
        
        return is_consistent, overall_score, details
    
    def _check_state_consistency(
        self, 
        state1: Dict[str, Any], 
        state2: Dict[str, Any]
    ) -> Tuple[bool, float]:
        """检查状态一致性"""
        if not state1 or not state2:
            return True, 1.0
        
        common_keys = set(state1.keys()) & set(state2.keys())
        if not common_keys:
            return True, 1.0
        
        consistent_count = 0
        for key in common_keys:
            if state1[key] == state2[key]:
                consistent_count += 1
        
        score = consistent_count / len(common_keys)
        
        time_jumped = self._detect_impossible_transition(state1, state2)
        if time_jumped:
            return False, 0.0
        
        return score >= 0.8, score
    
    def _detect_impossible_transition(
        self, 
        state1: Dict[str, Any], 
        state2: Dict[str, Any]
    ) -> bool:
        """检测不可能的状态转换"""
        location1 = state1.get("location", "")
        location2 = state2.get("location", "")
        
        if location1 and location2 and location1 != location2:
            if self._check_simultaneous_displacement(location1, location2):
                return True
        
        return False
    
    def _check_simultaneous_displacement(self, loc1: str, loc2: str) -> bool:
        """检查同时在不同位置的情况"""
        loc1_lower = loc1.lower()
        loc2_lower = loc2.lower()
        
        incompatible_pairs = [
            (["home", "家"], ["office", "公司", "办公室"]),
            (["学校", "school"], ["家", "home"]),
        ]
        
        for incompatible in incompatible_pairs:
            if (any(v in loc1_lower for v in incompatible[0]) and 
                any(v in loc2_lower for v in incompatible[1])):
                return True
        
        return False
    
    def _check_temporal_consistency(
        self,
        sample1: TemporalSample,
        pred1: Dict[str, Any],
        sample2: TemporalSample,
        pred2: Dict[str, Any]
    ) -> Tuple[bool, float]:
        """检查时间一致性"""
        ans1 = pred1.get("answer", "")
        ans2 = pred2.get("answer", "")
        
        if not ans1 or not ans2:
            return True, 1.0
        
        time1 = self._extract_time_reference(ans1)
        time2 = self._extract_time_reference(ans2)
        
        if time1 and time2:
            if time2 < time1:
                return False, 0.0
        
        return True, 1.0
    
    def _extract_time_reference(self, text: str) -> Optional[float]:
        """提取时间参考值（分钟）"""
        patterns = [
            (r'(\d+)\s*分钟', 1),
            (r'(\d+)\s*小时', 60),
            (r'(\d+)\s*天', 1440),
            (r'(\d+)\s*周', 10080),
            (r'(\d+)\s*月', 43200),
            (r'(\d+)\s*年', 525600),
        ]
        
        for pattern, multiplier in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return float(matches[0]) * multiplier
        
        return None


class TemporalBenchmarkEvaluator:
    """统一的三层评测器
    
    整合 Answer-level、State-level、Chain-level 评测
    """
    
    def __init__(self):
        self.answer_evaluator = AnswerLevelEvaluator()
        self.state_evaluator = StateLevelEvaluator()
        self.chain_evaluator = ChainLevelEvaluator()
        
        self.results: List[EvaluationResult] = []
    
    def evaluate(
        self, 
        samples: List[TemporalSample], 
        predictions: List[Dict[str, Any]]
    ) -> List[EvaluationResult]:
        """评测所有样本
        
        Args:
            samples: 原始样本列表
            predictions: 预测结果列表
        
        Returns:
            每个样本的评测结果
        """
        results = []
        
        for sample, prediction in zip(samples, predictions):
            result = self._evaluate_single(sample, prediction)
            results.append(result)
        
        self.results = results
        return results
    
    def _evaluate_single(self, sample: TemporalSample, prediction: Dict[str, Any]) -> EvaluationResult:
        """评测单个样本"""
        result = EvaluationResult(
            sample_id=sample.id,
            task_type=sample.task_type
        )
        
        answer_correct, answer_score, answer_details = self.answer_evaluator.evaluate(
            sample, prediction
        )
        result.answer_correct = answer_correct
        result.answer_level_score = answer_score
        result.details["answer"] = answer_details
        
        if sample.task_type == TaskType.T2_STATE_TRACKING:
            state_correct, state_score, field_scores = self.state_evaluator.evaluate(
                sample, prediction
            )
            result.state_correct = state_correct
            result.state_accuracy = state_score
            result.state_level_scores = field_scores
            result.details["state"] = field_scores
        
        result.overall_score = self._compute_overall_score(result)
        
        return result
    
    def _compute_overall_score(self, result: EvaluationResult) -> float:
        """计算综合得分"""
        if result.task_type == TaskType.T2_STATE_TRACKING:
            return (result.answer_level_score + result.state_accuracy) / 2
        return result.answer_level_score
    
    def evaluate_chain_consistency(
        self,
        samples: List[TemporalSample],
        predictions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """评估链一致性"""
        return self.chain_evaluator.evaluate_chain(samples, predictions)
    
    def compute_metrics(self) -> Dict[str, Any]:
        """计算总体指标"""
        if not self.results:
            return {}
        
        metrics = {
            "overall": self._compute_overall_metrics(),
            "by_task": self._compute_task_metrics(),
            "by_difficulty": self._compute_difficulty_metrics(),
        }
        
        return metrics
    
    def _compute_overall_metrics(self) -> Dict[str, float]:
        """计算总体指标"""
        total = len(self.results)
        correct = sum(1 for r in self.results if r.answer_correct)
        
        return {
            "total_samples": total,
            "accuracy": correct / total if total > 0 else 0.0,
            "correct_count": correct,
        }
    
    def _compute_task_metrics(self) -> Dict[str, Dict[str, float]]:
        """按任务类型计算指标"""
        task_results = defaultdict(list)
        
        for result in self.results:
            task_results[result.task_type.value].append(result)
        
        metrics = {}
        for task_type, results in task_results.items():
            total = len(results)
            correct = sum(1 for r in results if r.answer_correct)
            avg_score = sum(r.overall_score for r in results) / total if total > 0 else 0
            
            metrics[task_type] = {
                "total": total,
                "accuracy": correct / total if total > 0 else 0.0,
                "avg_score": avg_score,
            }
        
        return metrics
    
    def _compute_difficulty_metrics(self) -> Dict[str, Dict[str, float]]:
        """按难度级别计算指标"""
        difficulty_results = defaultdict(list)
        
        for result in self.results:
            difficulty = result.details.get("difficulty", "unknown")
            difficulty_results[difficulty].append(result)
        
        metrics = {}
        for difficulty, results in difficulty_results.items():
            total = len(results)
            correct = sum(1 for r in results if r.answer_correct)
            
            metrics[difficulty] = {
                "total": total,
                "accuracy": correct / total if total > 0 else 0.0,
            }
        
        return metrics
    
    def generate_report(self) -> Dict[str, Any]:
        """生成评测报告"""
        metrics = self.compute_metrics()
        
        return {
            "summary": metrics,
            "sample_results": [
                {
                    "sample_id": r.sample_id,
                    "task_type": r.task_type.value,
                    "answer_correct": r.answer_correct,
                    "answer_score": r.answer_level_score,
                    "state_accuracy": r.state_accuracy,
                    "consistency_score": r.consistency_score,
                    "overall_score": r.overall_score,
                    "error_type": r.error_type,
                }
                for r in self.results
            ]
        }
