"""对话模板引擎 - 支持动态实例化模板"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dialogue.templates import ALL_TEMPLATES

class DialogueTemplateEngine:
    """对话模板引擎"""
    
    def __init__(self):
        self.templates = ALL_TEMPLATES
    
    def get_weekday_name(self, date: datetime) -> str:
        """获取中文星期名称"""
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return weekdays[date.weekday()]
    
    def get_relative_day_desc(self, current_date: datetime, target_date: datetime) -> str:
        """获取相对日期描述"""
        diff = (target_date - current_date).days
        if diff == 0:
            return "今天"
        elif diff == 1:
            return "明天"
        elif diff == 2:
            return "后天"
        elif diff == -1:
            return "昨天"
        elif diff == -2:
            return "前天"
        elif 0 < diff <= 7:
            weekday = self.get_weekday_name(target_date)
            return f"这周{weekday}"
        else:
            return f"{target_date.month}月{target_date.day}日"
    
    def resolve_variables(self, template: Dict) -> Dict[str, Any]:
        """解析模板变量"""
        variables = {}
        current_date = datetime.now()
        # 保存当前日期字符串，用于JSON序列化
        variables["current_date"] = current_date.strftime("%Y-%m-%d")
        
        # 解析所有变量
        for key, value_func in template.get("variables", {}).items():
            if callable(value_func):
                variables[key] = value_func()
            else:
                variables[key] = value_func
        
        # 计算派生变量
        meeting_day_offset = variables.get("meeting_day_offset", 3)
        meeting_date = current_date + timedelta(days=meeting_day_offset)
        
        variables["meeting_date"] = meeting_date.strftime("%Y-%m-%d")
        variables["meeting_day_name"] = self.get_weekday_name(meeting_date)
        variables["meeting_day_desc"] = self.get_relative_day_desc(current_date, meeting_date)
        
        # 处理小时
        if "meeting_hour" in variables:
            variables["meeting_hour_padded"] = f"{variables['meeting_hour']:02d}"
        if "original_hour" in variables:
            variables["original_hour_padded"] = f"{variables['original_hour']:02d}"
        
        # 处理持续时间
        if "meeting_duration_minutes" in variables:
            duration = variables["meeting_duration_minutes"]
            if duration == 60:
                variables["meeting_duration_desc"] = "1小时"
            elif duration == 90:
                variables["meeting_duration_desc"] = "1个半小时"
            elif duration == 120:
                variables["meeting_duration_desc"] = "2小时"
            else:
                variables["meeting_duration_desc"] = f"{duration}分钟"
            
            # 计算结束时间
            if "meeting_hour" in variables:
                end_hour = variables["meeting_hour"] + duration // 60
                end_minute = duration % 60
                variables["meeting_end_time"] = f"{variables['meeting_day_name']} {end_hour:02d}:{end_minute:02d}"
        
        if "original_duration" in variables:
            duration = variables["original_duration"]
            if duration == 60:
                variables["original_duration_desc"] = "1小时"
            elif duration == 90:
                variables["original_duration_desc"] = "1个半小时"
            elif duration == 120:
                variables["original_duration_desc"] = "2小时"
            else:
                variables["original_duration_desc"] = f"{duration}分钟"
            
            if "meeting_hour" in variables:
                end_hour = variables["meeting_hour"] + duration // 60
                end_minute = duration % 60
                variables["original_end_time"] = f"{variables['meeting_day_name']} {end_hour:02d}:{end_minute:02d}"
        
        if "new_duration" in variables:
            duration = variables["new_duration"]
            if duration == 30:
                variables["new_duration_desc"] = "30分钟"
            elif duration == 45:
                variables["new_duration_desc"] = "45分钟"
            elif duration == 60:
                variables["new_duration_desc"] = "1小时"
            else:
                variables["new_duration_desc"] = f"{duration}分钟"
            
            if "meeting_hour" in variables:
                end_hour = variables["meeting_hour"] + duration // 60
                end_minute = duration % 60
                variables["new_end_time"] = f"{variables['meeting_day_name']} {end_hour:02d}:{end_minute:02d}"
        
        if "duration" in variables:
            duration = variables["duration"]
            if duration == 60:
                variables["duration_desc"] = "1小时"
            elif duration == 90:
                variables["duration_desc"] = "1个半小时"
            else:
                variables["duration_desc"] = f"{duration}分钟"
            
            if "meeting_hour" in variables:
                end_hour = variables["meeting_hour"] + duration // 60
                end_minute = duration % 60
                variables["end_time"] = f"{variables['meeting_day_name']} {end_hour:02d}:{end_minute:02d}"
        
        # 处理提前/延后
        if "hours_to_earlier" in variables:
            new_hour = variables.get("original_hour", variables.get("meeting_hour", 14)) - variables["hours_to_earlier"]
            variables["new_hour"] = new_hour
            variables["new_hour_padded"] = f"{new_hour:02d}"
            end_hour = new_hour + 1  # 假设1.5小时会议
            variables["new_end_time"] = f"{variables['meeting_day_name']} {end_hour}:30"
        
        if "first_change_hours" in variables:
            hours = variables["first_change_hours"]
            if hours < 0:
                variables["first_change_desc"] = f"{abs(hours)}个小时"
            else:
                variables["first_change_desc"] = f"{hours}个小时"
            first_hour = variables.get("original_hour", 14) + hours
            variables["first_hour"] = first_hour
            variables["first_hour_padded"] = f"{first_hour:02d}"
            end_hour = first_hour + 1
            variables["first_end_time"] = f"{variables['meeting_day_name']} {end_hour}:30"
        
        if "second_change_desc" in variables:
            desc = variables["second_change_desc"]
            if "前" in desc:
                final_date = meeting_date - timedelta(days=1)
            else:
                final_date = meeting_date + timedelta(days=1)
            variables["final_day_name"] = self.get_weekday_name(final_date)
            variables["final_hour"] = variables.get("first_hour", variables.get("original_hour", 14))
            variables["final_hour_padded"] = f"{variables['final_hour']:02d}"
            end_hour = variables["final_hour"] + 1
            variables["final_end_time"] = f"{variables['final_day_name']} {end_hour}:30"
        
        # 处理换天
        if "new_day_offset" in variables:
            new_date = meeting_date + timedelta(days=variables["new_day_offset"])
            variables["new_day_name"] = self.get_weekday_name(new_date)
            variables["new_day_desc"] = self.get_relative_day_desc(current_date, new_date)
            if "meeting_hour" in variables:
                end_hour = variables["meeting_hour"] + 1
                variables["new_end_time"] = f"{variables['new_day_name']} {end_hour}:00"
                variables["original_end_time"] = f"{variables['meeting_day_name']} {end_hour}:00"
        
        # 处理冲突时间
        if "conflict_hour" in variables:
            new_hour = variables["conflict_hour"] - 2  # 提前到冲突前
            variables["new_hour"] = new_hour
            variables["new_hour_padded"] = f"{new_hour:02d}"
            end_hour = new_hour + 2
            variables["new_end_time"] = f"{variables['meeting_day_name']} {end_hour:00}"
        
        # 处理下周
        if "meeting_weekday" in variables:
            variables["meeting_weekday"] = variables["meeting_day_name"]
        
        # 处理结束时间
        if "end_time_only" not in variables:
            if "meeting_hour" in variables:
                duration = variables.get("duration", variables.get("meeting_duration_minutes", 60))
                end_hour = variables["meeting_hour"] + duration // 60
                end_minute = duration % 60
                variables["end_time_only"] = f"{end_hour:02d}:{end_minute:02d}"
        
        return variables
    
    def substitute_template(self, template_str: str, variables: Dict[str, Any]) -> str:
        """替换模板中的变量"""
        result = template_str
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        return result
    
    def instantiate_template(self, template_id: str) -> Optional[Dict]:
        """实例化一个模板"""
        template = self.templates.get(template_id)
        if not template:
            return None
        
        # 解析变量
        variables = self.resolve_variables(template)
        
        # 生成对话
        dialogue = []
        for turn in template["dialogue_template"]:
            new_turn = {
                "role": turn["role"],
                "content": self.substitute_template(turn["content"], variables)
            }
            if "hidden_state" in turn:
                # 深度复制并替换状态中的变量
                state = {}
                for key, value in turn["hidden_state"].items():
                    if isinstance(value, str):
                        state[key] = self.substitute_template(value, variables)
                    elif isinstance(value, list):
                        state[key] = [self.substitute_template(item, variables) if isinstance(item, str) else item for item in value]
                    else:
                        state[key] = value
                new_turn["hidden_state"] = state
            dialogue.append(new_turn)
        
        # 生成最终状态
        final_state = {}
        for key, value in template["state_template"].items():
            if isinstance(value, str):
                final_state[key] = self.substitute_template(value, variables)
            elif isinstance(value, list):
                final_state[key] = [self.substitute_template(item, variables) if isinstance(item, str) else item for item in value]
            else:
                final_state[key] = value
        
        return {
            "id": template_id,
            "type": template["type"],
            "name": template["name"],
            "description": template["description"],
            "variables": {k: v for k, v in variables.items() if not callable(v)},
            "dialogue": dialogue,
            "expected_final_state": final_state
        }
    
    def generate_instances(self, template_id: str, count: int = 5) -> List[Dict]:
        """生成多个模板实例"""
        instances = []
        for _ in range(count):
            instance = self.instantiate_template(template_id)
            if instance:
                instances.append(instance)
        return instances
    
    def generate_all_instances(self, count_per_template: int = 5) -> List[Dict]:
        """生成所有模板的实例"""
        all_instances = []
        for template_id in self.templates:
            instances = self.generate_instances(template_id, count_per_template)
            all_instances.extend(instances)
        return all_instances
