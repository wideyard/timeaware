"""快速测试对比实验"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
from qa_types import QA_GENERATORS, QA_TYPE_DESCRIPTIONS
from config import EVAL_MODELS
from llm_client import call_llm

def quick_test():
    """快速测试对比实验"""
    print("=" * 60)
    print("快速测试对比实验")
    print("=" * 60)
    
    # 只生成2种类型，每类2道题
    test_types = ["duration", "fictional_timeline"]
    qa_benchmark = {}
    
    for qa_type in test_types:
        print(f"\n生成 {QA_TYPE_DESCRIPTIONS[qa_type]}...")
        generator = QA_GENERATORS[qa_type]
        questions = generator(2)
        qa_benchmark[qa_type] = questions
        print(f"  生成 {len(questions)} 道题目")
    
    # 对比实验
    print("\n" + "=" * 60)
    print("运行对比实验")
    print("=" * 60)
    
    results = {}
    
    for model_key in EVAL_MODELS:
        print(f"\n评测模型: {model_key}")
        model_results = {"correct": 0, "total": 0, "details": []}
        
        for qa_type, questions in qa_benchmark.items():
            for q in questions:
                options_text = "\n".join([f"{k}. {v}" for k, v in q.get("options", {}).items()])
                prompt = f"""请回答以下时间推理问题，只返回选项字母（A/B/C/D）。

【问题】{q.get('question', '')}

【选项】
{options_text}

请直接返回答案字母，不要解释。"""
                
                try:
                    response = call_llm(prompt, temperature=0.3, model_key=model_key)
                    answer = response.strip().upper()
                    predicted = answer[0] if answer and answer[0] in ['A', 'B', 'C', 'D'] else 'X'
                    is_correct = predicted == q.get("answer", "")
                    
                    model_results["details"].append({
                        "question_id": q.get("id"),
                        "correct": q.get("answer"),
                        "predicted": predicted,
                        "is_correct": is_correct
                    })
                    
                    if is_correct:
                        model_results["correct"] += 1
                    model_results["total"] += 1
                    
                    status = "✓" if is_correct else "✗"
                    print(f"  {status} {q.get('id')}: 正确={q.get('answer')}, 预测={predicted}")
                    
                except Exception as e:
                    print(f"  ✗ {q.get('id')}: 错误 - {e}")
                    model_results["total"] += 1
        
        results[model_key] = model_results
        accuracy = model_results["correct"] / model_results["total"] if model_results["total"] > 0 else 0
        print(f"  准确率: {model_results['correct']}/{model_results['total']} = {accuracy:.1%}")
    
    # 打印对比结果
    print("\n" + "=" * 60)
    print("对比结果")
    print("=" * 60)
    print(f"\n{'模型':<25} {'正确':<10} {'总数':<10} {'准确率':<10}")
    print("-" * 55)
    for model_key, res in results.items():
        accuracy = res["correct"] / res["total"] if res["total"] > 0 else 0
        print(f"{model_key:<25} {res['correct']:<10} {res['total']:<10} {accuracy:.1%}")
    
    # 保存结果
    with open("output/quick_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n结果已保存到: output/quick_test_results.json")

if __name__ == "__main__":
    quick_test()
