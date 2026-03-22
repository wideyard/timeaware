"""虚拟时间线类QA生成器 - 防止数据污染"""

from llm_client import call_llm_json

SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器。你需要生成基于虚构世界时间系统的推理题目。

核心目标：使用完全虚构的时间系统，防止模型通过记忆作弊。

要求：
1. 创造一个虚构的世界/星球，有独特的时间系统
2. 时间系统应包含非标准元素（如不同天数的周、不同的月份规则等）
3. 题目需要在这个虚构系统内进行时间推理
4. 答案必须基于题目给出的规则计算得出
5. 避免与现实时间系统混淆

输出格式：JSON
{
    "question": "问题文本（包含虚构时间系统规则）",
    "world_name": "虚构世界名称",
    "time_system_rules": "时间系统规则说明",
    "options": {
        "A": "选项A",
        "B": "选项B",
        "C": "选项C",
        "D": "选项D"
    },
    "answer": "A/B/C/D",
    "explanation": "详细的计算过程",
    "calculation_steps": ["步骤1", "步骤2", ...]
}"""


def generate_fictional_timeline_qa(count: int = 15) -> list:
    """生成虚拟时间线类QA题目"""
    questions = []
    
    prompt = f"""请生成{count}道基于虚构世界时间系统的推理题目。

核心要求：
1. 创造独特的虚构时间系统，例如：
   - 一周只有5天（无周末）
   - 一个月有不同天数（如20天、25天等）
   - 有独特的周期（如每3天一个节日）
   - 时间单位不同（如"一响"=2小时）

2. 题目类型：
   - 计算某个事件发生在星期几
   - 计算两个事件之间的间隔
   - 判断周期性事件的重叠

3. 必须在题目中明确给出时间系统的所有规则
4. 答案必须是唯一可计算的

请生成{count}道不同的题目，以JSON数组格式返回：
[{{
    "question": "...",
    "world_name": "...",
    "time_system_rules": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "A/B/C/D",
    "explanation": "...",
    "calculation_steps": ["...", "..."]
}}, ...]"""

    try:
        result = call_llm_json(prompt, SYSTEM_PROMPT)
        if isinstance(result, list):
            for i, q in enumerate(result):
                q["id"] = f"fictional_{i+1:03d}"
                q["type"] = "fictional_timeline"
            questions = result
    except Exception as e:
        print(f"生成虚拟时间线QA失败: {e}")
    
    return questions
