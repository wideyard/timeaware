"""LLM Model for PTA Benchmark"""

import json
import re
import time
from typing import Dict, Any, Optional, List
from tqdm import tqdm

from .base import BaseModel
from ..data import PTASample
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from llm_client import call_llm, call_llm_json


SYSTEM_PROMPT_EN = """You are a smart assistant determining if a user is available to be interrupted.

You will receive information about an ongoing activity and need to decide the most appropriate action.
"""

SYSTEM_PROMPT_ZH = """你是一个智能助手，需要判断用户当前是否方便被打扰。

你会收到关于一个正在进行中的活动的信息，需要决定最合适的行动。
"""

USER_PROMPT_EN = """Context: {context}
Activity has been ongoing for: {delta_t} minutes
Expected duration for this type of activity: approximately {expected_duration} minutes

Please choose the most appropriate action from the following options:
A) defer - The activity is very likely still in progress, do not interrupt
B) check-in - Unsure about the activity status, proactively confirm
C) interrupt - The activity is very likely finished, can interrupt

Please respond in JSON format with the following structure:
{{"action": "A", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}

Important: Only output the JSON, no other text."""

USER_PROMPT_ZH = """情境：{context}
活动已经进行了：{delta_t} 分钟
这类活动的典型持续时间约为：{expected_duration} 分钟

请从以下选项中选择最合适的行动：
A) defer (推迟) - 活动很可能还在进行，不打扰
B) check-in (询问) - 不确定活动状态，主动确认
C) interrupt (打断) - 活动很可能已经结束，可以打扰

请以JSON格式回复，格式如下：
{{"action": "A", "confidence": 0.0-1.0, "reasoning": "简要解释"}}

重要提示：只输出JSON，不要输出其他文字。"""


class LLMModel(BaseModel):
    """LLM-based model for PTA benchmark"""
    
    ACTION_MAP = {
        "A": "defer",
        "B": "check-in", 
        "C": "interrupt",
        "defer": "defer",
        "check-in": "check-in",
        "interrupt": "interrupt",
        "推迟": "defer",
        "询问": "check-in",
        "打断": "interrupt",
    }
    
    def __init__(
        self,
        model_key: str = "gpt-4o-mini",
        language: str = "en",
        use_expanded: bool = False,
        batch_size: int = 10,
        rate_limit_delay: float = 0.5,
        cache_dir: Optional[str] = None,
    ):
        """
        Initialize LLM model.
        
        Args:
            model_key: Model identifier (gpt-4o-mini, doubao-seed-1-8, doubao-seed-2-0-pro)
            language: Prompt language ('en' or 'zh')
            use_expanded: Whether to use expanded activities
            batch_size: Number of samples to process before showing progress
            rate_limit_delay: Delay between API calls (seconds)
            cache_dir: Directory to cache predictions
        """
        self.model_key = model_key
        self.language = language
        self.batch_size = batch_size
        self.rate_limit_delay = rate_limit_delay
        self.cache_dir = cache_dir
        self.use_expanded = use_expanded
        
        model_display_name = model_key.replace("-", "_")
        lang_display = "zh" if language == "zh" else "en"
        super().__init__(name=f"LLM_{model_display_name}_{lang_display}")
        
        self.system_prompt = SYSTEM_PROMPT_ZH if language == "zh" else SYSTEM_PROMPT_EN
        self.user_prompt_template = USER_PROMPT_ZH if language == "zh" else USER_PROMPT_EN
        
        self._prediction_cache: Dict[int, Dict[str, Any]] = {}
    
    def _build_prompt(self, sample: PTASample) -> str:
        """Build user prompt from sample"""
        return self.user_prompt_template.format(
            context=sample.context,
            delta_t=sample.delta_t,
            expected_duration=sample.expected_duration,
        )
    
    def _parse_response(self, response: str, sample_id: int) -> Dict[str, Any]:
        """Parse LLM response to extract action and confidence"""
        response = response.strip()
        
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                action_str = data.get("action", "B")
                confidence = data.get("confidence", 0.5)
                reasoning = data.get("reasoning", "")
                
                action = self.ACTION_MAP.get(action_str, self.ACTION_MAP.get(action_str.upper(), "check-in"))
                
                return {
                    "action": action,
                    "confidence": float(confidence),
                    "p_active": None,
                    "raw_response": response,
                    "reasoning": reasoning,
                    "sample_id": sample_id,
                }
            except json.JSONDecodeError:
                pass
        
        action_patterns = [
            (r'["\']action["\']\s*:\s*["\']?([ABC])', None),
            (r'action["\']?\s*[:=]\s*["\']?(defer|check-in|interrupt)', "en"),
            (r'行动["\']?\s*[:=]\s*["\']?(推迟|询问|打断)', "zh"),
            (r'置信度["\']?\s*[:=]\s*([0-9.]+)', None),
        ]
        
        for pattern, lang in action_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                action_raw = match.group(1) if match.lastindex else match.group(0)
                
                if action_raw in ["A", "B", "C"]:
                    action = self.ACTION_MAP.get(action_raw, "check-in")
                elif action_raw in ["defer", "check-in", "interrupt"]:
                    action = action_raw
                elif action_raw in ["推迟", "询问", "打断"]:
                    action = self.ACTION_MAP.get(action_raw, "check-in")
                else:
                    action = "check-in"
                
                return {
                    "action": action,
                    "confidence": 0.5,
                    "p_active": None,
                    "raw_response": response,
                    "reasoning": "",
                    "sample_id": sample_id,
                }
        
        return {
            "action": "check-in",
            "confidence": 0.5,
            "p_active": None,
            "raw_response": response,
            "reasoning": "Failed to parse response",
            "sample_id": sample_id,
        }
    
    def predict(self, sample: PTASample) -> Dict[str, Any]:
        """Make a prediction for a single sample"""
        if sample.id in self._prediction_cache:
            return self._prediction_cache[sample.id]
        
        prompt = self._build_prompt(sample)
        
        try:
            response = call_llm(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.3,
                model_key=self.model_key,
            )
            result = self._parse_response(response, sample.id)
        except Exception as e:
            result = {
                "action": "check-in",
                "confidence": 0.0,
                "p_active": None,
                "error": str(e),
                "sample_id": sample.id,
            }
        
        self._prediction_cache[sample.id] = result
        
        time.sleep(self.rate_limit_delay)
        
        return result
    
    def predict_batch(
        self, 
        samples: List[PTASample],
        show_progress: bool = True,
    ) -> List[Dict[str, Any]]:
        """Make predictions for a batch of samples"""
        predictions = []
        
        iterator = tqdm(samples, desc=f"Evaluating {self.name}") if show_progress else samples
        
        for sample in iterator:
            pred = self.predict(sample)
            predictions.append(pred)
        
        return predictions
    
    def clear_cache(self):
        """Clear prediction cache"""
        self._prediction_cache.clear()


def create_llm_model(
    model_key: str = "gpt-4o-mini",
    language: str = "en",
    **kwargs,
) -> LLMModel:
    """Factory function to create LLM model"""
    return LLMModel(
        model_key=model_key,
        language=language,
        **kwargs,
    )
