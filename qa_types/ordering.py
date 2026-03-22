"""事件先后顺序类QA生成器"""

from llm_client import call_llm_json

SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器。你需要生成关于事件排序的推理题目。

核心目标：给定多个具有不同耗时、不同时间窗口限制的事件，考察模型的拓扑排序与规划能力。

要求：
1. 包含多个需要完成的任务
2. 每个任务有：耗时、时间窗口限制、地点
3. 需要考虑任务之间的路程时间
4. 正确答案是最优或唯一可行的执行顺序
5. 错误选项会导致时间冲突或任务失败

输出格式：JSON
{
    "question": "问题文本",
    "tasks": [
        {"name": "任务名", "duration": "耗时", "deadline": "截止时间", "constraint": "其他约束"}
    ],
    "current_time": "当前时间",
    "options": {
        "A": "顺序A",
        "B": "顺序B",
        "C": "顺序C",
        "D": "顺序D"
    },
    "answer": "A/B/C/D",
    "explanation": "为什么这个顺序可行，其他顺序为什么失败",
    "timeline": "最优顺序的时间线"
}"""


def generate_ordering_qa(count: int = 15) -> list:
    """生成事件先后顺序类QA题目"""
    questions = []
    
    prompt = f"""请生成{count}道关于事件排序的推理题目。

核心要求：
1. 场景：某人需要在限定时间内完成多个任务
2. 每个任务包含：
   - 任务名称（如：去银行、取快递、开会等）
   - 所需时间（如：30分钟、1小时等）
   - 时间窗口（如：下午4点前、仅2-3点有空等）
   - 地点（如：市中心、公司附近等）

3. 需要考虑：
   - 任务之间的路程时间
   - 任务的时间窗口限制
   - 当前时间

4. 正确答案是唯一或最优可行顺序
5. 错误选项会导致至少一个任务无法完成

请生成{count}道不同的题目，以JSON数组格式返回：
[{{
    "question": "...",
    "tasks": [...],
    "current_time": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "A/B/C/D",
    "explanation": "...",
    "timeline": "..."
}}, ...]"""

    try:
        result = call_llm_json(prompt, SYSTEM_PROMPT)
        if isinstance(result, list):
            for i, q in enumerate(result):
                q["id"] = f"ordering_{i+1:03d}"
                q["type"] = "ordering"
            questions = result
    except Exception as e:
        print(f"生成事件排序QA失败: {e}")
    
    return questions
