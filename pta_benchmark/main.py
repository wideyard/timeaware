"""
PTA Benchmark - Main Entry Point

Probabilistic Temporal Alignment Benchmark for evaluating LLMs
on time-aware decision making under implicit commonsense uncertainty.
"""

import os
import json
import argparse
from typing import List, Dict, Any
from dataclasses import asdict

from pta_benchmark.config import DataConfig, EvalConfig, OUTPUT_DIR
from pta_benchmark.data import PTADatasetGenerator, PTASample, generate_ablation_dataset
from pta_benchmark.models import (
    RandomModel,
    MajorityModel,
    HeuristicModel,
    OracleModel,
    ThresholdModel,
    BaseModel,
    LLMModel,
)
from pta_benchmark.metrics import compute_all_metrics
from pta_benchmark.analysis import generate_analysis_report


LLM_MODELS = ["gpt-4o-mini", "doubao-seed-1-8", "doubao-seed-2-0-pro"]


def run_evaluation(
    model: BaseModel,
    samples: List[PTASample],
    paired_samples=None,
    eval_config: EvalConfig = None
) -> Dict[str, Any]:
    """Run evaluation for a single model"""
    config = eval_config or EvalConfig()
    
    # Get predictions
    predictions = model.predict_batch(samples)
    
    # Get paired predictions if available
    paired_predictions = None
    if paired_samples:
        paired_predictions = [
            (model.predict(s1), model.predict(s2))
            for s1, s2 in paired_samples
        ]
    
    # Compute metrics
    metrics = compute_all_metrics(
        samples=samples,
        predictions=predictions,
        paired_samples=paired_samples,
        paired_predictions=paired_predictions,
        bas_tolerance=config.bas_tolerance,
        calibration_bins=config.calibration_bins
    )
    
    # Generate analysis
    analysis = generate_analysis_report(samples, predictions, model.name)
    
    return {
        "model_name": model.name,
        "metrics": metrics,
        "analysis": analysis,
        "predictions": predictions
    }


def print_results_table(results: List[Dict[str, Any]]):
    """Print results in a formatted table"""
    print("\n" + "=" * 80)
    print("PTA Benchmark Results")
    print("=" * 80)
    
    # Header
    header = f"{'Model':<25} {'PPA':>8} {'TSU':>8} {'BAS':>8} {'CE':>8} {'ECE':>8}"
    print(header)
    print("-" * 80)
    
    # Rows
    for result in results:
        metrics = result["metrics"]
        name = result["model_name"]
        ppa = f"{metrics['ppa']:.3f}" if metrics['ppa'] is not None else "N/A"
        tsu = f"{metrics['tsu']:.3f}" if metrics['tsu'] is not None else "N/A"
        bas = f"{metrics['bas']:.3f}" if metrics['bas'] is not None else "N/A"
        ce = f"{metrics['ce']:.3f}" if metrics['ce'] is not None else "N/A"
        ece = f"{metrics['ece']:.3f}" if metrics['ece'] is not None else "N/A"
        
        print(f"{name:<25} {ppa:>8} {tsu:>8} {bas:>8} {ce:>8} {ece:>8}")
    
    print("=" * 80)


def print_analysis_details(results: List[Dict[str, Any]]):
    """Print detailed analysis for each model"""
    for result in results:
        print(f"\n{'='*60}")
        print(f"Analysis: {result['model_name']}")
        print(f"{'='*60}")
        
        analysis = result["analysis"]
        
        # Region breakdown
        print("\nPerformance by Delta-t Region:")
        print("-" * 40)
        for region, data in analysis["region_breakdown"].items():
            print(f"  {region:<10}: {data['accuracy']:.3f} ({data['correct']}/{data['total']})")
        
        # Error breakdown
        print("\nError Categorization:")
        print("-" * 40)
        error_counts = analysis["error_counts"]
        total = sum(error_counts.values())
        for error_type, count in error_counts.items():
            pct = count / total * 100 if total > 0 else 0
            print(f"  {error_type:<20}: {count:>4} ({pct:.1f}%)")
        
        # Action distribution
        print("\nAction Distribution:")
        print("-" * 40)
        pred_dist = analysis["action_distribution"]["predicted"]
        true_dist = analysis["action_distribution"]["ground_truth"]
        all_actions = set(list(pred_dist.keys()) + list(true_dist.keys()))
        for action in sorted(all_actions):
            pred = pred_dist.get(action, 0)
            true = true_dist.get(action, 0)
            print(f"  {action:<12}: predicted={pred:>4}, ground_truth={true:>4}")


def run_ablation_study(
    model_class,
    samples: List[PTASample],
    paired_samples,
    ablation_types: List[str],
    **model_kwargs
) -> List[Dict[str, Any]]:
    """Run ablation study"""
    print("\n" + "=" * 60)
    print("Ablation Study")
    print("=" * 60)
    
    ablation_results = []
    
    # Baseline (no ablation)
    model = model_class(**model_kwargs)
    baseline_result = run_evaluation(model, samples, paired_samples)
    ablation_results.append({
        "ablation": "baseline",
        "result": baseline_result
    })
    print(f"\nBaseline PPA: {baseline_result['metrics']['ppa']:.3f}")
    
    # Each ablation
    for ablation_type in ablation_types:
        ablated_samples = generate_ablation_dataset(samples, ablation_type)
        model = model_class(**model_kwargs)
        result = run_evaluation(model, ablated_samples, paired_samples)
        ablation_results.append({
            "ablation": ablation_type,
            "result": result
        })
        delta = result['metrics']['ppa'] - baseline_result['metrics']['ppa']
        print(f"{ablation_type:<25} PPA: {result['metrics']['ppa']:.3f} (delta: {delta:+.3f})")
    
    return ablation_results


def save_results(
    results: List[Dict[str, Any]],
    ablation_results: List[Dict[str, Any]],
    output_dir: str,
    save_predictions: bool = False
):
    """Save all results to files"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save main results
    main_results_path = os.path.join(output_dir, "benchmark_results.json")
    serializable_results = []
    for r in results:
        result_data = {
            "model_name": r["model_name"],
            "metrics": r["metrics"],
            "analysis": r["analysis"]
        }
        if save_predictions and "predictions" in r:
            result_data["predictions"] = [
                {k: v for k, v in p.items() if k != "raw_response"}
                for p in r["predictions"]
            ]
        serializable_results.append(result_data)
    
    with open(main_results_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {main_results_path}")
    
    # Save ablation results
    if ablation_results:
        ablation_path = os.path.join(output_dir, "ablation_results.json")
        serializable_ablation = []
        for ar in ablation_results:
            serializable_ablation.append({
                "ablation": ar["ablation"],
                "model_name": ar["result"]["model_name"],
                "metrics": ar["result"]["metrics"]
            })
        
        with open(ablation_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_ablation, f, indent=2, ensure_ascii=False)
        print(f"Ablation results saved to: {ablation_path}")


def initialize_baseline_models(args) -> List[BaseModel]:
    """Initialize baseline (non-LLM) models"""
    return [
        RandomModel(seed=args.seed),
        MajorityModel(majority_action="defer"),
        HeuristicModel(use_expanded=args.expanded),
        ThresholdModel(use_expanded=args.expanded),
        OracleModel(use_expanded=args.expanded)
    ]


def initialize_llm_models(args) -> List[LLMModel]:
    """Initialize LLM models based on args"""
    models = []
    
    # Determine which models to use
    if args.llm_models:
        model_keys = [m for m in args.llm_models if m in LLM_MODELS]
        if not model_keys:
            print(f"Warning: No valid LLM models specified. Using {LLM_MODELS[0]}.")
            model_keys = [LLM_MODELS[0]]
    else:
        model_keys = LLM_MODELS
    
    # Determine languages
    languages = []
    if args.lang in ["en", "zh"]:
        languages = [args.lang]
    elif args.lang == "both":
        languages = ["en", "zh"]
    else:
       
        languages = ["en"]
    
    for model_key in model_keys:
        for lang in languages:
            lang_display = "EN" if lang == "en" else "ZH"
            print(f"  - {model_key} ({lang_display})")
            model = LLMModel(
                model_key=model_key,
                language=lang,
                use_expanded=args.expanded,
                rate_limit_delay=args.rate_limit_delay,
            )
            models.append(model)
    
    return models


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="PTA Benchmark")
    
    # Data generation args
    parser.add_argument("--num_samples", type=int, default=500, help="Number of samples")
    parser.add_argument("--num_pairs", type=int, default=100, help="Number of paired samples for TSU")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--expanded", action="store_true", help="Use expanded activities from MCTACO")
    
    # Model selection args
    parser.add_argument("--baselines", action="store_true", default=True, help="Evaluate baseline models (default: True)")
    parser.add_argument("--no-baselines", action="store_false", dest="baselines", help="Skip baseline models")
    parser.add_argument("--llm", action="store_true", help="Evaluate LLM models")
    parser.add_argument("--llm_models", nargs="+", choices=LLM_MODELS, help=f"LLM models to evaluate: {LLM_MODELS}")
    parser.add_argument("--lang", type=str, default="en", choices=["en", "zh", "both"], help="Prompt language")
    
    # LLM-specific args
    parser.add_argument("--rate_limit_delay", type=float, default=0.5, help="Delay between LLM API calls (seconds)")
    
    # Output args
    parser.add_argument("--output_dir", type=str, default=OUTPUT_DIR, help="Output directory")
    parser.add_argument("--save_predictions", action="store_true", help="Save prediction details")
    
    # Analysis args
    parser.add_argument("--ablation", action="store_true", help="Run ablation study")
    parser.add_argument("--detailed", action="store_true", help="Print detailed analysis")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("PTA Benchmark - Probabilistic Temporal Alignment")
    print("=" * 60)
    if args.expanded:
        print("(Using expanded activities from MCTACO)")
    
    # Configuration
    data_config = DataConfig(
        num_samples=args.num_samples, 
        seed=args.seed,
        use_expanded_activities=args.expanded
    )
    eval_config = EvalConfig()
    
    # Generate dataset
    print(f"\nGenerating dataset with {args.num_samples} samples...")
    generator = PTADatasetGenerator(data_config)
    samples = generator.generate_dataset()
    print(f"  Using {len(generator.activities)} activities")
    
    print(f"Generating {args.num_pairs} paired samples for TSU...")
    paired_samples = generator.generate_paired_samples(args.num_pairs)
    
    # Save dataset
    dataset_path = os.path.join(args.output_dir, "dataset.json")
    generator.save_dataset(samples, dataset_path)
    print(f"Dataset saved to: {dataset_path}")
    
    # Initialize models
    print("\nInitializing models...")
    models: List[BaseModel] = []
    
    if args.baselines:
        print("  Baseline models:")
        for model in initialize_baseline_models(args):
            print(f"    - {model.name}")
            models.append(model)
    
    if args.llm:
        print("  LLM models:")
        for model in initialize_llm_models(args):
            models.append(model)
    
    if not models:
        print("Error: No models selected for evaluation. Use --baselines and/or --llm")
        return
    
    # Run evaluation
    print("\nRunning evaluation...")
    results = []
    for model in models:
        print(f"\n  Evaluating {model.name}...")
        result = run_evaluation(model, samples, paired_samples, eval_config)
        results.append(result)
        print(f"    PPA: {result['metrics']['ppa']:.3f}")
    
    # Print results
    print_results_table(results)
    
    if args.detailed:
        print_analysis_details(results)
    
    # Run ablation study (for baselines only)
    ablation_results = []
    if args.ablation and args.baselines:
        ablation_results = run_ablation_study(
            ThresholdModel,
            samples,
            paired_samples,
            ["remove_time", "remove_commonsense", "deterministic_duration"],
            use_expanded=args.expanded
        )
    
    # Save results
    save_results(results, ablation_results, args.output_dir, args.save_predictions)
    
    print("\nBenchmark complete!")
    return results, ablation_results


if __name__ == "__main__":
    main()
