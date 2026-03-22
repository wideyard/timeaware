"""日程修改类对话模板"""

from datetime import datetime, timedelta
import random

def get_weekday_name(date: datetime) -> str:
    """获取中文星期名称"""
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return weekdays[date.weekday()]

# 模板1: 取消会议
CANCEL_MEETING_TEMPLATE = {
    "id": "modification_001",
    "type": "modification",
    "name": "取消会议",
    "description": "用户取消之前安排的会议",
    "variables": {
        "current_date": lambda: datetime.now().strftime("%Y-%m-%d"),
        "meeting_day_offset": lambda: random.randint(2, 5),
        "meeting_hour": lambda: random.choice([10, 14, 15]),
    },
    "dialogue_template": [
        {
            "role": "user",
            "content": "帮我安排{meeting_day_desc}下午{meeting_hour}点的技术分享会，持续1小时。"
        },
        {
            "role": "assistant",
            "content": "好的，已安排。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {meeting_hour_padded}:00",
                "meeting_end": "{original_end_time}",
                "meeting_status": "scheduled",
                "conflict_resolved": False
            }
        },
        {
            "role": "user",
            "content": "那个技术分享会取消吧，主讲人出差了。"
        },
        {
            "role": "assistant",
            "content": "好的，已取消{meeting_day_desc}下午{meeting_hour}点的技术分享会。",
            "hidden_state": {
                "meeting_start": None,
                "meeting_end": None,
                "meeting_status": "cancelled",
                "conflict_resolved": True
            }
        }
    ],
    "state_template": {
        "meeting_start": None,
        "meeting_end": None,
        "meeting_status": "cancelled",
        "conflict_resolved": True
    }
}

# 模板2: 缩短会议
SHORTEN_MEETING_TEMPLATE = {
    "id": "modification_002",
    "type": "modification",
    "name": "缩短会议",
    "description": "用户要求缩短会议时长",
    "variables": {
        "current_date": lambda: datetime.now().strftime("%Y-%m-%d"),
        "meeting_day_offset": lambda: random.randint(2, 5),
        "meeting_hour": lambda: random.choice([9, 10, 14]),
        "original_duration": lambda: random.choice([90, 120]),
        "new_duration": lambda: random.choice([30, 45, 60]),
    },
    "dialogue_template": [
        {
            "role": "user",
            "content": "帮我安排{meeting_day_desc}上午{meeting_hour}点的项目启动会，持续{original_duration_desc}。"
        },
        {
            "role": "assistant",
            "content": "好的，已安排。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {meeting_hour_padded}:00",
                "meeting_end": "{original_end_time}",
                "meeting_duration_minutes": "{original_duration}",
                "conflict_resolved": False
            }
        },
        {
            "role": "user",
            "content": "时间太长了，改成{new_duration_desc}吧。"
        },
        {
            "role": "assistant",
            "content": "好的，已将会议时长调整为{new_duration_desc}。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {meeting_hour_padded}:00",
                "meeting_end": "{new_end_time}",
                "meeting_duration_minutes": "{new_duration}",
                "conflict_resolved": True
            }
        }
    ],
    "state_template": {
        "meeting_start": "{meeting_day_name} {meeting_hour_padded}:00",
        "meeting_end": "{new_end_time}",
        "meeting_duration_minutes": "{new_duration}",
        "conflict_resolved": True
    }
}

# 模板3: 添加参会者
ADD_PARTICIPANT_TEMPLATE = {
    "id": "modification_003",
    "type": "modification",
    "name": "添加参会者",
    "description": "用户在会议中添加新的参会者",
    "variables": {
        "current_date": lambda: datetime.now().strftime("%Y-%m-%d"),
        "meeting_day_offset": lambda: random.randint(2, 5),
        "meeting_hour": lambda: random.choice([10, 14, 15]),
        "duration": lambda: random.choice([60, 90]),
        "new_participant": lambda: random.choice(["张总", "李经理", "王总监", "赵工"]),
    },
    "dialogue_template": [
        {
            "role": "user",
            "content": "帮我安排{meeting_day_desc}下午{meeting_hour}点的部门例会，持续{duration_desc}。"
        },
        {
            "role": "assistant",
            "content": "好的，已安排。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {meeting_hour_padded}:00",
                "meeting_end": "{end_time}",
                "participants": ["我"],
                "conflict_resolved": False
            }
        },
        {
            "role": "user",
            "content": "把{new_participant}也加上，他也要参加。"
        },
        {
            "role": "assistant",
            "content": "好的，已将{new_participant}添加到参会人员中。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {meeting_hour_padded}:00",
                "meeting_end": "{end_time}",
                "participants": ["我", "{new_participant}"],
                "conflict_resolved": True
            }
        }
    ],
    "state_template": {
        "meeting_start": "{meeting_day_name} {meeting_hour_padded}:00",
        "meeting_end": "{end_time}",
        "participants": ["我", "{new_participant}"],
        "conflict_resolved": True
    }
}

# 模板4: 会议改到下周
POSTPONE_NEXT_WEEK_TEMPLATE = {
    "id": "modification_004",
    "type": "modification",
    "name": "会议延期到下周",
    "description": "用户要求将会议延期到下周",
    "variables": {
        "current_date": lambda: datetime.now().strftime("%Y-%m-%d"),
        "meeting_day_offset": lambda: random.randint(2, 5),
        "meeting_hour": lambda: random.choice([10, 14, 15]),
        "duration": lambda: random.choice([60, 90]),
    },
    "dialogue_template": [
        {
            "role": "user",
            "content": "帮我安排{meeting_day_desc}下午{meeting_hour}点的年度总结会，持续{duration_desc}。"
        },
        {
            "role": "assistant",
            "content": "好的，已安排。",
            "hidden_state": {
                "meeting_start": "{meeting_day_name} {meeting_hour_padded}:00",
                "meeting_end": "{end_time}",
                "meeting_status": "scheduled",
                "conflict_resolved": False
            }
        },
        {
            "role": "user",
            "content": "这周太忙了，改到下周同一时间吧。"
        },
        {
            "role": "assistant",
            "content": "好的，已将会议延期到下周{meeting_weekday}下午{meeting_hour}点。",
            "hidden_state": {
                "meeting_start": "下周{meeting_weekday} {meeting_hour_padded}:00",
                "meeting_end": "下周{meeting_weekday} {end_time_only}",
                "meeting_status": "postponed",
                "conflict_resolved": True
            }
        }
    ],
    "state_template": {
        "meeting_start": "下周{meeting_weekday} {meeting_hour_padded}:00",
        "meeting_end": "下周{meeting_weekday} {end_time_only}",
        "meeting_status": "postponed",
        "conflict_resolved": True
    }
}

MODIFICATION_TEMPLATES = {
    "modification_001": CANCEL_MEETING_TEMPLATE,
    "modification_002": SHORTEN_MEETING_TEMPLATE,
    "modification_003": ADD_PARTICIPANT_TEMPLATE,
    "modification_004": POSTPONE_NEXT_WEEK_TEMPLATE,
}
