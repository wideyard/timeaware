"""日程安排类对话模板"""

from datetime import datetime, timedelta
import random

def get_weekday_name(date: datetime) -> str:
    """获取中文星期名称"""
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return weekdays[date.weekday()]

def get_relative_day(current_date: datetime, target_date: datetime) -> str:
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
        return f"{get_weekday_name(target_date)}"
    else:
        return f"{target_date.month}月{target_date.day}日"

# 模板1: 基础会议安排
BASIC_MEETING_TEMPLATE = {
    "id": "scheduling_001",
    "type": "scheduling",
    "name": "基础会议安排",
    "description": "用户安排一个会议，包含开始时间和持续时长",
    "variables": {
        "current_date": lambda: datetime.now().strftime("%Y-%m-%d"),
        "meeting_day_offset": lambda: random.randint(2, 7),
        "meeting_hour": lambda: random.choice([9, 10, 14, 15, 16]),
        "meeting_duration_minutes": lambda: random.choice([60, 90, 120]),
    },
    "dialogue_template": [
        {
            "role": "user",
            "content": "帮我安排{meeting_day_desc}下午{meeting_hour}点的跨部门会议，持续{meeting_duration_desc}。"
        },
        {
            "role": "assistant",
            "content": "好的，我已为您安排了{meeting_day_desc}下午{meeting_hour}点的跨部门会议，持续{meeting_duration_desc}。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {meeting_hour_padded}:00",
                "meeting_end": "{meeting_end_time}",
                "conflict_resolved": False
            }
        }
    ],
    "state_template": {
        "meeting_start": "{meeting_day_name} {meeting_hour_padded}:00",
        "meeting_end": "{meeting_end_time}",
        "conflict_resolved": False
    }
}

# 模板2: 会议修改 - 提前
MEETING_EARLIER_TEMPLATE = {
    "id": "scheduling_002",
    "type": "scheduling",
    "name": "会议提前修改",
    "description": "用户要求将会议提前",
    "variables": {
        "current_date": lambda: datetime.now().strftime("%Y-%m-%d"),
        "meeting_day_offset": lambda: random.randint(3, 7),
        "original_hour": lambda: random.choice([14, 15, 16]),
        "hours_to_earlier": lambda: random.choice([1, 2, 3]),
    },
    "dialogue_template": [
        {
            "role": "user",
            "content": "帮我安排{meeting_day_desc}下午{original_hour}点的项目汇报会议，持续一个半小时。"
        },
        {
            "role": "assistant",
            "content": "好的，已安排。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {original_hour_padded}:00",
                "meeting_end": "{original_end_time}",
                "conflict_resolved": False
            }
        },
        {
            "role": "user",
            "content": "我想把会议提前{hours_to_earlier}个小时，可以吗？"
        },
        {
            "role": "assistant",
            "content": "好的，已将会议调整为{meeting_day_desc}下午{new_hour}点。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {new_hour_padded}:00",
                "meeting_end": "{new_end_time}",
                "conflict_resolved": True
            }
        }
    ],
    "state_template": {
        "meeting_start": "{meeting_day_name} {new_hour_padded}:00",
        "meeting_end": "{new_end_time}",
        "conflict_resolved": True
    }
}

# 模板3: 会议修改 - 换天
MEETING_CHANGE_DAY_TEMPLATE = {
    "id": "scheduling_003",
    "type": "scheduling",
    "name": "会议换天修改",
    "description": "用户要求将会议改到另一天",
    "variables": {
        "current_date": lambda: datetime.now().strftime("%Y-%m-%d"),
        "meeting_day_offset": lambda: random.randint(3, 7),
        "new_day_offset": lambda: random.choice([-1, 1, 2]),
        "meeting_hour": lambda: random.choice([10, 14, 15]),
    },
    "dialogue_template": [
        {
            "role": "user",
            "content": "帮我安排{meeting_day_desc}下午{meeting_hour}点的团队周会，持续1小时。"
        },
        {
            "role": "assistant",
            "content": "好的，已安排。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {meeting_hour_padded}:00",
                "meeting_end": "{original_end_time}",
                "conflict_resolved": False
            }
        },
        {
            "role": "user",
            "content": "那天我有事，改到{new_day_desc}同一时间吧。"
        },
        {
            "role": "assistant",
            "content": "好的，已将会议调整到{new_day_name}下午{meeting_hour}点。",
            "hidden_state": {
                "meeting_start": "{new_day_name} {meeting_hour_padded}:00",
                "meeting_end": "{new_end_time}",
                "conflict_resolved": True
            }
        }
    ],
    "state_template": {
        "meeting_start": "{new_day_name} {meeting_hour_padded}:00",
        "meeting_end": "{new_end_time}",
        "conflict_resolved": True
    }
}

# 模板4: 冲突解决
MEETING_CONFLICT_TEMPLATE = {
    "id": "scheduling_004",
    "type": "scheduling",
    "name": "会议冲突解决",
    "description": "用户发现会议时间有冲突，需要调整",
    "variables": {
        "current_date": lambda: datetime.now().strftime("%Y-%m-%d"),
        "meeting_day_offset": lambda: random.randint(3, 7),
        "meeting_hour": lambda: random.choice([14, 15]),
        "conflict_hour": lambda: random.choice([15, 16]),
    },
    "dialogue_template": [
        {
            "role": "user",
            "content": "帮我安排{meeting_day_desc}下午{meeting_hour}点的产品评审会，持续2小时。"
        },
        {
            "role": "assistant",
            "content": "好的，已安排。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {meeting_hour_padded}:00",
                "meeting_end": "{original_end_time}",
                "conflict_resolved": False
            }
        },
        {
            "role": "user",
            "content": "糟了，我那天下午{conflict_hour}点要去见客户，能提前到{new_hour}点开始吗？"
        },
        {
            "role": "assistant",
            "content": "好的，已将会议调整为{meeting_day_desc}下午{new_hour}点，这样在见客户前可以结束。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {new_hour_padded}:00",
                "meeting_end": "{new_end_time}",
                "conflict_resolved": True
            }
        }
    ],
    "state_template": {
        "meeting_start": "{meeting_day_name} {new_hour_padded}:00",
        "meeting_end": "{new_end_time}",
        "conflict_resolved": True
    }
}

# 模板5: 多轮修改
MEETING_MULTI_CHANGE_TEMPLATE = {
    "id": "scheduling_005",
    "type": "scheduling",
    "name": "多轮会议修改",
    "description": "用户多次修改会议时间",
    "variables": {
        "current_date": lambda: datetime.now().strftime("%Y-%m-%d"),
        "meeting_day_offset": lambda: random.randint(4, 7),
        "original_hour": lambda: random.choice([14, 15]),
        "first_change_hours": lambda: random.choice([-2, -1, 1, 2]),
        "second_change_desc": lambda: random.choice(["前一天同一时刻", "后一天同一时刻"]),
    },
    "dialogue_template": [
        {
            "role": "user",
            "content": "帮我安排{meeting_day_desc}下午{original_hour}点的预算讨论会，持续1个半小时。"
        },
        {
            "role": "assistant",
            "content": "好的，已安排。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {original_hour_padded}:00",
                "meeting_end": "{original_end_time}",
                "conflict_resolved": False
            }
        },
        {
            "role": "user",
            "content": "能提前{first_change_desc}吗？"
        },
        {
            "role": "assistant",
            "content": "好的，已调整。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {first_hour_padded}:00",
                "meeting_end": "{first_end_time}",
                "conflict_resolved": False
            }
        },
        {
            "role": "user",
            "content": "还是不太好，改到{second_change_desc}吧。"
        },
        {
            "role": "assistant",
            "content": "好的，已将会议调整到{final_day_name}下午{final_hour}点。",
            "hidden_state": {
                "meeting_start": "{final_day_name} {final_hour_padded}:00",
                "meeting_end": "{final_end_time}",
                "conflict_resolved": True
            }
        }
    ],
    "state_template": {
        "meeting_start": "{final_day_name} {final_hour_padded}:00",
        "meeting_end": "{final_end_time}",
        "conflict_resolved": True
    }
}

SCHEDULING_TEMPLATES = {
    "scheduling_001": BASIC_MEETING_TEMPLATE,
    "scheduling_002": MEETING_EARLIER_TEMPLATE,
    "scheduling_003": MEETING_CHANGE_DAY_TEMPLATE,
    "scheduling_004": MEETING_CONFLICT_TEMPLATE,
    "scheduling_005": MEETING_MULTI_CHANGE_TEMPLATE,
}
