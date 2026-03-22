"""对话模板定义"""

from dialogue.templates.scheduling_templates import SCHEDULING_TEMPLATES
from dialogue.templates.modification_templates import MODIFICATION_TEMPLATES

# 所有对话模板
ALL_TEMPLATES = {
    **SCHEDULING_TEMPLATES,
    **MODIFICATION_TEMPLATES,
}

# 模板类型描述
TEMPLATE_TYPE_DESCRIPTIONS = {
    "scheduling": "日程安排类对话",
    "modification": "日程修改类对话",
}
