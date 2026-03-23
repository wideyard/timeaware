"""Analysis Tools for PTA Benchmark"""

import numpy as np
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from ..data import PTASample


def breakdown_by_region(
    samples: List[PTASample],
    predictions: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Breakdown performance by delta_t region (early/mid/late)
    """
    regions = defaultdict(lambda: {"correct": 0, "total": 0, "samples": []})
    
    for sample, pred in zip(samples, predictions):
        region = sample.delta_t_region
        regions[region]["total"] += 1
        if pred["action"] in sample.valid_actions:
            regions[region]["correct"] += 1
        regions[region]["samples"].append((sample, pred))
    
    results = {}
    for region, data in regions.items():
        accuracy = data["correct"] / data["total"] if data["total"] > 0 else 0.0
        results[region] = {
            "accuracy": accuracy,
            "correct": data["correct"],
            "total": data["total"]
        }
    
    return results


def breakdown_by_activity(
    samples: List[PTASample],
    predictions: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Breakdown performance by activity type
    """
    activities = defaultdict(lambda: {"correct": 0, "total": 0})
    
    for sample, pred in zip(samples, predictions):
        activity = sample.activity
        activities[activity]["total"] += 1
        if pred["action"] in sample.valid_actions:
            activities[activity]["correct"] += 1
    
    results = {}
    for activity, data in activities.items():
        accuracy = data["correct"] / data["total"] if data["total"] > 0 else 0.0
        results[activity] = {
            "accuracy": accuracy,
            "correct": data["correct"],
            "total": data["total"]
        }
    
    return results


def categorize_errors(
    samples: List[PTASample],
    predictions: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Categorize errors into:
    - temporal_error: Wrong action due to misjudging time
    - commonsense_error: Wrong action due to misjudging activity duration
    - decision_error: Correct probability but wrong action selection
    """
    errors = {
        "temporal_error": [],
        "commonsense_error": [],
        "decision_error": [],
        "correct": []
    }
    
    for sample, pred in zip(samples, predictions):
        if pred["action"] in sample.valid_actions:
            errors["correct"].append({
                "sample": sample,
                "prediction": pred
            })
            continue
        
        # Determine error type
        p_active = sample.p_active
        pred_p = pred.get("p_active")
        
        if pred_p is not None:
            # Model provided probability - check if decision threshold was wrong
            pred_action = pred["action"]
            correct_action = sample.valid_actions[0] if len(sample.valid_actions) == 1 else "check-in"
            
            # Decision error: probability suggests one action but model chose another
            if (pred_p > 0.8 and pred_action != "defer") or \
               (pred_p < 0.3 and pred_action != "interrupt") or \
               (0.3 <= pred_p <= 0.8 and pred_action not in ["check-in", "defer"]):
                errors["decision_error"].append({
                    "sample": sample,
                    "prediction": pred,
                    "error_detail": "Probability-action mismatch"
                })
            else:
                # Temporal or commonsense error
                if abs(pred_p - p_active) > 0.3:
                    errors["commonsense_error"].append({
                        "sample": sample,
                        "prediction": pred,
                        "error_detail": f"P(active) mismatch: pred={pred_p:.2f}, true={p_active:.2f}"
                    })
                else:
                    errors["temporal_error"].append({
                        "sample": sample,
                        "prediction": pred,
                        "error_detail": "Time sensitivity error"
                    })
        else:
            # No probability provided - categorize based on context
            delta_t_ratio = sample.delta_t / sample.expected_duration if sample.expected_duration > 0 else 1.0
            
            if delta_t_ratio < 0.3:
                # Early - should defer
                errors["temporal_error"].append({
                    "sample": sample,
                    "prediction": pred,
                    "error_detail": f"Early phase error (ratio={delta_t_ratio:.2f})"
                })
            elif delta_t_ratio > 0.8:
                # Late - should interrupt
                errors["commonsense_error"].append({
                    "sample": sample,
                    "prediction": pred,
                    "error_detail": f"Late phase error (ratio={delta_t_ratio:.2f})"
                })
            else:
                errors["decision_error"].append({
                    "sample": sample,
                    "prediction": pred,
                    "error_detail": f"Mid phase error (ratio={delta_t_ratio:.2f})"
                })
    
    return errors


def compute_action_distribution(
    samples: List[PTASample],
    predictions: List[Dict[str, Any]]
) -> Dict[str, Dict[str, int]]:
    """
    Compute distribution of predicted actions vs valid actions
    """
    pred_dist = defaultdict(int)
    true_dist = defaultdict(int)
    
    for sample, pred in zip(samples, predictions):
        pred_dist[pred["action"]] += 1
        for action in sample.valid_actions:
            true_dist[action] += 1
    
    return {
        "predicted": dict(pred_dist),
        "ground_truth": dict(true_dist)
    }


def generate_analysis_report(
    samples: List[PTASample],
    predictions: List[Dict[str, Any]],
    model_name: str = "Model"
) -> Dict[str, Any]:
    """Generate comprehensive analysis report"""
    report = {
        "model_name": model_name,
        "total_samples": len(samples)
    }
    
    # Region breakdown
    report["region_breakdown"] = breakdown_by_region(samples, predictions)
    
    # Activity breakdown
    report["activity_breakdown"] = breakdown_by_activity(samples, predictions)
    
    # Error categorization
    errors = categorize_errors(samples, predictions)
    report["error_counts"] = {
        "correct": len(errors["correct"]),
        "temporal_error": len(errors["temporal_error"]),
        "commonsense_error": len(errors["commonsense_error"]),
        "decision_error": len(errors["decision_error"])
    }
    
    # Action distribution
    report["action_distribution"] = compute_action_distribution(samples, predictions)
    
    return report
