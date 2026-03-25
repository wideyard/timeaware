"""完整测试脚本 - 生成所有类型的题目"""

import json
import time
from qa_types.historical_events import generate_historical_events_qa
from qa_types.ordering import generate_ordering_qa
from qa_types.implicit_time import generate_implicit_time_qa
from qa_types.duration import generate_duration_qa
from qa_types.fictional_timeline import generate_fictional_timeline_qa
from qa_types.concurrency import generate_concurrency_qa
from judge import LLMJudge

def generate_and_validate_all():
    """生成并验证所有类型的题目"""
    print("\n" + "=" * 60)
    print("Generating All QA Types")
    print("=" * 60)
    
    all_results = {}
    judge = LLMJudge()
    
    generators = {
        "historical_events": generate_historical_events_qa,
        "ordering": generate_ordering_qa,
        "implicit_time": generate_implicit_time_qa,
        "duration": generate_duration_qa,
        "fictional_timeline": generate_fictional_timeline_qa,
        "concurrency": generate_concurrency_qa,
    }
    
    for qa_type, generator in generators.items():
        print(f"\n--- Generating {qa_type} ---")
        try:
            questions = generator(3)  # 每种类型生成3道
            print(f"Generated {len(questions)} questions")
            
            # 验证
            valid_count = 0
            for q in questions:
                result = judge.validate_qa_question(q)
                q["validation_result"] = result
                q["validation_score"] = result.get("quality_score", 0)
                if result.get("is_valid", False):
                    valid_count += 1
            
            print(f"Valid: {valid_count}/{len(questions)}")
            all_results[qa_type] = questions
            
            time.sleep(3)  # 避免API限流
        except Exception as e:
            print(f"Error generating {qa_type}: {e}")
            all_results[qa_type] = []
    
    return all_results

def save_results(results, output_path):
    """保存结果"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {output_path}")

if __name__ == "__main__":
    results = generate_and_validate_all()
    
    # 保存结果
    output_path = "D:\\workspace\\timeaware\\output\\qa_benchmark_v2.json"
    save_results(results, output_path)
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for qa_type, questions in results.items():
        if questions:
            valid = sum(1 for q in questions if q.get("validation_result", {}).get("is_valid", False))
            avg_score = sum(q.get("validation_score", 0) for q in questions) / len(questions)
            print(f"{qa_type}: {valid}/{len(questions)} valid, avg score: {avg_score:.2f}")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
