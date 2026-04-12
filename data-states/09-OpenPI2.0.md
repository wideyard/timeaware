# 09. OpenPI2.0 数据集说明

## 1. 数据集定位
- 任务类型：过程理解与实体状态追踪
- 目录位置：data/OpenPI2.0
- README 来源：data/OpenPI2.0/LICENSE, data/OpenPI2.0/README.md, data/OpenPI2.0/api/README.md, data/OpenPI2.0/source/cluster/README.md, data/OpenPI2.0/data/outdated_cluster_data/README.md, data/OpenPI2.0/data/outdated_mturk_data/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/OpenPI2.0/data/train-data-reformatted-v4_pred-salience-gpt-4.json: 644
- data/OpenPI2.0/data/cluster-removed/train.json: 644
- data/OpenPI2.0/data/data_in_new_format/train-data-reformatted-v4.json: 644
- data/OpenPI2.0/data/train-ranked.json: 644
- data/OpenPI2.0/data/test-data-reformatted-v4_pred-salience-gpt-4.json: 111
- data/OpenPI2.0/data/dev-data-reformatted-v4_pred-salience-llama2-70.json: 55
- 已统计主文件合计（非去重）：2742

## 3. 数据样例
- 样例来源：data/OpenPI2.0/data/train-data-reformatted-v4_pred-salience-gpt-4.json

```text
{'1': {'goal': 'Flip Someone over Your Shoulder', 'steps': ['Be in a fighting position with this person.', 'Turn around, stepping away from them, pulling them towards you (this throws off their balance), and grab their arm.', 'Roll them off of your hip.', 'Onc ...
```

## 4. 数据构造方法
- 方法概述：围绕目标导向步骤（多源于 how-to）标注实体属性/状态在步骤前后的变化。
- README/文件线索：The original [OpenPI dataset](https://github.com/allenai/openpi-dataset) is one that trains and evaluates models to predict entity states throughout a procedure.；- A **dataset** for development, evaluation, and tuning of models to predict the above.；## Dataset

## 5. 数据构造目的
- 目标：训练模型理解 procedural text 中“谁在何时发生何种状态变化”。

## 6. 你在使用前需要注意
- 关键注意事项：包含多种重排与重格式版本（reformatted、ranked、cluster-removed），实验需固定版本。
- README 摘要：The original [OpenPI dataset](https://github.com/allenai/openpi-dataset) is one that trains and evaluates models to predict entity states throughout a procedure. ![alt text](figures/entity_tracking.png)
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。