"""配置文件"""

import os

# API配置
API_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "api.txt")

# 模型配置
MODELS = {
    "gpt-4o-mini": {
        "name": "gpt-4o-mini",
        "provider": "openai",
        "base_url": None,  # 从api.txt读取
        "api_key": None,   # 从api.txt读取
    },
    "doubao-seed-1-8": {
        "name": "doubao-seed-1-8-251228",
        "provider": "volcengine",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key": "d9b4e219-86d3-4a3a-aaef-31480e953613",
    },
    "doubao-seed-2-0-pro": {
        "name": "doubao-seed-2-0-pro-260215",
        "provider": "volcengine",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key": "d9b4e219-86d3-4a3a-aaef-31480e953613",
    },
}

# 默认模型（用于生成题目）
DEFAULT_MODEL = "gpt-4o-mini"

# 评测模型列表（用于对比实验）
EVAL_MODELS = ["gpt-4o-mini", "doubao-seed-1-8", "doubao-seed-2-0-pro"]

TEMPERATURE = 0.7
MAX_TOKENS = 2000

# 数据集配置
QA_COUNT_PER_TYPE = 17  # 每种类型生成题目数 (6*17=102道)
DIALOGUE_TEMPLATE_INSTANCES = 5  # 每个对话模板实例化次数

# 输出配置
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
QA_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "qa_benchmark.json")
DIALOGUE_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "dialogue_benchmark.json")
EVALUATION_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "evaluation_report.json")
COMPARISON_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "comparison_report.json")

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)
