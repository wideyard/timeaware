"""Main entry point for the Timeaware Benchmark Experiment.

Usage:
    python -m experiment.main                    # Run full experiment
    python -m experiment.main --dry-run           # Sample data only, no API calls
    python -m experiment.main --subtasks T1-Ordering T2-StateTrack  # Filter subtasks
    python -m experiment.main --models gpt-4o-mini                  # Filter models
    python -m experiment.main --resume results/experiment_results.json  # Resume from partial results
"""

import sys
import os
import json
import argparse
import time
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiment.subtask_config import (
    SUBTASK_CONFIG, EVAL_MODELS, OUTPUT_DIR,
)
from experiment.sampler import sample_all_subtasks, get_sample_statistics
from experiment.runner import run_experiment, save_results
from experiment.evaluator import evaluate_all_results, compute_accuracy
from experiment.reporter import print_full_report


def parse_args():
    parser = argparse.ArgumentParser(description="Timeaware Benchmark Experiment")
    parser.add_argument("--dry-run", action="store_true",
                        help="Sample data only, don't make API calls")
    parser.add_argument("--subtasks", nargs="+", default=None,
                        help="Filter to specific subtask keys (e.g., T1-Ordering T2-StateTrack)")
    parser.add_argument("--models", nargs="+", default=None,
                        help="Filter to specific models")
    parser.add_argument("--modes", nargs="+", default=None,
                        choices=["single_turn", "multi_turn", "multi_turn_noise"],
                        help="Conversation modes to test")
    parser.add_argument("--sample-count", type=int, default=10,
                        help="Samples per atomic task (default: 10)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Delay between API calls in seconds")
    parser.add_argument("--resume", type=str, default=None,
                        help="Resume from existing results file")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory")
    parser.add_argument("--skip-eval", action="store_true",
                        help="Skip LLM-as-judge evaluation")
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = args.output_dir or OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=" * 70)
    print("  TIMEAWARE BENCHMARK EXPERIMENT")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Seed: {args.seed}")
    print(f"  Sample count: {args.sample_count} per atomic task")
    if args.subtasks:
        print(f"  Subtasks: {args.subtasks}")
    if args.models:
        print(f"  Models: {args.models}")
    print("=" * 70)
    
    # Step 1: Sample data
    print("\n" + "=" * 60)
    print("  STEP 1: Sampling Data")
    print("=" * 60)
    
    samples = sample_all_subtasks(
        sample_count=args.sample_count,
        seed=args.seed,
        subtask_filter=args.subtasks,
    )
    
    # Print sampling statistics
    sample_stats = get_sample_statistics(samples)
    print(f"\n  Total samples: {sample_stats['total_samples']}")
    print(f"  By dimension:")
    for dim, count in sorted(sample_stats['by_dimension'].items()):
        print(f"    {dim}: {count}")
    
    # Save sampled data
    sample_path = os.path.join(output_dir, f"sampled_data_{timestamp}.json")
    with open(sample_path, 'w', encoding='utf-8') as f:
        # Save without full sample content (just metadata)
        sample_meta = {}
        for key, slist in samples.items():
            sample_meta[key] = [{
                "source_id": s.get("source_id", ""),
                "sub_task": s.get("sub_task", ""),
                "difficulty": s.get("difficulty", ""),
                "task": s.get("task", ""),
            } for s in slist]
        json.dump({"statistics": sample_stats, "samples": sample_meta}, f, ensure_ascii=False, indent=2)
    print(f"  Sample metadata saved to: {sample_path}")
    
    if args.dry_run:
        print("\n  [DRY RUN] Stopping here. No API calls made.")
        return
    
    # Step 2: Run experiment (LLM calls)
    print("\n" + "=" * 60)
    print("  STEP 2: Running Experiment")
    print("=" * 60)
    
    # Check if resuming
    existing_results = []
    if args.resume and os.path.exists(args.resume):
        print(f"\n  Resuming from: {args.resume}")
        with open(args.resume, 'r', encoding='utf-8') as f:
            existing_results = json.load(f)
        print(f"  Loaded {len(existing_results)} existing results")
    
    results = run_experiment(
        samples=samples,
        models=args.models or EVAL_MODELS,
        modes=args.modes,
        delay=args.delay,
    )
    
    # Merge with existing results if resuming
    if existing_results:
        # Deduplicate by checking source_id + model + mode + noise_type
        existing_keys = set()
        for r in existing_results:
            key = (r.get('source_id', ''), r.get('model', ''), r.get('mode', ''), r.get('noise_type', ''))
            existing_keys.add(key)
        
        new_results = []
        for r in results:
            key = (r.get('source_id', ''), r.get('model', ''), r.get('mode', ''), r.get('noise_type', ''))
            if key not in existing_keys:
                new_results.append(r)
        
        results = existing_results + new_results
        print(f"\n  Merged: {len(existing_results)} existing + {len(new_results)} new = {len(results)} total")
    
    # Save raw results
    results_path = os.path.join(output_dir, f"experiment_results_{timestamp}.json")
    save_results(results, results_path)
    
    # Step 3: Evaluate
    if not args.skip_eval:
        print("\n" + "=" * 60)
        print("  STEP 3: Evaluating Results")
        print("=" * 60)
        
        evaluated = evaluate_all_results(results, delay=args.delay)
        
        # Save evaluated results
        eval_path = os.path.join(output_dir, f"evaluated_results_{timestamp}.json")
        with open(eval_path, 'w', encoding='utf-8') as f:
            json.dump(evaluated, f, ensure_ascii=False, indent=2)
        print(f"\n  Evaluated results saved to: {eval_path}")
        
        # Step 4: Generate report
        print("\n" + "=" * 60)
        print("  STEP 4: Generating Report")
        print("=" * 60)
        
        stats = compute_accuracy(evaluated)
        report_path = os.path.join(output_dir, f"report_{timestamp}.txt")
        print_full_report(stats, output_path=report_path)
    else:
        print("\n  [SKIP EVAL] Evaluation skipped.")
    
    print("\n" + "=" * 60)
    print("  EXPERIMENT COMPLETE")
    print("=" * 60)
    print(f"  Results: {results_path}")
    if not args.skip_eval:
        print(f"  Report: {report_path}")
    print()


if __name__ == "__main__":
    main()
