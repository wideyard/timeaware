"""LLM-as-a-Judge 自检模块"""

import json
from typing import Dict, List, Any, Optional
from llm_client import call_llm_json

class LLMJudge:
    """LLM-as-a-Judge 评估器"""
    
    QA_VALIDATION_PROMPT = """你是一个严格的题目质量评估专家。请评估以下时间推理题目的质量。

评估标准：
1. 选项互斥性：四个选项是否相互排斥，不会出现两个选项都正确的情况
2. 答案唯一性：正确答案是否唯一且明确
3. 问题清晰性：问题表述是否清晰无歧义
4. 干扰项质量：错误选项是否有足够的迷惑性
5. 时间逻辑：时间推理是否符合常识逻辑

请给出详细评估。"""
    
    DIALOGUE_VALIDATION_PROMPT = """你是一个严格的对话题目质量评估专家。请评估以下对话题目的质量。

评估标准：
1. 对话自然性：对话是否自然流畅
2. 时间线索清晰性：时间信息是否足够清晰
3. 答案可推理性：正确答案是否可以从对话中推理得出
4. 干扰项质量：错误选项是否有足够的迷惑性

请给出详细评估。"""
    
    def __init__(self):
        pass
    
    def validate_qa_question(self, question: Dict) -> Dict:
        """验证单个QA题目"""
        prompt = f"""请评估以下时间推理题目的质量：

【题目类型】{question.get('type', 'unknown')}
【问题】{question.get('question', '')}
【选项】
A. {question.get('options', {}).get('A', '')}
B. {question.get('options', {}).get('B', '')}
C. {question.get('options', {}).get('C', '')}
D. {question.get('options', {}).get('D', '')}
【正确答案】{question.get('answer', '')}
【解释】{question.get('explanation', '')}

请以JSON格式返回评估结果：
{{
    "is_valid": true/false,
    "mutual_exclusive": true/false,
    "unique_answer": true/false,
    "clear_question": true/false,
    "good_distractors": true/false,
    "logical_time": true/false,
    "quality_score": 0.0-1.0,
    "issues": ["问题1", "问题2", ...],
    "suggestions": ["建议1", "建议2", ...]
}}"""
        
        try:
            result = call_llm_json(prompt, self.QA_VALIDATION_PROMPT, temperature=0.3)
            result["question_id"] = question.get("id", "unknown")
            return result
        except Exception as e:
            return {
                "question_id": question.get("id", "unknown"),
                "is_valid": False,
                "error": str(e),
                "quality_score": 0.0
            }
    
    def validate_dialogue_question(self, question: Dict) -> Dict:
        """验证对话题目"""
        transcript = question.get("transcript", [])
        transcript_str = "\n".join([f"{t['role']}: {t['content']}" for t in transcript])
        
        prompt = f"""请评估以下对话题目的质量：

【对话记录】
{transcript_str}

【探针问题】{question.get('probe_question', '')}
【选项】
A. {question.get('options', {}).get('A', '')}
B. {question.get('options', {}).get('B', '')}
C. {question.get('options', {}).get('C', '')}
D. {question.get('options', {}).get('D', '')}
【正确答案】{question.get('answer', '')}
【解释】{question.get('explanation', '')}

请以JSON格式返回评估结果：
{{
    "is_valid": true/false,
    "natural_dialogue": true/false,
    "clear_time_clues": true/false,
    "deducible_answer": true/false,
    "good_distractors": true/false,
    "quality_score": 0.0-1.0,
    "issues": ["问题1", "问题2", ...],
    "suggestions": ["建议1", "建议2", ...]
}}"""
        
        try:
            result = call_llm_json(prompt, self.DIALOGUE_VALIDATION_PROMPT, temperature=0.3)
            result["question_id"] = question.get("id", "unknown")
            return result
        except Exception as e:
            return {
                "question_id": question.get("id", "unknown"),
                "is_valid": False,
                "error": str(e),
                "quality_score": 0.0
            }
    
    def validate_batch(self, questions: List[Dict], question_type: str = "qa") -> List[Dict]:
        """批量验证题目"""
        results = []
        for question in questions:
            if question_type == "qa":
                result = self.validate_qa_question(question)
            else:
                result = self.validate_dialogue_question(question)
            results.append(result)
        return results
    
    def filter_valid_questions(self, questions: List[Dict], validation_results: List[Dict], 
                               min_score: float = 0.6) -> List[Dict]:
        """根据验证结果过滤有效题目"""
        valid_questions = []
        for question, validation in zip(questions, validation_results):
            if validation.get("is_valid", False) and validation.get("quality_score", 0) >= min_score:
                question["validation_score"] = validation.get("quality_score", 0)
                question["validation_result"] = validation
                valid_questions.append(question)
        return valid_questions
