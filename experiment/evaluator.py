"""LLM-as-Judge evaluator for the Timeaware Benchmark Experiment.

Evaluates model predictions against ground truth answers using a judge LLM.
Supports both exact match (for multiple choice) and semantic evaluation (for open-ended).
"""

import sys
import os
import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client import call_llm
from experiment.subtask_config import JUDGE_MODEL, LLM_TEMPERATURE, API_DELAY


def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    text = text.strip().lower()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text


def exact_match_eval(prediction: str, ground_truth: str) -> bool:
    """Check for exact or near-exact match.
    
    Handles:
    - Direct string match
    - Multiple acceptable answers (separated by |)
    - Option letter match (A, B, C, D)
    """
    if not prediction or not ground_truth:
        return False
    
    pred_norm = _normalize_text(prediction)
    gt_norm = _normalize_text(ground_truth)
    
    # Direct match
    if pred_norm == gt_norm:
        return True
    
    # Prediction contains the ground truth
    if gt_norm in pred_norm:
        return True
    
    # Ground truth contains the prediction (for short answers)
    if pred_norm in gt_norm and len(pred_norm) > 2:
        return True
    
    # Multiple acceptable answers (separated by |)
    if '|' in ground_truth:
        alternatives = [a.strip().lower() for a in ground_truth.split('|')]
        return any(pred_norm == alt or alt in pred_norm for alt in alternatives)
    
    # Option letter match
    if len(gt_norm) == 1 and gt_norm in 'abcd':
        # Check if prediction starts with or contains the letter
        pred_lower = prediction.lower()
        if pred_lower.startswith(gt_norm) or f" {gt_norm}" in pred_lower or f"{gt_norm}." in pred_lower:
            return True
    
    return False


def build_judge_prompt(query: str, ground_truth: str, prediction: str,
                        subtask_key: str, dimension: str) -> str:
    """Build the LLM-as-judge prompt.
    
    Asks the judge to evaluate whether the prediction is correct given the
    query and ground truth.
    """
    return f"""你是一个严格的评估专家。请判断模型的回答是否正确。

【问题】
{query}

【标准答案】
{ground_truth}

【模型回答】
{prediction}

【任务维度】{dimension} - {subtask_key}

请判断模型回答是否正确。评判标准：
1. 如果模型回答与标准答案语义等价，判为正确
2. 如果模型回答包含标准答案的核心信息，判为正确
3. 如果模型回答偏离了问题或给出了错误信息，判为错误
4. 如果模型回答表示"不知道"或"没有足够信息"，判为错误

请以JSON格式返回评估结果，不要包含任何其他文字：
{{
    "correct": true/false,
    "reason": "简要说明判断理由"
}}"""


def judge_single_result(result: Dict[str, Any], 
                         judge_model: str = JUDGE_MODEL,
                         temperature: float = 0.0) -> Dict[str, Any]:
    """Evaluate a single result using LLM-as-judge.
    
    First tries exact match, then falls back to LLM judge for ambiguous cases.
    
    Returns:
        Result dict augmented with evaluation
    """
    prediction = result.get('prediction', '')
    ground_truth = result.get('ground_truth', '')
    
    if not prediction:
        return {
            **result,
            "eval_correct": False,
            "eval_method": "no_prediction",
            "eval_reason": "No prediction received",
        }
    
    # Try exact match first (fast, no API call)
    if exact_match_eval(prediction, ground_truth):
        return {
            **result,
            "eval_correct": True,
            "eval_method": "exact_match",
            "eval_reason": "Prediction matches ground truth",
        }
    
    # For multiple choice questions, check if the answer letter is in the prediction
    query = result.get('query', '')
    gt_lower = ground_truth.lower().strip()
    
    # Check if ground truth is a single letter (A/B/C/D)
    if len(gt_lower) == 1 and gt_lower in 'abcd':
        pred_lower = prediction.lower()
        if gt_lower in pred_lower:
            return {
                **result,
                "eval_correct": True,
                "eval_method": "option_match",
                "eval_reason": f"Prediction contains option {gt_lower.upper()}",
            }
    
    # Fall back to LLM-as-judge
    subtask_key = result.get('subtask_key', '')
    dimension = result.get('dimension', '')
    
    prompt = build_judge_prompt(query, ground_truth, prediction, subtask_key, dimension)
    
    try:
        response = call_llm(
            prompt=prompt,
            system_prompt="你是一个客观公正的评估专家。请仔细比较模型回答和标准答案。",
            temperature=temperature,
            model_key=judge_model,
        )
        
        # Parse JSON response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        eval_result = json.loads(response)
        
        return {
            **result,
            "eval_correct": eval_result.get('correct', False),
            "eval_method": "llm_judge",
            "eval_reason": eval_result.get('reason', ''),
        }
    except Exception as e:
        return {
            **result,
            "eval_correct": False,
            "eval_method": "judge_error",
            "eval_reason": f"Judge failed: {str(e)}",
        }


def evaluate_all_results(results: List[Dict[str, Any]],
                          judge_model: str = JUDGE_MODEL,
                          delay: float = API_DELAY) -> List[Dict[str, Any]]:
    """Evaluate all results.
    
    Uses exact match where possible, LLM-as-judge for the rest.
    
    Returns:
        List of result dicts with evaluation added
    """
    evaluated = []
    total = len(results)
    
    # Count how many need LLM judge
    need_judge = 0
    for r in results:
        if not exact_match_eval(r.get('prediction', ''), r.get('ground_truth', '')):
            pred = r.get('prediction', '')
            gt = r.get('ground_truth', '').lower().strip()
            if not (pred and len(gt) == 1 and gt in 'abcd' and gt in pred.lower()):
                need_judge += 1
    
    print(f"\n{'='*60}")
    print(f"Evaluating {total} results...")
    print(f"  Exact match: {total - need_judge}")
    print(f"  Need LLM judge: {need_judge}")
    print(f"{'='*60}\n")
    
    current = 0
    for result in results:
        # Quick check if exact match works
        pred = result.get('prediction', '')
        gt = result.get('ground_truth', '')
        
        if exact_match_eval(pred, gt):
            ev = {
                **result,
                "eval_correct": True,
                "eval_method": "exact_match",
                "eval_reason": "Prediction matches ground truth",
            }
            evaluated.append(ev)
            continue
        
        # Check option letter match
        gt_lower = gt.lower().strip()
        if len(gt_lower) == 1 and gt_lower in 'abcd' and pred:
            pred_lower = pred.lower()
            if gt_lower in pred_lower:
                ev = {
                    **result,
                    "eval_correct": True,
                    "eval_method": "option_match",
                    "eval_reason": f"Prediction contains option {gt_lower.upper()}",
                }
                evaluated.append(ev)
                continue
        
        # Need LLM judge
        current += 1
        print(f"  Judging [{current}/{need_judge}]: {result.get('subtask_key', '')} | {result.get('model', '')}")
        
        ev = judge_single_result(result, judge_model=judge_model)
        evaluated.append(ev)
        
        if delay > 0:
            time.sleep(delay)
    
    return evaluated


def compute_accuracy(evaluated_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute accuracy statistics from evaluated results.
    
    Returns:
        Dict with accuracy breakdowns by dimension, subtask, model, mode, etc.
    """
    total = len(evaluated_results)
    correct = sum(1 for r in evaluated_results if r.get('eval_correct', False))
    
    stats = {
        "overall": {
            "total": total,
            "correct": correct,
            "accuracy": correct / total if total > 0 else 0,
        },
        "by_dimension": {},
        "by_subtask": {},
        "by_model": {},
        "by_mode": {},
        "by_noise_type": {},
        "by_difficulty": {},
        "by_dimension_mode": {},
        "by_model_mode": {},
        "by_model_noise": {},
    }
    
    for r in evaluated_results:
        dim = r.get('dimension', 'unknown')
        subtask = r.get('subtask_key', 'unknown')
        model = r.get('model', 'unknown')
        mode = r.get('mode', 'unknown')
        noise = r.get('noise_type', 'none')
        diff = r.get('difficulty', 'unknown')
        is_correct = r.get('eval_correct', False)
        
        # By dimension
        if dim not in stats["by_dimension"]:
            stats["by_dimension"][dim] = {"total": 0, "correct": 0}
        stats["by_dimension"][dim]["total"] += 1
        if is_correct:
            stats["by_dimension"][dim]["correct"] += 1
        
        # By subtask
        if subtask not in stats["by_subtask"]:
            stats["by_subtask"][subtask] = {"total": 0, "correct": 0}
        stats["by_subtask"][subtask]["total"] += 1
        if is_correct:
            stats["by_subtask"][subtask]["correct"] += 1
        
        # By model
        if model not in stats["by_model"]:
            stats["by_model"][model] = {"total": 0, "correct": 0}
        stats["by_model"][model]["total"] += 1
        if is_correct:
            stats["by_model"][model]["correct"] += 1
        
        # By mode
        if mode not in stats["by_mode"]:
            stats["by_mode"][mode] = {"total": 0, "correct": 0}
        stats["by_mode"][mode]["total"] += 1
        if is_correct:
            stats["by_mode"][mode]["correct"] += 1
        
        # By noise type
        noise_key = noise if noise else "none"
        if noise_key not in stats["by_noise_type"]:
            stats["by_noise_type"][noise_key] = {"total": 0, "correct": 0}
        stats["by_noise_type"][noise_key]["total"] += 1
        if is_correct:
            stats["by_noise_type"][noise_key]["correct"] += 1
        
        # By difficulty
        if diff not in stats["by_difficulty"]:
            stats["by_difficulty"][diff] = {"total": 0, "correct": 0}
        stats["by_difficulty"][diff]["total"] += 1
        if is_correct:
            stats["by_difficulty"][diff]["correct"] += 1
        
        # By dimension + mode
        dm_key = f"{dim}_{mode}"
        if dm_key not in stats["by_dimension_mode"]:
            stats["by_dimension_mode"][dm_key] = {"total": 0, "correct": 0}
        stats["by_dimension_mode"][dm_key]["total"] += 1
        if is_correct:
            stats["by_dimension_mode"][dm_key]["correct"] += 1
        
        # By model + mode
        mm_key = f"{model}_{mode}"
        if mm_key not in stats["by_model_mode"]:
            stats["by_model_mode"][mm_key] = {"total": 0, "correct": 0}
        stats["by_model_mode"][mm_key]["total"] += 1
        if is_correct:
            stats["by_model_mode"][mm_key]["correct"] += 1
        
        # By model + noise
        if mode == "multi_turn_noise":
            mn_key = f"{model}_{noise_key}"
            if mn_key not in stats["by_model_noise"]:
                stats["by_model_noise"][mn_key] = {"total": 0, "correct": 0}
            stats["by_model_noise"][mn_key]["total"] += 1
            if is_correct:
                stats["by_model_noise"][mn_key]["correct"] += 1
    
    # Compute accuracy rates
    for category in ["by_dimension", "by_subtask", "by_model", "by_mode",
                      "by_noise_type", "by_difficulty", "by_dimension_mode",
                      "by_model_mode", "by_model_noise"]:
        for key, val in stats[category].items():
            val["accuracy"] = val["correct"] / val["total"] if val["total"] > 0 else 0
    
    return stats
