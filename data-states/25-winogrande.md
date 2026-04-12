# 25. winogrande 数据集说明

## 1. 数据集定位
- 任务类型：常识指代消解（Wino 式填空）
- 目录位置：data/winogrande
- README 来源：data/winogrande/README.md

## 2. 数据规模（基于仓库内可见文件）
- 未检测到可直接统计的数据文件（仅有说明或需额外下载）。

## 3. 数据样例
- 暂无样例（目录中未发现主数据文件）。

## 4. 数据构造方法
- 方法概述：围绕歧义指代句构造候选替换并标注正确项（官方为多规模版本）。
- README/文件线索：dataset_info:；splits:；dataset_size: 1595220

## 5. 数据构造目的
- 目标：评估模型在去偏置设置下的常识推理与指代解析能力。

## 6. 你在使用前需要注意
- 关键注意事项：当前目录仅见 README，未检出主数据文件；需从上游或附加脚本下载。
- README 摘要：--- language: - en paperswithcode_id: winogrande pretty_name: WinoGrande dataset_info: - config_name: winogrande_debiased features: - name: sentence dtype: string - name: option1 dtype: string - name: option2 dtype: string - name: answer dtype: string splits: - name: train num_bytes: 1203404
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。