"""Metrics for PTA Benchmark"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from ..data import PTASample


def compute_ppa(
    samples: List[PTASample],
    predictions: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Probabilistic Policy Accuracy (PPA)
    
    A prediction is correct if predicted_action ∈ valid_actions
    """
    correct = 0
    total = len(samples)
    
    for sample, pred in zip(samples, predictions):
        if pred["action"] in sample.valid_actions:
            correct += 1
    
    accuracy = correct / total if total > 0 else 0.0
    
    return {
        "ppa": accuracy,
        "correct": correct,
        "total": total
    }


def compute_tsu(
    paired_samples: List[Tuple[PTASample, PTASample]],
    paired_predictions: List[Tuple[Dict[str, Any], Dict[str, Any]]]
) -> Dict[str, float]:
    """
    Temporal Sensitivity under Uncertainty (TSU)
    
    For paired samples (same context, different delta_t):
    - Check if model predictions differ appropriately
    - Both predictions must be correct
    """
    sensitive_pairs = 0
    total_pairs = len(paired_samples)
    
    for (s1, s2), (p1, p2) in zip(paired_samples, paired_predictions):
        # Check if both predictions are correct
        correct1 = p1["action"] in s1.valid_actions
        correct2 = p2["action"] in s2.valid_actions
        
        # Check if predictions differ (showing sensitivity to time)
        predictions_differ = p1["action"] != p2["action"]
        
        # Check if valid actions differ (expected to differ)
        actions_differ = set(s1.valid_actions) != set(s2.valid_actions)
        
        if correct1 and correct2:
            if actions_differ:
                # When valid actions differ, model should show sensitivity
                if predictions_differ:
                    sensitive_pairs += 1
            else:
                # When valid actions are same, both correct is sufficient
                sensitive_pairs += 1
    
    tsu = sensitive_pairs / total_pairs if total_pairs > 0 else 0.0
    
    return {
        "tsu": tsu,
        "sensitive_pairs": sensitive_pairs,
        "total_pairs": total_pairs
    }


def compute_bas(
    samples: List[PTASample],
    predictions: List[Dict[str, Any]],
    tolerance: float = 0.1
) -> Dict[str, float]:
    """
    Boundary Awareness Score (BAS)
    
    Evaluate only samples where delta_t is near E[d]
    (i.e., P(active) is near the decision boundary)
    """
    boundary_samples = []
    boundary_predictions = []
    
    for sample, pred in zip(samples, predictions):
        # Check if near boundary (P(active) around 0.3-0.8)
        if 0.3 - tolerance <= sample.p_active <= 0.8 + tolerance:
            boundary_samples.append(sample)
            boundary_predictions.append(pred)
    
    if not boundary_samples:
        return {
            "bas": 0.0,
            "boundary_samples": 0,
            "total_samples": len(samples)
        }
    
    # Compute accuracy on boundary samples
    correct = sum(
        1 for s, p in zip(boundary_samples, boundary_predictions)
        if p["action"] in s.valid_actions
    )
    
    bas = correct / len(boundary_samples)
    
    return {
        "bas": bas,
        "correct_boundary": correct,
        "boundary_samples": len(boundary_samples),
        "total_samples": len(samples)
    }


def compute_ce(
    samples: List[PTASample],
    predictions: List[Dict[str, Any]],
    num_bins: int = 10
) -> Dict[str, float]:
    """
    Calibration Error (CE)
    
    If model outputs probability: CE = mean(|pred_p - true_p|)
    """
    # Filter predictions that have p_active
    valid_pairs = [
        (s, p) for s, p in zip(samples, predictions)
        if p.get("p_active") is not None
    ]
    
    if not valid_pairs:
        return {
            "ce": None,
            "ece": None,
            "valid_predictions": 0
        }
    
    # Compute Expected Calibration Error (ECE)
    bin_boundaries = np.linspace(0, 1, num_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    ece = 0.0
    total_samples = len(valid_pairs)
    
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        # Find samples in this bin
        bin_samples = [
            (s, p) for s, p in valid_pairs
            if bin_lower <= p["p_active"] < bin_upper
        ]
        
        if not bin_samples:
            continue
        
        # Compute bin statistics
        bin_size = len(bin_samples)
        avg_pred_prob = np.mean([p["p_active"] for _, p in bin_samples])
        avg_true_prob = np.mean([s.p_active for s, _ in bin_samples])
        
        ece += (bin_size / total_samples) * abs(avg_pred_prob - avg_true_prob)
    
    # Also compute simple mean absolute error
    mae = np.mean([
        abs(p["p_active"] - s.p_active)
        for s, p in valid_pairs
    ])
    
    return {
        "ce": mae,
        "ece": ece,
        "valid_predictions": len(valid_pairs),
        "total_samples": total_samples
    }


def compute_all_metrics(
    samples: List[PTASample],
    predictions: List[Dict[str, Any]],
    paired_samples: Optional[List[Tuple[PTASample, PTASample]]] = None,
    paired_predictions: Optional[List[Tuple[Dict[str, Any], Dict[str, Any]]]] = None,
    bas_tolerance: float = 0.1,
    calibration_bins: int = 10
) -> Dict[str, Any]:
    """Compute all metrics"""
    results = {}
    
    # PPA
    ppa_results = compute_ppa(samples, predictions)
    results["ppa"] = ppa_results["ppa"]
    
    # TSU (if paired data available)
    if paired_samples and paired_predictions:
        tsu_results = compute_tsu(paired_samples, paired_predictions)
        results["tsu"] = tsu_results["tsu"]
    else:
        results["tsu"] = None
    
    # BAS
    bas_results = compute_bas(samples, predictions, tolerance=bas_tolerance)
    results["bas"] = bas_results["bas"]
    results["boundary_samples"] = bas_results["boundary_samples"]
    
    # CE
    ce_results = compute_ce(samples, predictions, num_bins=calibration_bins)
    results["ce"] = ce_results["ce"]
    results["ece"] = ce_results["ece"]
    
    return results
