"""LLM客户端封装 - 支持多模型"""

import os
import json
from openai import OpenAI
from config import API_CONFIG_PATH, MODELS, DEFAULT_MODEL, TEMPERATURE, MAX_TOKENS


def load_api_config():
    """从api.txt加载API配置"""
    config = {}
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config


def get_client(model_key: str = DEFAULT_MODEL) -> tuple:
    """获取OpenAI客户端和模型配置
    
    Returns:
        tuple: (client, model_name)
    """
    model_config = MODELS.get(model_key, MODELS[DEFAULT_MODEL])
    
    # 获取API配置
    if model_config["provider"] == "openai":
        api_config = load_api_config()
        base_url = model_config.get("base_url") or api_config.get("OPENAI_BASE_URL")
        api_key = model_config.get("api_key") or api_config.get("OPENAI_API_KEY")
    else:
        base_url = model_config["base_url"]
        api_key = model_config["api_key"]
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    
    return client, model_config["name"]


def call_llm(prompt: str, system_prompt: str = None, 
             temperature: float = TEMPERATURE, model_key: str = DEFAULT_MODEL) -> str:
    """调用LLM生成响应
    
    Args:
        prompt: 用户提示
        system_prompt: 系统提示
        temperature: 温度参数
        model_key: 模型键名 (gpt-4o-mini, doubao-seed-1-8, doubao-seed-2-0-pro)
    
    Returns:
        str: LLM响应
    """
    client, model_name = get_client(model_key)
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=MAX_TOKENS,
    )
    
    return response.choices[0].message.content


def call_llm_json(prompt: str, system_prompt: str = None, 
                  temperature: float = TEMPERATURE, model_key: str = DEFAULT_MODEL) -> dict:
    """调用LLM并确保返回JSON格式
    
    Args:
        prompt: 用户提示
        system_prompt: 系统提示
        temperature: 温度参数
        model_key: 模型键名
    
    Returns:
        dict: 解析后的JSON
    """
    # 在prompt中明确要求返回JSON
    json_prompt = f"""{prompt}

请严格按照JSON格式返回，不要包含任何其他文字或markdown标记。"""
    
    response = call_llm(json_prompt, system_prompt, temperature, model_key)
    
    # 尝试解析JSON
    # 移除可能的markdown代码块标记
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    response = response.strip()
    
    return json.loads(response)


# 便捷函数
def call_gpt4o_mini(prompt: str, system_prompt: str = None, temperature: float = TEMPERATURE) -> str:
    """调用GPT-4o-mini"""
    return call_llm(prompt, system_prompt, temperature, "gpt-4o-mini")


def call_doubao_seed_1_8(prompt: str, system_prompt: str = None, temperature: float = TEMPERATURE) -> str:
    """调用Doubao-Seed-1.8"""
    return call_llm(prompt, system_prompt, temperature, "doubao-seed-1-8")


def call_doubao_seed_2_0_pro(prompt: str, system_prompt: str = None, temperature: float = TEMPERATURE) -> str:
    """调用Doubao-Seed-2.0-Pro"""
    return call_llm(prompt, system_prompt, temperature, "doubao-seed-2-0-pro")
