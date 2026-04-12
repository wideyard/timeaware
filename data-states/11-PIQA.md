# 11. PIQA 数据集说明

## 1. 数据集定位
- 任务类型：物理常识选择题（二选一）
- 目录位置：data/PIQA
- README 来源：无

## 2. 数据规模（基于仓库内可见文件）
- data/PIQA/physicaliqa-train-dev/train.jsonl: 16113
- data/PIQA/tests.jsonl: 3084
- data/PIQA/physicaliqa-train-dev/dev.jsonl: 1838
- data/PIQA/physicaliqa-train-dev/train-labels.lst: 16113
- data/PIQA/physicaliqa-train-dev/dev-labels.lst: 1838
- 已统计主文件合计（非去重）：38986

## 3. 数据样例
- 样例来源：data/PIQA/physicaliqa-train-dev/train.jsonl

```text
{"id": "f6be5fcc-d686-4549-8207-7904068693d7", "goal": "When boiling butter, when it's ready, you can", "sol1": "Pour it onto a plate", "sol2": "Pour it into a jar"} {"id": "ee9783b5-76a7-4beb-bbbb-9b179b11c43e", "goal": "To permanently attach metal legs to a  ...
```

## 4. 数据构造方法
- 方法概述：给定 goal 与两个解决方案，标签指示哪个方案更符合物理世界常识。
- README/文件线索：未提取到显式数据构造描述。

## 5. 数据构造目的
- 目标：测试模型在日常物理可行性判断上的能力。

## 6. 你在使用前需要注意
- 关键注意事项：文本与标签分离：jsonl 存题干与候选，*.lst 存金标。
- README 摘要：未找到 README。
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。