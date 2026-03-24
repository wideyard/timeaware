"""LLM-as-a-Judge 自检模块 - 改进版"""

import json
from typing import Dict, List, Any, Optional
from llm_client import call_llm_json

class LLMJudge:
    """LLM-as-a-Judge 评估器 - 针对不同题型定制验证"""
    
    BASE_VALIDATION_PROMPT = """你是一个严格的题目质量评估专家。请评估以下时间推理题目的质量。

评估标准：
1. 选项互斥性：四个选项是否相互排斥，不会出现两个选项都正确的情况
2. 答案唯一性：正确答案是否唯一且明确
3. 问题清晰性：问题表述是否清晰无歧义
4. 干扰项质量：错误选项是否有足够的迷惑性
5. 时间逻辑：时间推理是否符合逻辑

请给出详细评估。"""
    
    QA_TYPE_SPECIFIC_PROMPTS = {
        "historical_events": """【历史事件类题目特殊要求】
这是反事实/虚构历史题目，评估时请注意：
- 不要用"是否符合真实历史"来评判
- 应该评估"假设逻辑是否自洽"
- 时间推理是否在假设前提下合理
- 正确答案应该是基于"给定假设"的时间逻辑推理

【额外评估标准】
- 假设前提是否明确
- 时间推理是否在假设前提下唯一确定
- 错误选项是否与假设逻辑矛盾""",
        
        "duration": """【时长推理类题目特殊要求】
评估时请注意：
- 需要验证时间计算是否正确
- 物理后果是否符合常识
- 选项之间是否有足够区分度

【额外评估标准】
- 时间累加计算是否正确
- 物理后果描述是否合理
- 正确答案是否基于正确的物理推理""",
        
        "implicit_time": """【隐式时间推断类题目特殊要求】
评估时请注意：
- 场景线索是否足够明确且无歧义
- 推断出的时间是否与线索一致
- 问题答案是否基于推断出的时间

【额外评估标准】
- 时间线索是否清晰（如：秋季不能同时有中秋又举办春季活动）
- 推断逻辑是否合理
- 干扰项是否与推断时间冲突""",
        
        "fictional_timeline": """【虚构时间线类题目特殊要求】
评估时请注意：
- 时间系统规则是否完整清晰
- 表述是否有歧义（如"今天是Pax的第10天"应明确含义）
- 计算逻辑是否正确

【额外评估标准】
- 时间系统规则是否无歧义
- 计算步骤是否正确
- 选项是否能从规则唯一确定""",
        
        "ordering": """【事件排序类题目特殊要求】
评估时请注意：
- 需要检查所有选项是否满足时间约束
- 正确答案是否真的是唯一/最优可行顺序
- 错误选项是否导致时间冲突

【额外评估标准】
- 所有任务的时间约束是否完整提供
- 各选项是否逐一验证时间可行性
- 正确答案是否经过严格的时间线验证
- 错误选项是否有明确的时间冲突

【关键】请务必检查：
1. 当前时间和任务时间约束
2. 每个选项的执行顺序是否满足所有deadline
3. 正确答案是否真的能在截止时间前完成
4. 错误选项是否真的会导致任务失败""",
        
        "concurrency": """【并发冲突类题目特殊要求】
评估时请注意：
- 主任务描述是否明确
- 各选项的冲突类型是否正确分类
- 正确答案是否真的是唯一可接受的选项

【额外评估标准】
- 主任务是否不可中断
- 各选项的冲突分析是否准确
- 是否只有一个选项真正可接受"""
    }
    
    DIALOGUE_VALIDATION_PROMPT = """你是一个严格的对话题目质量评估专家。请评估以下对话题目的质量。

评估标准：
1. 对话自然性：对话是否自然流畅
2. 时间线索清晰性：时间信息是否足够清晰
3. 答案可推理性：正确答案是否可以从对话中推理得出
4. 干扰项质量：错误选项是否有足够的迷惑性

请给出详细评估。"""
    
    def __init__(self):
        pass
    
    def _build_qa_prompt(self, question: Dict) -> str:
        """根据题目类型构建定制化验证prompt"""
        qa_type = question.get('type', 'unknown')
        
        prompt_parts = []
        
        # 基础prompt
        prompt_parts.append(self.BASE_VALIDATION_PROMPT)
        
        # 添加类型特定的prompt
        if qa_type in self.QA_TYPE_SPECIFIC_PROMPTS:
            prompt_parts.append(self.QA_TYPE_SPECIFIC_PROMPTS[qa_type])
        
        # 构建题目信息
        prompt_parts.append(f"\n\n【题目类型】{qa_type}")
        prompt_parts.append(f"【问题】{question.get('question', '')}")
        
        # 根据题目类型添加相关字段
        if qa_type == "ordering" and 'tasks' in question:
            tasks = question.get('tasks', [])
            tasks_str = "\n".join([
                f"- {t.get('name', '')}: 耗时{t.get('duration', '')}, 截止{t.get('deadline', '')}, 地点{t.get('constraint', '')}"
                for t in tasks
            ])
            prompt_parts.append(f"【任务列表】\n{tasks_str}")
            prompt_parts.append(f"【当前时间】{question.get('current_time', '')}")
        
        if qa_type == "fictional_timeline":
            prompt_parts.append(f"【世界名称】{question.get('world_name', '')}")
            prompt_parts.append(f"【时间系统规则】{question.get('time_system_rules', '')}")
            if 'calculation_steps' in question:
                prompt_parts.append(f"【计算步骤】{' -> '.join(question.get('calculation_steps', []))}")
        
        if qa_type == "duration":
            prompt_parts.append(f"【时间计算】{question.get('time_calculation', '')}")
            prompt_parts.append(f"【物理后果】{question.get('physical_consequence', '')}")
        
        if qa_type == "implicit_time":
            clues = question.get('time_clues', [])
            prompt_parts.append(f"【时间线索】{', '.join(clues)}")
            prompt_parts.append(f"【推断时间】{question.get('inferred_time', '')}")
        
        if qa_type == "concurrency":
            prompt_parts.append(f"【主任务】{question.get('main_task', '')}")
            events = question.get('conflicting_events', [])
            events_str = "\n".join([
                f"- {e.get('option', '')}: {e.get('event', '')} ({e.get('conflict_type', '')})"
                for e in events
            ])
            prompt_parts.append(f"【冲突事件】\n{events_str}")
        
        if qa_type == "historical_events":
            prompt_parts.append(f"【是否反事实】{'是' if question.get('is_counterfactual', False) else '否'}")
            prompt_parts.append(f"【历史背景】{question.get('historical_context', '')}")
        
        # 选项和答案
        prompt_parts.append(f"\n【选项】")
        for opt_key in ['A', 'B', 'C', 'D']:
            opt_text = question.get('options', {}).get(opt_key, '')
            prompt_parts.append(f"{opt_key}. {opt_text}")
        
        prompt_parts.append(f"【正确答案】{question.get('answer', '')}")
        prompt_parts.append(f"【解释】{question.get('explanation', '')}")
        
        # 输出格式说明
        prompt_parts.append("""
请以JSON格式返回评估结果：
{
    "is_valid": true/false,
    "mutual_exclusive": true/false,
    "unique_answer": true/false,
    "clear_question": true/false,
    "good_distractors": true/false,
    "logical_time": true/false,
    "quality_score": 0.0-1.0,
    "issues": ["问题1", "问题2", ...],
    "suggestions": ["建议1", "建议2", ...]
}""")
        
        return "\n".join(prompt_parts)
    
    def validate_qa_question(self, question: Dict) -> Dict:
        """验证单个QA题目"""
        prompt = self._build_qa_prompt(question)
        
        try:
            result = call_llm_json(prompt, self.BASE_VALIDATION_PROMPT, temperature=0.3)
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
        
        prompt = f"""你是一个严格的对话题目质量评估专家。请评估以下对话题目的质量。

评估标准：
1. 对话自然性：对话是否自然流畅
2. 时间线索清晰性：时间信息是否足够清晰
3. 答案可推理性：正确答案是否可以从对话中推理得出
4. 干扰项质量：错误选项是否有足够的迷惑性

【重要】时间表达必须明确：
- "后天"、"下周"等相对时间需要有明确的具体日期
- 如果使用相对时间，选项中也应使用相同的相对时间表达

请给出详细评估。

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
