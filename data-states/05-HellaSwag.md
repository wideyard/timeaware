# 05. HellaSwag 数据集说明

## 1. 数据集定位
- 任务类型：常识完形续写（多选）
- 目录位置：data/HellaSwag
- README 来源：data/HellaSwag/LICENSE, data/HellaSwag/README.md, data/HellaSwag/adversarial_filtering/README.md, data/HellaSwag/data/README.md, data/HellaSwag/hellaswag_models/README.md, data/HellaSwag/adversarial_filtering/bert/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/HellaSwag/data/hellaswag_train.jsonl: 39905
- data/HellaSwag/data/hellaswag_test.jsonl: 10003
- data/HellaSwag/data/hellaswag_val.jsonl: 10042
- data/HellaSwag/hellaswag_models/bertlarge-example-submission.csv: 10004
- 已统计主文件合计（非去重）：69954

## 3. 数据样例
- 样例来源：data/HellaSwag/data/hellaswag_train.jsonl

```text
{"ind": 4, "activity_label": "Removing ice from car", "ctx_a": "Then, the man writes over the snow covering the window of a car, and a woman wearing winter clothes smiles.", "ctx_b": "then", "ctx": "Then, the man writes over the snow covering the window of a c ...
```

## 4. 数据构造方法
- 方法概述：给定场景前缀 ctx 与四个 endings，通过对抗过滤（adversarial filtering）构造高迷惑负例。
- README/文件线索：* The HellaSwag dataset, in `data/`

## 5. 数据构造目的
- 目标：评估模型对日常事件连续性与物理/社会常识的理解。

## 6. 你在使用前需要注意
- 关键注意事项：split_type 可区分 indomain 等设置；test 通常不提供标签。
- README 摘要：HellaSwag: Can a Machine _Really_ Finish Your Sentence?
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。