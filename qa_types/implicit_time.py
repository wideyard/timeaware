"""隐式时间戳与前提条件推断类QA生成器"""

from llm_client import call_llm_json

SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器。你需要生成关于隐式时间推断的推理题目。

核心目标：不直接告诉模型现在是几月几号，让它通过人物穿着、环境、行为反推时间。

要求：
1. 通过环境线索（天气、植物、节日装饰等）暗示时间
2. 通过人物行为（穿着、活动、饮食等）暗示时间
3. 通过社会事件（考试季、假期、节日等）暗示时间
4. 模型需要先推断出时间，再回答基于该时间的问题
5. 正确答案应该是"最不可能"或"最可能"的选项

输出格式：JSON
{
    "question": "问题文本",
    "options": {
        "A": "选项A",
        "B": "选项B",
        "C": "选项C",
        "D": "选项D"
    },
    "answer": "A/B/C/D",
    "explanation": "解释从线索推断时间的过程",
    "time_clues": ["线索1", "线索2", ...],
    "inferred_time": "推断出的时间范围"
}"""


def generate_implicit_time_qa(count: int = 15) -> list:
    """生成隐式时间推断类QA题目"""
    questions = []
    
    prompt = f"""请生成{count}道关于隐式时间推断的推理题目。

核心要求：
1. 题目不直接告诉当前日期/时间
2. 通过以下线索暗示时间：
   - 天气/季节特征（柳絮、落叶、雪花、高温等）
   - 人物穿着（短袖、羽绒服、校服等）
   - 环境装饰（春联、圣诞树、月饼等）
   - 社会活动（期末考试、暑假、春节等）
3. 问题通常是"最不可能"或"最可能"的选项
4. 模型需要先推断时间，再回答问题

请生成{count}道不同的题目，以JSON数组格式返回：
[{{
    "question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "A/B/C/D",
    "explanation": "...",
    "time_clues": ["...", "..."],
    "inferred_time": "..."
}}, ...]"""

    try:
        result = call_llm_json(prompt, SYSTEM_PROMPT)
        if isinstance(result, list):
            for i, q in enumerate(result):
                q["id"] = f"implicit_{i+1:03d}"
                q["type"] = "implicit_time"
            questions = result
    except Exception as e:
        print(f"生成隐式时间QA失败: {e}")
    
    return questions
