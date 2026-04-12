# 18. TimeDial 数据集说明

## 1. 数据集定位
- 任务类型：对话时间补全/推理（mask 预测）
- 目录位置：data/TimeDial
- README 来源：data/TimeDial/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/TimeDial/test.json: 1446
- 已统计主文件合计（非去重）：1446

## 3. 数据样例
- 样例来源：data/TimeDial/test.json

```text
{'conversation': ["A:We need to take the accounts system offline to carry out the upgrade . But don't worry , it won't cause too much inconvenience . We're going to do it over the weekend .", 'B: How long will the system be down for ?', "A: We'll be taking eve ...
```

## 4. 数据构造方法
- 方法概述：在多轮对话中掩蔽时间表达，利用上下文推断合理时间片段。
- README/文件线索：TimeDial presents a crowdsourced English challenge set, for temporal commonsense reasoning, formulated as a multiple choice cloze task with around 1.5k carefully curated dialogs. The dataset is derived from the DailyDialog ([Li et al., 2017](https://www.aclweb.org/anthology/I17-1099/)), which is a multi-turn dialog corpus.；## Dataset Description；TimeDial dataset consists of 1,104 dialog instances with 2 correct and 2 incorrect options with the following statistics:

## 5. 数据构造目的
- 目标：评估对话场景下的时间一致性理解能力。

## 6. 你在使用前需要注意
- 关键注意事项：当前目录主要提供 test；训练集可能在上游仓库或其他分发路径。
- README 摘要：TimeDial presents a crowdsourced English challenge set, for temporal commonsense reasoning, formulated as a multiple choice cloze task with around 1.5k carefully curated dialogs. The dataset is derived from the DailyDialog ([Li et al., 2017](https://www.aclweb.org/anthology/I17-1099/)), which is a multi-turn dialog corpus.
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。