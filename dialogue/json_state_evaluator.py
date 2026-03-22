"""JSON状态输出评估器"""

import json
import re
from typing import Dict, List, Any, Optional
from llm_client import call_llm, call_llm_json

class JSONStateEvaluator:
    """JSON状态输出评估器"""
    
    SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器。你需要生成要求LLM输出JSON状态的对话评估题目。

核心目标：测试LLM在多轮对话中维护和更新时间状态的能力。

要求：
1. 设计多轮对话场景
2. 每一轮都要求LLM输出结构化的JSON状态
3. JSON状态需要包含时间相关信息
4. 验证JSON的准确性和一致性

输出格式：JSON
{
    "dialogue_script": [
        {
            "turn": 1,
            "user_input": "用户消息",
            "expected_state": {"key": "value", ...},
            "state_description": "状态说明"
        }
    ],
    "evaluation_criteria": {
        "required_keys": ["key1", "key2"],
        "exact_match_keys": ["key1"],
        "semantic_match_keys": ["key2"]
    },
    "difficulty": "easy/medium/hard"
}"""
    
    def __init__(self):
        pass
    
    def generate_state_evaluations(self, count: int = 10) -> List[Dict]:
        """生成JSON状态评估题目"""
        prompt = f"""请生成{count}道JSON状态输出评估题目。

核心要求：
1. 场景类型：
   - 会议安排和修改
   - 日程冲突解决
   - 多事件时间规划

2. 每道题目包含3-5轮对话
3. 每轮都需要LLM输出JSON状态
4. JSON状态应包含：
   - 时间信息（开始时间、结束时间）
   - 状态标记（是否解决冲突、是否确认等）
   - 相关事件信息

5. 难度梯度：
   - 简单：单一事件的时间调整
   - 中等：多个事件的时间协调
   - 困难：复杂冲突解决和状态追踪

请生成{count}道不同的题目，以JSON数组格式返回：
[{{
    "dialogue_script": [...],
    "evaluation_criteria": {{...}},
    "difficulty": "easy/medium/hard"
}}, ...]"""
        
        try:
            result = call_llm_json(prompt, self.SYSTEM_PROMPT)
            if isinstance(result, list):
                for i, q in enumerate(result):
                    q["id"] = f"state_eval_{i+1:03d}"
                    q["type"] = "json_state_evaluation"
                return result
        except Exception as e:
            print(f"生成JSON状态评估失败: {e}")
        
        return []
    
    def generate_from_template(self, template_instance: Dict) -> Optional[Dict]:
        """从模板实例生成状态评估题目"""
        dialogue = template_instance.get("dialogue", [])
        expected_state = template_instance.get("expected_final_state", {})
        
        if not dialogue:
            return None
        
        # 构建对话脚本
        dialogue_script = []
        for i, turn in enumerate(dialogue):
            if turn["role"] == "user":
                # 找到对应的assistant回复
                assistant_turn = None
                for j in range(i + 1, len(dialogue)):
                    if dialogue[j]["role"] == "assistant":
                        assistant_turn = dialogue[j]
                        break
                
                script_turn = {
                    "turn": len(dialogue_script) + 1,
                    "user_input": turn["content"],
                    "expected_state": assistant_turn.get("hidden_state", {}) if assistant_turn else {},
                    "state_description": f"第{len(dialogue_script) + 1}轮对话后的状态"
                }
                dialogue_script.append(script_turn)
        
        if not dialogue_script:
            return None
        
        # 确定评估标准
        required_keys = list(expected_state.keys())
        
        return {
            "id": f"state_{template_instance.get('id', 'unknown')}",
            "type": "json_state_evaluation",
            "dialogue_script": dialogue_script,
            "evaluation_criteria": {
                "required_keys": required_keys,
                "exact_match_keys": required_keys,
                "semantic_match_keys": []
            },
            "difficulty": "medium",
            "expected_final_state": expected_state
        }
    
    def evaluate_llm_response(self, expected_state: Dict, actual_response: str) -> Dict:
        """评估LLM的JSON状态输出"""
        # 尝试从响应中提取JSON
        json_match = re.search(r'\{[^{}]*\}', actual_response)
        if not json_match:
            return {
                "valid_json": False,
                "match_score": 0.0,
                "errors": ["无法从响应中提取有效的JSON"]
            }
        
        try:
            actual_state = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            return {
                "valid_json": False,
                "match_score": 0.0,
                "errors": [f"JSON解析失败: {str(e)}"]
            }
        
        # 计算匹配分数
        total_keys = len(expected_state)
        if total_keys == 0:
            return {
                "valid_json": True,
                "match_score": 1.0,
                "errors": []
            }
        
        matched_keys = 0
        errors = []
        
        for key, expected_value in expected_state.items():
            if key not in actual_state:
                errors.append(f"缺少必需的键: {key}")
            elif actual_state[key] == expected_value:
                matched_keys += 1
            else:
                errors.append(f"键 {key} 的值不匹配: 期望 {expected_value}, 实际 {actual_state[key]}")
        
        match_score = matched_keys / total_keys
        
        return {
            "valid_json": True,
            "match_score": match_score,
            "matched_keys": matched_keys,
            "total_keys": total_keys,
            "errors": errors
        }
