"""QA类型模块"""

from qa_types.historical_events import generate_historical_events_qa
from qa_types.duration import generate_duration_qa
from qa_types.implicit_time import generate_implicit_time_qa
from qa_types.fictional_timeline import generate_fictional_timeline_qa
from qa_types.ordering import generate_ordering_qa
from qa_types.concurrency import generate_concurrency_qa

# 所有QA类型生成器
QA_GENERATORS = {
    "historical_events": generate_historical_events_qa,
    "duration": generate_duration_qa,
    "implicit_time": generate_implicit_time_qa,
    "fictional_timeline": generate_fictional_timeline_qa,
    "ordering": generate_ordering_qa,
    "concurrency": generate_concurrency_qa,
}

# QA类型描述
QA_TYPE_DESCRIPTIONS = {
    "historical_events": "历史事件（冷门事件或故意反转事实）",
    "duration": "日常活动的持续时间",
    "implicit_time": "隐式时间戳与前提条件推断",
    "fictional_timeline": "防止数据污染的虚拟时间线",
    "ordering": "事件的先后顺序",
    "concurrency": "多事件的并发冲突",
}
