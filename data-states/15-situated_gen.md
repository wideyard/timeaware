# 15. situated_gen 数据集说明

## 1. 数据集定位
- 任务类型：情境化陈述生成与一致性建模
- 目录位置：data/situated_gen
- README 来源：data/situated_gen/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/situated_gen/data/train.jsonl: 5641
- data/situated_gen/data/dev.jsonl: 1407
- data/situated_gen/data/test.jsonl: 1220
- data/situated_gen/data/preprocessed/statements/arc.json: 643
- data/situated_gen/data/preprocessed/statements/creak.json: 1573
- data/situated_gen/data/preprocessed/statements/strategyqa.jsonl: 953
- 已统计主文件合计（非去重）：11437

## 3. 数据样例
- 样例来源：data/situated_gen/data/train.jsonl

```text
{"keywords":["the United Kingdom","Southeast Asia","Pakistan","History","telecommunication","Vodafone","region","services"],"statement":"Vodafone provides telecommunication services in the United Kingdom. The region of Southeast Asia includes the History of Pa ...
```

## 4. 数据构造方法
- 方法概述：从多个 QA/知识源抽取 statement 与关键词，构造可控生成样本。
- README/文件线索：> NeurIPS 2023 Datasets and Benchmarks Track；Datasets and Benchmarks, NeurIPS Datasets and Benchmarks 2023, New Orleans, LA, United States, December 10-16,；## Datasets

## 5. 数据构造目的
- 目标：训练模型在给定关键词/事实约束下生成连贯陈述。

## 6. 你在使用前需要注意
- 关键注意事项：除 train/dev/test 外，还提供 preprocessed statements 作为中间语料。
- README 摘要：This repository contains the data and code for the baseline described in the following paper:
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。