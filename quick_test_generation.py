"""快速测试脚本 - 测试生成和验证流程"""

import json
import time
from qa_types.historical_events import generate_historical_events_qa
from qa_types.ordering import generate_ordering_qa
from qa_types.implicit_time import generate_implicit_time_qa
from judge import LLMJudge

def test_historical_events():
    """测试历史事件生成"""
    print("\n" + "=" * 60)
    print("Testing Historical Events Generation")
    print("=" * 60)
    
    try:
        questions = generate_historical_events_qa(2)
        print(f"\nGenerated {len(questions)} questions")
        
        for q in questions:
            print(f"\n--- {q['id']} ---")
            print(f"Question: {q['question']}")
            print(f"Options: {q['options']}")
            print(f"Answer: {q['answer']}")
            print(f"Counterfactual: {q.get('is_counterfactual', 'N/A')}")
        
        # 验证
        print("\n--- Validation Results ---")
        judge = LLMJudge()
        for q in questions:
            result = judge.validate_qa_question(q)
            print(f"\n{q['id']}:")
            print(f"  is_valid: {result.get('is_valid')}")
            print(f"  quality_score: {result.get('quality_score')}")
            print(f"  issues: {result.get('issues', [])}")
        
        return questions
    except Exception as e:
        print(f"Error: {e}")
        return []

def test_ordering():
    """测试事件排序生成"""
    print("\n" + "=" * 60)
    print("Testing Ordering Generation")
    print("=" * 60)
    
    try:
        questions = generate_ordering_qa(2)
        print(f"\nGenerated {len(questions)} questions")
        
        for q in questions:
            print(f"\n--- {q['id']} ---")
            print(f"Question: {q['question']}")
            print(f"Current time: {q.get('current_time')}")
            print(f"Tasks: {q.get('tasks')}")
            print(f"Options: {q['options']}")
            print(f"Answer: {q['answer']}")
        
        # 验证
        print("\n--- Validation Results ---")
        judge = LLMJudge()
        for q in questions:
            result = judge.validate_qa_question(q)
            print(f"\n{q['id']}:")
            print(f"  is_valid: {result.get('is_valid')}")
            print(f"  quality_score: {result.get('quality_score')}")
            print(f"  issues: {result.get('issues', [])}")
        
        return questions
    except Exception as e:
        print(f"Error: {e}")
        return []

def test_implicit_time():
    """测试隐式时间生成"""
    print("\n" + "=" * 60)
    print("Testing Implicit Time Generation")
    print("=" * 60)
    
    try:
        questions = generate_implicit_time_qa(2)
        print(f"\nGenerated {len(questions)} questions")
        
        for q in questions:
            print(f"\n--- {q['id']} ---")
            print(f"Question: {q['question']}")
            print(f"Time clues: {q.get('time_clues')}")
            print(f"Inferred time: {q.get('inferred_time')}")
            print(f"Options: {q['options']}")
            print(f"Answer: {q['answer']}")
        
        # 验证
        print("\n--- Validation Results ---")
        judge = LLMJudge()
        for q in questions:
            result = judge.validate_qa_question(q)
            print(f"\n{q['id']}:")
            print(f"  is_valid: {result.get('is_valid')}")
            print(f"  quality_score: {result.get('quality_score')}")
            print(f"  issues: {result.get('issues', [])}")
        
        return questions
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    test_historical_events()
    time.sleep(2)
    test_ordering()
    time.sleep(2)
    test_implicit_time()
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
