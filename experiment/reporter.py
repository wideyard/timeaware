"""Reporter module for the Timeaware Benchmark Experiment.

Generates formatted reports from evaluation statistics.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional


def _fmt_pct(val: float) -> str:
    """Format a float as percentage."""
    return f"{val:.1%}"


def _fmt_table(headers: List[str], rows: List[List[str]]) -> str:
    """Format a simple ASCII table."""
    if not rows:
        return ""
    
    # Calculate column widths
    all_rows = [headers] + rows
    widths = [max(len(str(row[i])) for row in all_rows) for i in range(len(headers))]
    
    # Build table
    lines = []
    
    # Header
    header_line = " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("-+-".join("-" * w for w in widths))
    
    # Rows
    for row in rows:
        line = " | ".join(str(row[i]).ljust(widths[i]) for i in range(len(headers)))
        lines.append(line)
    
    return "\n".join(lines)


def print_dimension_report(stats: Dict[str, Any]) -> str:
    """Print accuracy by dimension."""
    lines = ["\n" + "=" * 70, "  DIMENSION ACCURACY", "=" * 70, ""]
    
    headers = ["Dimension", "Total", "Correct", "Accuracy"]
    rows = []
    
    for dim in ["T1", "T2", "T3", "T4", "T5"]:
        if dim in stats.get("by_dimension", {}):
            d = stats["by_dimension"][dim]
            rows.append([dim, str(d["total"]), str(d["correct"]), _fmt_pct(d["accuracy"])])
    
    lines.append(_fmt_table(headers, rows))
    return "\n".join(lines)


def print_subtask_report(stats: Dict[str, Any], top_n: Optional[int] = None) -> str:
    """Print accuracy by subtask."""
    lines = ["\n" + "=" * 70, "  SUBTASK ACCURACY", "=" * 70, ""]
    
    headers = ["Subtask", "Total", "Correct", "Accuracy"]
    rows = []
    
    subtasks = stats.get("by_subtask", {})
    sorted_subtasks = sorted(subtasks.items(), key=lambda x: x[1]["accuracy"])
    
    for subtask, d in sorted_subtasks:
        rows.append([subtask, str(d["total"]), str(d["correct"]), _fmt_pct(d["accuracy"])])
    
    if top_n:
        rows = rows[:top_n]
    
    lines.append(_fmt_table(headers, rows))
    return "\n".join(lines)


def print_model_report(stats: Dict[str, Any]) -> str:
    """Print accuracy by model."""
    lines = ["\n" + "=" * 70, "  MODEL ACCURACY", "=" * 70, ""]
    
    headers = ["Model", "Total", "Correct", "Accuracy"]
    rows = []
    
    for model, d in stats.get("by_model", {}).items():
        rows.append([model, str(d["total"]), str(d["correct"]), _fmt_pct(d["accuracy"])])
    
    lines.append(_fmt_table(headers, rows))
    return "\n".join(lines)


def print_mode_report(stats: Dict[str, Any]) -> str:
    """Print accuracy by conversation mode."""
    lines = ["\n" + "=" * 70, "  CONVERSATION MODE ACCURACY", "=" * 70, ""]
    
    headers = ["Mode", "Total", "Correct", "Accuracy"]
    rows = []
    
    mode_labels = {
        "single_turn": "Single-Turn",
        "multi_turn": "Multi-Turn",
        "multi_turn_noise": "Multi-Turn+Noise",
    }
    
    for mode, d in stats.get("by_mode", {}).items():
        label = mode_labels.get(mode, mode)
        rows.append([label, str(d["total"]), str(d["correct"]), _fmt_pct(d["accuracy"])])
    
    lines.append(_fmt_table(headers, rows))
    return "\n".join(lines)


def print_noise_report(stats: Dict[str, Any]) -> str:
    """Print accuracy by noise type."""
    lines = ["\n" + "=" * 70, "  NOISE TYPE ACCURACY", "=" * 70, ""]
    
    headers = ["Noise Type", "Total", "Correct", "Accuracy"]
    rows = []
    
    noise_labels = {
        "none": "No Noise",
        "hist_noise": "HistNoise",
        "confusion_noise": "ConfusionNoise",
        "num_noise": "NumNoise",
    }
    
    for noise, d in stats.get("by_noise_type", {}).items():
        label = noise_labels.get(noise, noise)
        rows.append([label, str(d["total"]), str(d["correct"]), _fmt_pct(d["accuracy"])])
    
    lines.append(_fmt_table(headers, rows))
    return "\n".join(lines)


def print_model_mode_report(stats: Dict[str, Any]) -> str:
    """Print accuracy by model × mode."""
    lines = ["\n" + "=" * 70, "  MODEL × MODE ACCURACY", "=" * 70, ""]
    
    headers = ["Model", "Mode", "Total", "Correct", "Accuracy"]
    rows = []
    
    mode_labels = {
        "single_turn": "Single",
        "multi_turn": "Multi",
        "multi_turn_noise": "Multi+Noise",
    }
    
    for key, d in sorted(stats.get("by_model_mode", {}).items()):
        parts = key.split("_", 1)
        model = parts[0]
        mode = mode_labels.get(parts[1] if len(parts) > 1 else "", parts[1] if len(parts) > 1 else "")
        rows.append([model, mode, str(d["total"]), str(d["correct"]), _fmt_pct(d["accuracy"])])
    
    lines.append(_fmt_table(headers, rows))
    return "\n".join(lines)


def print_model_noise_report(stats: Dict[str, Any]) -> str:
    """Print accuracy by model × noise type."""
    lines = ["\n" + "=" * 70, "  MODEL × NOISE TYPE ACCURACY", "=" * 70, ""]
    
    headers = ["Model", "Noise Type", "Total", "Correct", "Accuracy"]
    rows = []
    
    noise_labels = {
        "hist_noise": "HistNoise",
        "confusion_noise": "ConfusionNoise",
        "num_noise": "NumNoise",
    }
    
    for key, d in sorted(stats.get("by_model_noise", {}).items()):
        parts = key.rsplit("_", 2)
        if len(parts) >= 2:
            noise = noise_labels.get(parts[-1], parts[-1])
            model = "_".join(parts[:-1])
        else:
            model = key
            noise = ""
        rows.append([model, noise, str(d["total"]), str(d["correct"]), _fmt_pct(d["accuracy"])])
    
    lines.append(_fmt_table(headers, rows))
    return "\n".join(lines)


def print_difficulty_report(stats: Dict[str, Any]) -> str:
    """Print accuracy by difficulty."""
    lines = ["\n" + "=" * 70, "  DIFFICULTY ACCURACY", "=" * 70, ""]
    
    headers = ["Difficulty", "Total", "Correct", "Accuracy"]
    rows = []
    
    for diff in ["easy", "medium", "hard", "very_hard"]:
        if diff in stats.get("by_difficulty", {}):
            d = stats["by_difficulty"][diff]
            rows.append([diff, str(d["total"]), str(d["correct"]), _fmt_pct(d["accuracy"])])
    
    lines.append(_fmt_table(headers, rows))
    return "\n".join(lines)


def print_full_report(stats: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Print the complete evaluation report."""
    sections = [
        f"\n{'='*70}",
        f"  TIMEAWARE BENCHMARK EXPERIMENT REPORT",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"{'='*70}",
        f"\n  Overall: {stats['overall']['correct']}/{stats['overall']['total']} "
        f"({_fmt_pct(stats['overall']['accuracy'])})",
        "",
        print_dimension_report(stats),
        print_subtask_report(stats),
        print_model_report(stats),
        print_mode_report(stats),
        print_noise_report(stats),
        print_model_mode_report(stats),
        print_model_noise_report(stats),
        print_difficulty_report(stats),
        f"\n{'='*70}",
        f"  END OF REPORT",
        f"{'='*70}",
    ]
    
    report_text = "\n".join(sections)
    print(report_text)
    
    # Also save to file
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save text report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        # Save JSON report
        json_path = output_path.replace('.txt', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved to: {output_path}")
        print(f"JSON stats saved to: {json_path}")
    
    return report_text
