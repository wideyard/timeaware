# 02. choice-75 数据集说明

## 1. 数据集定位
- 任务类型：目标导向程序脚本分支选择与理由生成
- 目录位置：data/choice-75
- README 来源：data/choice-75/README.md, data/choice-75/data/choice-75/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/choice-75/data/choice-75/user_profile/train/155.json: 6
- data/choice-75/data/choice-75/user_profile/dev/288.json: 5
- data/choice-75/data/choice-75/user_profile/dev/35.json: 5
- data/choice-75/data/choice-75/user_profile/train/174.json: 6
- data/choice-75/data/choice-75/user_profile/dev/317.json: 5
- data/choice-75/data/choice-75/user_profile/dev/194.json: 5
- 已统计主文件合计（非去重）：32

## 3. 数据样例
- 样例来源：data/choice-75/data/choice-75/user_profile/train/155.json

```text
{'goal': 'go back in time'}
```

## 4. 数据构造方法
- 方法概述：围绕日常 goal 构造步骤序列，在关键分歧点设置两个候选分支并标注 rationale（如 op1_ra/op2_ra）。
- README/文件线索：# Choice-75: A Dataset on Decision Branching in Script Learning；- Location: `/data/final_dataset/`；- `dataset`: dataset, could be `train`, `dev`, `test`

## 5. 数据构造目的
- 目标：评测模型在程序化计划中做分支决策、解释决策依据以及检索相关步骤的能力。

## 6. 你在使用前需要注意
- 关键注意事项：仓库中含 archived 与任务提示模板文件，训练时应区分原始标注数据与 prompt 资源。
- README 摘要：- [Link to paper](https://aclanthology.org/2024.lrec-main.285/)
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。