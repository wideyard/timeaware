"""剧本截断+探针多选题生成器"""

import json
import random
from typing import Dict, List, Any, Optional
from llm_client import call_llm_json

class TranscriptProber:
    """剧本截断+探针生成器"""
    
    SYSTEM_PROMPT = """你是一个时间推理benchmark数据集的生成器。你需要基于对话记录生成时间推理探针题目。

核心目标：给定一段包含时间信息的对话，在对话末尾抛出一个时间推理选择题。

要求：
1. 对话必须包含隐式时间线索（如"明天"、"下周"、"三天后"等）
2. 对话中需要有干扰性的时间信息
3. 探针问题需要推断对话中提到的某个事件的具体时间
4. 正确答案必须基于对话中的时间逻辑
5. 错误选项应该是对时间的误解

输出格式：JSON
{
    "transcript": [
        {"role": "speaker1", "content": "对话内容"},
        {"role": "speaker2", "content": "对话内容"}
    ],
    "probe_question": "探针问题",
    "options": {
        "A": "选项A",
        "B": "选项B",
        "C": "选项C",
        "D": "选项D"
    },
    "answer": "A/B/C/D",
    "explanation": "解释答案的推理过程",
    "time_reasoning_chain": ["推理步骤1", "推理步骤2", ...],
    "current_day_hint": "对话中暗示的当前日期"
}"""
    
    def __init__(self):
        pass
    
    def generate_transcript_probes(self, count: int = 15) -> List[Dict]:
        """生成剧本截断+探针题目"""
        prompt = f"""请生成{count}道基于对话记录的时间推理探针题目。

核心要求：
1. 对话场景多样化：
   - 工作安排（会议、项目截止日期）
   - 生活场景（约会、旅行计划）
   - 社交场景（聚会、活动安排）

2. 对话必须包含：
   - 至少2-3个时间相关的信息
   - 一些干扰性的时间线索
   - 隐式的时间推断需求

3. 探针问题类型：
   - "根据对话，X事件将在哪一天举行？"
   - "对话中提到的deadline是什么时候？"
   - "如果按照对话安排，下一个事件是什么时候？"

4. 确保答案唯一且可从对话中推理得出

请生成{count}道不同的题目，以JSON数组格式返回：
[{{
    "transcript": [...],
    "probe_question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "A/B/C/D",
    "explanation": "...",
    "time_reasoning_chain": ["...", "..."],
    "current_day_hint": "..."
}}, ...]"""
        
        try:
            result = call_llm_json(prompt, self.SYSTEM_PROMPT)
            if isinstance(result, list):
                for i, q in enumerate(result):
                    q["id"] = f"transcript_probe_{i+1:03d}"
                    q["type"] = "transcript_probe"
                return result
        except Exception as e:
            print(f"生成剧本截断探针失败: {e}")
        
        return []
    
    def generate_from_template(self, template_instance: Dict) -> Optional[Dict]:
        """从模板实例生成探针题目"""
        dialogue = template_instance.get("dialogue", [])
        expected_state = template_instance.get("expected_final_state", {})
        
        if not dialogue or not expected_state:
            return None
        
        # 构建对话记录
        transcript = []
        for turn in dialogue:
            transcript.append({
                "role": "user" if turn["role"] == "user" else "assistant",
                "content": turn["content"]
            })
        
        # 生成探针问题
        meeting_start = expected_state.get("meeting_start", "")
        meeting_end = expected_state.get("meeting_end", "")
        
        if not meeting_start:
            return None
        
        probe_question = f"根据上述对话，会议将在什么时间结束？"
        
        # 生成选项
        options = self._generate_options(meeting_end, expected_state)
        if not options:
            return None
        
        return {
            "id": f"probe_{template_instance.get('id', 'unknown')}",
            "type": "transcript_probe",
            "transcript": transcript,
            "probe_question": probe_question,
            "options": options["options"],
            "answer": options["answer"],
            "explanation": options["explanation"],
            "time_reasoning_chain": [f"会议开始时间: {meeting_start}", f"会议结束时间: {meeting_end}"],
            "current_day_hint": template_instance.get("variables", {}).get("meeting_day_desc", "")
        }
    
    def _generate_options(self, correct_time: str, state: Dict) -> Optional[Dict]:
        """生成选项"""
        if not correct_time:
            return None
        
        options = {"A": correct_time}
        
        # 生成干扰项
        try:
            # 从正确答案中提取信息
            parts = correct_time.split()
            if len(parts) >= 2:
                day_name = parts[0]
                time_part = parts[1]
                
                # 干扰项1: 错误的日期
                weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                current_idx = weekdays.index(day_name) if day_name in weekdays else 0
                wrong_day = weekdays[(current_idx + 1) % 7]
                options["B"] = f"{wrong_day} {time_part}"
                
                # 干扰项2: 错误的时间
                hour, minute = time_part.split(":")
                wrong_hour = (int(hour) + 1) % 24
                options["C"] = f"{day_name} {wrong_hour:02d}:{minute}"
                
                # 干扰项3: 完全错误
                options["D"] = f"{wrong_day} {wrong_hour:02d}:{minute}"
        except:
            # 如果解析失败，使用简单干扰项
            options["B"] = "下周一 15:30"
            options["C"] = "周三 14:00"
            options["D"] = "周五 16:30"
        
        return {
            "options": options,
            "answer": "A",
            "explanation": f"根据对话记录，正确时间是{correct_time}"
        }
