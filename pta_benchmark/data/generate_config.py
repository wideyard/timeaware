"""生成扩充后的活动分布配置文件"""

import json
import os

def load_expanded_distributions(filepath: str) -> dict:
    """加载扩充的分布"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("distributions", {})


def filter_high_quality(distributions: dict, min_score: float = 0.7) -> dict:
    """过滤高质量的分布"""
    filtered = {}
    for key, value in distributions.items():
        if value.get("quality_score", 0) >= min_score:
            # 只保留分布配置
            filtered[key] = {
                "type": value["type"],
                "params": value["params"]
            }
    return filtered


def generate_config_file(
    original_distributions: dict,
    expanded_distributions: dict,
    output_path: str
):
    """生成配置文件"""
    
    # 合并分布
    merged = {}
    
    # 先添加原始分布
    for key, value in original_distributions.items():
        merged[key] = value
    
    # 添加扩充分布（不覆盖原始）
    added_count = 0
    for key, value in expanded_distributions.items():
        if key not in merged:
            merged[key] = value
            added_count += 1
    
    print(f"原始活动: {len(original_distributions)}")
    print(f"扩充活动: {len(expanded_distributions)}")
    print(f"新增活动: {added_count}")
    print(f"总计活动: {len(merged)}")
    
    # 生成Python配置文件
    config_content = f'''"""扩充后的活动分布配置

自动生成于 MCTACO 数据集
原始活动: {len(original_distributions)} 个
扩充活动: {added_count} 个
总计: {len(merged)} 个活动
"""

# 活动持续时间分布配置（分钟）
ACTIVITY_DISTRIBUTIONS = {{
'''
    
    # 按类型分组
    original_keys = set(original_distributions.keys())
    
    # 原始活动
    config_content += '    # ===== 原始活动 =====\n'
    for key, value in sorted(merged.items()):
        if key in original_keys:
            config_content += f'    "{key}": {{"type": "{value["type"]}", "params": {value["params"]}}},\n'
    
    # 扩充活动
    config_content += '\n    # ===== MCTACO扩充活动 =====\n'
    for key, value in sorted(merged.items()):
        if key not in original_keys:
            config_content += f'    "{key}": {{"type": "{value["type"]}", "params": {value["params"]}}},\n'
    
    config_content += '}\n'
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"\n配置文件已生成: {output_path}")
    
    return merged


def main():
    # 路径设置
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    expanded_path = os.path.join(project_root, "output", "expanded_distributions.json")
    config_output_path = os.path.join(project_root, "pta_benchmark", "data", "expanded_activities.py")
    
    # 原始分布
    from pta_benchmark.config import ACTIVITY_DISTRIBUTIONS
    
    # 加载扩充分布
    expanded = load_expanded_distributions(expanded_path)
    
    # 过滤高质量的
    filtered = filter_high_quality(expanded, min_score=0.8)
    print(f"过滤后保留: {len(filtered)} 个高质量分布")
    
    # 生成配置文件
    merged = generate_config_file(
        ACTIVITY_DISTRIBUTIONS,
        filtered,
        config_output_path
    )
    
    # 打印一些示例
    print("\n=== 新增活动示例 ===")
    original_keys = set(ACTIVITY_DISTRIBUTIONS.keys())
    new_activities = [k for k in merged.keys() if k not in original_keys]
    for act in sorted(new_activities)[:10]:
        dist = merged[act]
        print(f"  {act}: {dist['type']}({dist['params']})")


if __name__ == "__main__":
    main()
