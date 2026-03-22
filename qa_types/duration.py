"""日常活动持续时间类QA生成器"""

from llm_client import call_llm_json

SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器。你需要生成关于日常活动持续时间的推理题目。

核心目标：测试模型对时间流逝的物理感知能力，而非简单的数字计算。

要求：
1. 题目必须结合现实世界的物理规律
2. 需要推算事件耗时，并理解时间累积造成的物理后果
3. 场景应贴近日常生活（做饭、通勤、运动等）
4. 四个选项中必须有一个是基于正确时间推理的答案
5. 错误选项应该是对时间流逝或物理后果的误解

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
    "explanation": "解释时间推理过程和物理后果",
    "time_calculation": "具体的时间计算过程",
    "physical_consequence": "时间累积造成的物理后果说明"
}"""


def generate_duration_qa(count: int = 15) -> list:
    """生成日常活动持续时间类QA题目"""
    questions = []
    
    prompt = f"""请生成{count}道关于日常活动持续时间的推理题目。

核心要求：
1. 题目场景必须涉及物理世界的时间累积效应
2. 需要推算多个活动的总耗时
3. 必须理解时间流逝对物理世界的影响（如食物烹饪、冰融化、水蒸发等）
4. 场景示例：
   - 煮饺子/面条离开一段时间后的状态
   - 冰淇淋放在桌上一段时间后的状态
   - 衣服晾晒在不同天气下的干燥速度
   - 长时间运动后的身体状态

请生成{count}道不同的题目，以JSON数组格式返回：
[{{
    "question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "A/B/C/D",
    "explanation": "...",
    "time_calculation": "...",
    "physical_consequence": "..."
}}, ...]"""

    try:
        result = call_llm_json(prompt, SYSTEM_PROMPT)
        if isinstance(result, list):
            for i, q in enumerate(result):
                q["id"] = f"duration_{i+1:03d}"
                q["type"] = "duration"
            questions = result
    except Exception as e:
        print(f"生成持续时间QA失败: {e}")
    
    return questions
