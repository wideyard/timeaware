"""多事件并发冲突类QA生成器"""

from llm_client import call_llm_json

SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器。你需要生成关于事件并发冲突的推理题目。

核心目标：理解人类在同一物理时间点上"分身乏术"的常识，区分"需要物理独占"和"可异步/代理执行"的事件。

要求：
1. 设定一个不可中断的主任务（如：主持会议、手术、考试等）
2. 在主任务期间发生多个突发安排
3. 需要判断哪个安排可以接受（不影响主任务）
4. 考察对"物理冲突"、"注意力冲突"、"时间窗口冲突"的理解
5. 区分"必须本人执行"和"可委托代理"的任务

输出格式：JSON
{
    "question": "问题文本",
    "main_task": "主任务描述",
    "conflicting_events": [
        {"option": "A/B/C/D", "event": "事件描述", "conflict_type": "冲突类型"}
    ],
    "options": {
        "A": "选项A",
        "B": "选项B",
        "C": "选项C",
        "D": "选项D"
    },
    "answer": "A/B/C/D",
    "explanation": "解释为什么这个选项可以接受",
    "conflict_analysis": "各选项的冲突分析"
}"""


def generate_concurrency_qa(count: int = 15) -> list:
    """生成多事件并发冲突类QA题目"""
    questions = []
    
    prompt = f"""请生成{count}道关于事件并发冲突的推理题目。

核心要求：
1. 设定一个不可中断的主任务场景：
   - 主持重要会议
   - 进行手术
   - 参加考试
   - 驾驶车辆
   - 正在演讲/汇报

2. 在主任务期间，出现4个突发安排：
   - 一个必须物理在场且本人执行（物理冲突）
   - 一个需要高度注意力（注意力冲突）
   - 一个有时间窗口但与主任务冲突（时间冲突）
   - 一个可以委托他人或异步处理（正确答案）

3. 正确答案是"唯一能够接受"的安排
4. 其他选项都有不可调和的冲突

请生成{count}道不同的题目，以JSON数组格式返回：
[{{
    "question": "...",
    "main_task": "...",
    "conflicting_events": [...],
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "A/B/C/D",
    "explanation": "...",
    "conflict_analysis": "..."
}}, ...]"""

    try:
        result = call_llm_json(prompt, SYSTEM_PROMPT)
        if isinstance(result, list):
            for i, q in enumerate(result):
                q["id"] = f"concurrency_{i+1:03d}"
                q["type"] = "concurrency"
            questions = result
    except Exception as e:
        print(f"生成并发冲突QA失败: {e}")
    
    return questions
