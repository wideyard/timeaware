"""历史事件类QA生成器 - 使用冷门事件或故意反转事实"""

from llm_client import call_llm_json

SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器。你需要生成关于历史事件的时间推理题目。

要求：
1. 使用冷门历史事件，避免过于知名的事件（如林肯解放黑奴、二战结束等）
2. 或者故意使用"反转事实"——给出一个与真实历史相反但符合常识逻辑的假设情景
3. 题目需要考察时间推理能力，而非单纯的记忆背诵
4. 四个选项必须具有迷惑性，但只有一个绝对正确
5. 正确答案必须基于时间逻辑推理，而非知识检索

【重要】选项设计原则：
- 选项只包含纯粹的答案文本，不要添加任何解释
- 例如：A. 1910年 （不要写成 "1910年（正确，基于假设前提）"）
- 选项之间应该是时间维度上的差异

【验证标准】
- 评估的是"时间推理能力"，不是"历史知识准确性"
- 反事实题目的答案应该基于假设前提，而非真实历史

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
    "explanation": "解释为什么这是正确答案，以及各选项的时间错误",
    "is_counterfactual": true/false,
    "historical_context": "相关的历史背景说明"
}"""


def generate_historical_events_qa(count: int = 15) -> list:
    """生成历史事件类QA题目"""
    questions = []
    
    prompt = f"""请生成{count}道关于历史事件的时间推理题目。

要求：
1. 使用冷门历史事件（如地方性历史、特定行业历史、非主流国家历史等）
2. 或者使用"反事实假设"——假设某个历史事件结果不同，推演后续
3. 题目应考察时间先后顺序、因果时间关系、持续时长等

【关键】错误选项设计：
- 错误选项应该是"时间逻辑推理错误"，不是"不符合真实历史"
- 正确答案必须基于题目给出的假设前提
- 确保在假设前提下只有一个正确答案

【示例】
反事实题目示例：
问题："假设明治维新在1850年就开始了，那么日本的现代化进程会在什么时候开始？"
选项：
A. 1850年（正确，基于假设前提）
B. 1868年（错误，这是真实历史时间）
C. 1871年（错误）
D. 1889年（错误）

请生成{count}道不同的题目，以JSON数组格式返回：
[{{
    "question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "A/B/C/D",
    "explanation": "...",
    "is_counterfactual": true/false,
    "historical_context": "..."
}}, ...]"""

    try:
        result = call_llm_json(prompt, SYSTEM_PROMPT)
        if isinstance(result, list):
            for i, q in enumerate(result):
                q["id"] = f"historical_{i+1:03d}"
                q["type"] = "historical_events"
            questions = result
    except Exception as e:
        print(f"生成历史事件QA失败: {e}")
    
    return questions


if __name__ == "__main__":
    # 测试生成
    qs = generate_historical_events_qa(3)
    for q in qs:
        print(f"\n{q['question']}")
        for opt, text in q['options'].items():
            print(f"  {opt}. {text}")
        print(f"答案: {q['answer']}")
        print(f"解释: {q['explanation']}")
