"""TimeAware Benchmark - 主入口

基于 arich.md 的统一时间推理评测框架

功能:
1. 统一的数据格式和任务定义
2. 五大任务的数据生成和评测
3. 三层评测模块（Answer/State/Chain）
4. 多模型对比实验
"""

import json
import argparse
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from .task_schema import (
    TemporalSample, TaskType, DifficultyLevel,
    get_task_description, get_task_metrics
)
from .dataset_adapter import convert_all_datasets, DatasetConverter
from .task_generators import TaskGeneratorFactory, TaskConfig
from .evaluation import TemporalBenchmarkEvaluator, EvaluationResult
from llm_client import call_llm_json, call_llm


OUTPUT_DIR = Path(__file__).parent.parent / "output" / "arch"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_tasks(
    task_types: List[TaskType] = None,
    num_samples: int = 50,
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
    output_path: str = None
) -> Dict[TaskType, List[TemporalSample]]:
    """生成所有任务的样本
    
    Args:
        task_types: 要生成的任务类型列表，None表示全部
        num_samples: 每个任务的样本数
        difficulty: 难度级别
        output_path: 输出路径
    
    Returns:
        任务类型到样本列表的映射
    """
    if task_types is None:
        task_types = list(TaskType)
    
    results = {}
    
    for task_type in task_types:
        print(f"\n{'='*60}")
        print(f"生成 {get_task_description(task_type)}")
        print(f"{'='*60}")
        
        config = TaskConfig(
            task_type=task_type,
            difficulty=difficulty,
            num_samples=num_samples
        )
        
        generator = TaskGeneratorFactory.create(task_type, config)
        samples = generator.generate()
        
        results[task_type] = samples
        print(f"生成了 {len(samples)} 个样本")
    
    if output_path:
        save_generated_samples(results, output_path)
    
    return results


def save_generated_samples(
    samples: Dict[TaskType, List[TemporalSample]], 
    output_path: str
):
    """保存生成的样本"""
    output_data = {}
    
    for task_type, sample_list in samples.items():
        output_data[task_type.value] = [s.to_dict() for s in sample_list]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n样本已保存到: {output_path}")


def load_converted_data(data_path: str) -> List[TemporalSample]:
    """加载转换后的数据集"""
    samples = []
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            samples.append(TemporalSample.from_dict(item))
    
    return samples


def run_model_prediction(
    samples: List[TemporalSample],
    model_key: str = "gpt-4o-mini"
) -> List[Dict[str, Any]]:
    """运行模型预测
    
    Args:
        samples: 样本列表
        model_key: 模型名称
    
    Returns:
        预测结果列表
    """
    predictions = []
    
    system_prompt = """你是一个时间推理专家。请根据给定的上下文和问题，给出准确的回答。

回答格式（JSON）：
{
    "answer": "你的答案",
    "state": {"字段": "值"},  // 可选，用于状态追踪任务
    "reasoning": "推理过程"  // 可选
}"""
    
    for i, sample in enumerate(samples):
        print(f"\r处理样本 {i+1}/{len(samples)}...", end="", flush=True)
        
        prompt = f"""{sample.to_input_format()}

请用JSON格式回答：
{{
    "answer": "...",
    "state": {{...}},  // 可选
    "reasoning": "..."  // 可选
}}"""
        
        try:
            response = call_llm(prompt, system_prompt=system_prompt, temperature=0.3, model_key=model_key)
            prediction = parse_model_response(response)
            predictions.append(prediction)
        except Exception as e:
            predictions.append({"answer": "", "error": str(e)})
    
    print()  # 换行
    return predictions


def parse_model_response(response: str) -> Dict[str, Any]:
    """解析模型响应"""
    try:
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "{" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
        else:
            return {"answer": response.strip()}
        
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"answer": response.strip()}


def run_evaluation(
    samples: List[TemporalSample],
    predictions: List[Dict[str, Any]],
    save_path: str = None
) -> Dict[str, Any]:
    """运行评测
    
    Args:
        samples: 样本列表
        predictions: 预测结果列表
        save_path: 保存路径
    
    Returns:
        评测报告
    """
    evaluator = TemporalBenchmarkEvaluator()
    results = evaluator.evaluate(samples, predictions)
    report = evaluator.generate_report()
    
    if save_path:
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n评测报告已保存到: {save_path}")
    
    return report


def print_report(report: Dict[str, Any]):
    """打印评测报告"""
    print("\n" + "=" * 70)
    print("TimeAware Benchmark 评测报告")
    print("=" * 70)
    
    summary = report.get("summary", {})
    
    overall = summary.get("overall", {})
    print(f"\n【总体结果】")
    print(f"  总样本数: {overall.get('total_samples', 0)}")
    print(f"  准确率: {overall.get('accuracy', 0):.2%}")
    
    by_task = summary.get("by_task", {})
    if by_task:
        print(f"\n【按任务类型】")
        print(f"  {'任务':<35} {'数量':<8} {'准确率':<10}")
        print(f"  {'-'*53}")
        for task_type, metrics in by_task.items():
            task_name = task_type.replace("t", "T").replace("_", " ").title()
            print(f"  {task_name:<35} {metrics.get('total', 0):<8} {metrics.get('accuracy', 0):.2%}")
    
    by_difficulty = summary.get("by_difficulty", {})
    if by_difficulty:
        print(f"\n【按难度级别】")
        print(f"  {'难度':<15} {'数量':<8} {'准确率':<10}")
        print(f"  {'-'*33}")
        for difficulty, metrics in by_difficulty.items():
            print(f"  {difficulty:<15} {metrics.get('total', 0):<8} {metrics.get('accuracy', 0):.2%}")
    
    print("\n" + "=" * 70)


def run_comparison_experiment(
    samples: List[TemporalSample],
    models: List[str] = None
) -> Dict[str, Dict[str, Any]]:
    """运行多模型对比实验
    
    Args:
        samples: 样本列表
        models: 模型列表
    
    Returns:
        每个模型的评测结果
    """
    if models is None:
        models = ["gpt-4o-mini", "doubao-seed-1-8"]
    
    results = {}
    
    for model in models:
        print(f"\n{'='*60}")
        print(f"评测模型: {model}")
        print(f"{'='*60}")
        
        predictions = run_model_prediction(samples, model)
        
        report = run_evaluation(
            samples, 
            predictions,
            save_path=str(OUTPUT_DIR / f"eval_{model}.json")
        )
        
        results[model] = report
    
    print_comparison_table(results)
    
    return results


def print_comparison_table(results: Dict[str, Dict[str, Any]]):
    """打印对比表格"""
    print("\n" + "=" * 70)
    print("Model Comparison Table")
    print("=" * 70)
    
    print(f"\n{'Model':<25} {'T1':<10} {'T2':<10} {'T3':<10} {'T4':<10} {'T5':<10} {'Overall':<10}")
    print("-" * 85)
    
    for model, report in results.items():
        summary = report.get("summary", {})
        by_task = summary.get("by_task", {})
        overall = summary.get("overall", {})
        
        task_accs = []
        for task in ["t1_temporal_calculation", "t2_state_tracking", "t3_concurrency", 
                     "t4_long_term_memory", "t5_counterfactual"]:
            acc = by_task.get(task, {}).get("accuracy", 0)
            task_accs.append(f"{acc:.2f}")
        
        overall_acc = overall.get("accuracy", 0)
        task_accs.append(f"{overall_acc:.2f}")
        
        print(f"{model:<25} {' '.join(task_accs)}")
    
    print("=" * 70)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="TimeAware Benchmark - 统一时间推理评测框架")
    
    parser.add_argument("--convert-data", action="store_true", 
                       help="转换现有数据集为统一格式")
    parser.add_argument("--generate", action="store_true",
                       help="生成新的任务样本")
    parser.add_argument("--evaluate", action="store_true",
                       help="运行评测")
    parser.add_argument("--compare", action="store_true",
                       help="运行多模型对比")
    
    parser.add_argument("--task", type=str, nargs="+", 
                       choices=[t.value for t in TaskType],
                       help="指定任务类型")
    parser.add_argument("--num-samples", type=int, default=50,
                       help="每个任务的样本数")
    parser.add_argument("--difficulty", type=str, default="medium",
                       choices=["easy", "medium", "hard"],
                       help="难度级别")
    parser.add_argument("--model", type=str, default="gpt-4o-mini",
                       help="评测模型")
    parser.add_argument("--models", type=str, nargs="+",
                       help="对比实验的模型列表")
    
    parser.add_argument("--data-dir", type=str, default="data",
                       help="数据目录")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR),
                       help="输出目录")
    
    args = parser.parse_args()
    
    difficulty = DifficultyLevel(args.difficulty)
    
    if args.convert_data:
        print("转换数据集为统一格式...")
        output_path = os.path.join(args.output_dir, "converted")
        convert_all_datasets(args.data_dir, output_path)
    
    if args.generate:
        task_types = None
        if args.task:
            task_types = [TaskType(t) for t in args.task]
        
        output_path = os.path.join(args.output_dir, "generated_samples.json")
        generate_tasks(task_types, args.num_samples, difficulty, output_path)
    
    if args.evaluate:
        data_path = os.path.join(args.output_dir, "converted", "all_samples.json")
        if not os.path.exists(data_path):
            print(f"数据文件不存在: {data_path}")
            print("请先运行 --convert-data 生成数据")
            return
        
        print(f"加载数据: {data_path}")
        samples = load_converted_data(data_path)
        print(f"加载了 {len(samples)} 个样本")
        
        predictions = run_model_prediction(samples, args.model)
        
        save_path = os.path.join(args.output_dir, f"eval_{args.model}.json")
        report = run_evaluation(samples, predictions, save_path)
        
        print_report(report)
    
    if args.compare:
        data_path = os.path.join(args.output_dir, "converted", "all_samples.json")
        if not os.path.exists(data_path):
            print(f"数据文件不存在: {data_path}")
            return
        
        samples = load_converted_data(data_path)
        models = args.models or ["gpt-4o-mini", "doubao-seed-1-8"]
        run_comparison_experiment(samples, models)
    
    if not any([args.convert_data, args.generate, args.evaluate, args.compare]):
        parser.print_help()


if __name__ == "__main__":
    main()
