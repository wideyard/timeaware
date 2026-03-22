"""时间推理Benchmark生成器 - 主入口（支持多模型对比）"""

import json
import sys
from typing import Dict, List, Any

from config import (
    QA_COUNT_PER_TYPE, 
    DIALOGUE_TEMPLATE_INSTANCES,
    QA_OUTPUT_PATH,
    DIALOGUE_OUTPUT_PATH,
    EVALUATION_OUTPUT_PATH,
    COMPARISON_OUTPUT_PATH,
    EVAL_MODELS,
    DEFAULT_MODEL
)
from qa_types import QA_GENERATORS, QA_TYPE_DESCRIPTIONS
from dialogue import DialogueTemplateEngine, TranscriptProber, JSONStateEvaluator
from judge import LLMJudge
from evaluator import Evaluator
from llm_client import call_llm


def generate_qa_benchmark(count_per_type: int = QA_COUNT_PER_TYPE) -> Dict[str, List]:
    """生成QA benchmark（使用默认模型）"""
    print("\n" + "=" * 60)
    print("开始生成QA Benchmark")
    print("=" * 60)
    
    all_qa = {}
    
    for qa_type, generator in QA_GENERATORS.items():
        print(f"\n正在生成 {QA_TYPE_DESCRIPTIONS[qa_type]}...")
        try:
            questions = generator(count_per_type)
            all_qa[qa_type] = questions
            print(f"  成功生成 {len(questions)} 道题目")
        except Exception as e:
            print(f"  生成失败: {e}")
            all_qa[qa_type] = []
    
    return all_qa


def generate_dialogue_benchmark(instances_per_template: int = DIALOGUE_TEMPLATE_INSTANCES) -> Dict:
    """生成对话 benchmark"""
    print("\n" + "=" * 60)
    print("开始生成Dialogue Benchmark")
    print("=" * 60)
    
    engine = DialogueTemplateEngine()
    prober = TranscriptProber()
    state_evaluator = JSONStateEvaluator()
    
    result = {
        "template_instances": [],
        "transcript_probes": [],
        "state_evaluations": []
    }
    
    # 1. 生成模板实例
    print("\n正在生成模板实例...")
    template_instances = engine.generate_all_instances(instances_per_template)
    result["template_instances"] = template_instances
    print(f"  成功生成 {len(template_instances)} 个模板实例")
    
    # 2. 从模板生成探针题目
    print("\n正在从模板生成探针题目...")
    for instance in template_instances:
        probe = prober.generate_from_template(instance)
        if probe:
            result["transcript_probes"].append(probe)
    print(f"  成功生成 {len(result['transcript_probes'])} 道探针题目")
    
    # 3. 生成LLM创作的探针题目
    print("\n正在生成LLM创作的探针题目...")
    llm_probes = prober.generate_transcript_probes(10)
    result["transcript_probes"].extend(llm_probes)
    print(f"  成功生成 {len(llm_probes)} 道LLM探针题目")
    
    # 4. 从模板生成状态评估题目
    print("\n正在生成状态评估题目...")
    for instance in template_instances:
        state_eval = state_evaluator.generate_from_template(instance)
        if state_eval:
            result["state_evaluations"].append(state_eval)
    print(f"  成功生成 {len(result['state_evaluations'])} 道状态评估题目")
    
    # 5. 生成LLM创作的状态评估题目
    print("\n正在生成LLM创作的状态评估题目...")
    llm_state_evals = state_evaluator.generate_state_evaluations(5)
    result["state_evaluations"].extend(llm_state_evals)
    print(f"  成功生成 {len(llm_state_evals)} 道LLM状态评估题目")
    
    return result


def evaluate_model_on_qa(questions: List[Dict], model_key: str) -> List[Dict]:
    """使用指定模型回答QA题目
    
    Args:
        questions: 题目列表
        model_key: 模型键名
    
    Returns:
        List[Dict]: 包含模型回答的结果列表
    """
    results = []
    
    for q in questions:
        # 构建prompt
        options_text = "\n".join([f"{k}. {v}" for k, v in q.get("options", {}).items()])
        prompt = f"""请回答以下时间推理问题，只返回选项字母（A/B/C/D）。

【问题】{q.get('question', '')}

【选项】
{options_text}

请直接返回答案字母，不要解释。"""
        
        try:
            response = call_llm(prompt, temperature=0.3, model_key=model_key)
            # 提取答案字母
            answer = response.strip().upper()
            if answer and answer[0] in ['A', 'B', 'C', 'D']:
                predicted = answer[0]
            else:
                predicted = "X"  # 无法解析
            
            results.append({
                "question_id": q.get("id", "unknown"),
                "question_type": q.get("type", "unknown"),
                "correct_answer": q.get("answer", ""),
                "predicted_answer": predicted,
                "is_correct": predicted == q.get("answer", ""),
                "raw_response": response[:100]  # 保存部分原始响应
            })
        except Exception as e:
            results.append({
                "question_id": q.get("id", "unknown"),
                "question_type": q.get("type", "unknown"),
                "correct_answer": q.get("answer", ""),
                "predicted_answer": "ERROR",
                "is_correct": False,
                "error": str(e)
            })
    
    return results


def run_comparison_experiment(qa_benchmark: Dict[str, List], models: List[str]) -> Dict:
    """运行多模型对比实验
    
    Args:
        qa_benchmark: QA题目字典
        models: 要评测的模型列表
    
    Returns:
        Dict: 对比实验结果
    """
    print("\n" + "=" * 60)
    print("开始多模型对比实验")
    print("=" * 60)
    
    comparison_results = {}
    
    for model_key in models:
        print(f"\n正在评测模型: {model_key}")
        model_results = {
            "model_name": model_key,
            "by_type": {},
            "overall": {
                "total": 0,
                "correct": 0,
                "accuracy": 0.0
            }
        }
        
        all_results = []
        
        for qa_type, questions in qa_benchmark.items():
            if not questions:
                continue
            
            print(f"  评测 {QA_TYPE_DESCRIPTIONS[qa_type]} ({len(questions)}题)...")
            type_results = evaluate_model_on_qa(questions, model_key)
            all_results.extend(type_results)
            
            # 统计该类型结果
            total = len(type_results)
            correct = sum(1 for r in type_results if r["is_correct"])
            
            model_results["by_type"][qa_type] = {
                "total": total,
                "correct": correct,
                "accuracy": correct / total if total > 0 else 0.0,
                "details": type_results
            }
        
        # 统计总体结果
        total_all = len(all_results)
        correct_all = sum(1 for r in all_results if r["is_correct"])
        
        model_results["overall"] = {
            "total": total_all,
            "correct": correct_all,
            "accuracy": correct_all / total_all if total_all > 0 else 0.0
        }
        
        comparison_results[model_key] = model_results
        print(f"  {model_key} 总体准确率: {model_results['overall']['accuracy']:.1%}")
    
    return comparison_results


def validate_benchmark(qa_benchmark: Dict[str, List], dialogue_benchmark: Dict) -> Evaluator:
    """验证benchmark质量"""
    print("\n" + "=" * 60)
    print("开始验证Benchmark质量")
    print("=" * 60)
    
    judge = LLMJudge()
    evaluator = Evaluator()
    
    # 1. 验证QA题目
    print("\n正在验证QA题目...")
    for qa_type, questions in qa_benchmark.items():
        if questions:
            print(f"  验证 {QA_TYPE_DESCRIPTIONS[qa_type]}...")
            validation_results = judge.validate_batch(questions, "qa")
            
            # 添加验证结果到题目
            for q, v in zip(questions, validation_results):
                q["validation_result"] = v
                q["validation_score"] = v.get("quality_score", 0)
            
            evaluator.add_qa_evaluation(qa_type, questions, validation_results)
            
            valid_count = sum(1 for v in validation_results if v.get("is_valid", False))
            print(f"    有效: {valid_count}/{len(questions)}")
    
    # 2. 验证对话探针题目
    print("\n正在验证对话探针题目...")
    transcript_probes = dialogue_benchmark.get("transcript_probes", [])
    if transcript_probes:
        validation_results = judge.validate_batch(transcript_probes, "dialogue")
        
        for q, v in zip(transcript_probes, validation_results):
            q["validation_result"] = v
            q["validation_score"] = v.get("quality_score", 0)
        
        evaluator.add_dialogue_evaluation("transcript_probes", transcript_probes, validation_results)
        
        valid_count = sum(1 for v in validation_results if v.get("is_valid", False))
        print(f"  有效: {valid_count}/{len(transcript_probes)}")
    
    return evaluator


def save_results(qa_benchmark: Dict[str, List], dialogue_benchmark: Dict, 
                 evaluator: Evaluator, comparison_results: Dict = None):
    """保存所有结果"""
    print("\n" + "=" * 60)
    print("保存结果")
    print("=" * 60)
    
    # 保存QA benchmark
    with open(QA_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(qa_benchmark, f, ensure_ascii=False, indent=2)
    print(f"\nQA Benchmark 已保存到: {QA_OUTPUT_PATH}")
    
    # 保存对话 benchmark
    with open(DIALOGUE_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dialogue_benchmark, f, ensure_ascii=False, indent=2)
    print(f"Dialogue Benchmark 已保存到: {DIALOGUE_OUTPUT_PATH}")
    
    # 保存评估报告
    report = evaluator.save_report(EVALUATION_OUTPUT_PATH)
    
    # 保存对比实验结果
    if comparison_results:
        with open(COMPARISON_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(comparison_results, f, ensure_ascii=False, indent=2)
        print(f"对比实验报告 已保存到: {COMPARISON_OUTPUT_PATH}")
    
    # 打印评估摘要
    print_comparison_summary(comparison_results, evaluator)
    
    return report


def print_comparison_summary(comparison_results: Dict, evaluator: Evaluator):
    """打印对比实验摘要"""
    print("\n" + "=" * 60)
    print("时间推理Benchmark对比实验报告")
    print("=" * 60)
    
    # 打印各模型总体准确率
    print("\n【各模型总体准确率】")
    print("-" * 50)
    print(f"{'模型名称':<25} {'正确数':<10} {'总题数':<10} {'准确率':<10}")
    print("-" * 50)
    
    for model_key, results in comparison_results.items():
        overall = results["overall"]
        print(f"{model_key:<25} {overall['correct']:<10} {overall['total']:<10} {overall['accuracy']:.1%}")
    
    # 打印各类型详细对比
    print("\n【各题型准确率对比】")
    print("-" * 70)
    
    # 获取所有题型
    all_types = set()
    for results in comparison_results.values():
        all_types.update(results["by_type"].keys())
    
    for qa_type in sorted(all_types):
        print(f"\n{QA_TYPE_DESCRIPTIONS.get(qa_type, qa_type)}:")
        print(f"  {'模型名称':<25} {'正确数':<10} {'总题数':<10} {'准确率':<10}")
        print(f"  {'-'*55}")
        
        for model_key, results in comparison_results.items():
            type_data = results["by_type"].get(qa_type, {"total": 0, "correct": 0, "accuracy": 0})
            print(f"  {model_key:<25} {type_data['correct']:<10} {type_data['total']:<10} {type_data['accuracy']:.1%}")
    
    # 打印质量验证摘要
    print("\n【题目质量验证】")
    evaluator.print_summary()
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("时间情景感知Benchmark生成器（多模型对比版）")
    print("=" * 60)
    
    # 解析命令行参数
    qa_count = QA_COUNT_PER_TYPE
    template_instances = DIALOGUE_TEMPLATE_INSTANCES
    run_comparison = True
    
    if len(sys.argv) > 1:
        try:
            qa_count = int(sys.argv[1])
        except ValueError:
            pass
    
    if len(sys.argv) > 2:
        try:
            template_instances = int(sys.argv[2])
        except ValueError:
            pass
    
    if len(sys.argv) > 3 and sys.argv[3] == "--no-comparison":
        run_comparison = False
    
    print(f"\n配置:")
    print(f"  - 每种QA类型生成数量: {qa_count}")
    print(f"  - 每个模板实例化数量: {template_instances}")
    print(f"  - 运行对比实验: {'是' if run_comparison else '否'}")
    print(f"  - 对比模型: {', '.join(EVAL_MODELS)}")
    
    # 1. 生成QA benchmark
    qa_benchmark = generate_qa_benchmark(qa_count)
    
    # 2. 生成对话 benchmark
    dialogue_benchmark = generate_dialogue_benchmark(template_instances)
    
    # 3. 验证benchmark质量
    evaluator = validate_benchmark(qa_benchmark, dialogue_benchmark)
    
    # 4. 运行对比实验
    comparison_results = None
    if run_comparison:
        comparison_results = run_comparison_experiment(qa_benchmark, EVAL_MODELS)
    
    # 5. 保存结果
    report = save_results(qa_benchmark, dialogue_benchmark, evaluator, comparison_results)
    
    print("\n" + "=" * 60)
    print("Benchmark生成完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
