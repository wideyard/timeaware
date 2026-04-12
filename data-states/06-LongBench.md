# 06. LongBench 数据集说明

## 1. 数据集定位
- 任务类型：长上下文综合评测（QA/摘要/代码等多任务）
- 目录位置：data/LongBench
- README 来源：data/LongBench/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/LongBench/data/repobench-p.jsonl: 500
- data/LongBench/data/narrativeqa.jsonl: 200
- data/LongBench/data/repobench-p_e.jsonl: 300
- data/LongBench/data/lcc_e.jsonl: 300
- data/LongBench/data/gov_report_e.jsonl: 300
- data/LongBench/data/musique.jsonl: 200
- 已统计主文件合计（非去重）：1800

## 3. 数据样例
- 样例来源：data/LongBench/data/repobench-p.jsonl

```text
{"input": "package kademlia;\nimport java.io.DataInputStream;\nimport java.io.DataOutputStream;\nimport java.io.File;\nimport java.io.FileInputStream;\nimport java.io.FileNotFoundException;\nimport java.io.FileOutputStream;\nimport java.io.IOException;\nimport ...
```

## 4. 数据构造方法
- 方法概述：整合多个子任务数据集为统一 jsonl 格式，每条包含 input/context/answers 等字段。
- README/文件线索：We are fully aware of the potentially high costs involved in the model evaluation process, especially in the context of long context scenarios (such as manual annotation costs or API call costs). Therefore, we adopt a fully automated evaluation method, aimed at measuring and evaluating the model's ability to understand long contexts at the lowest cost.；LongBench includes 14 English tasks, 5 Chinese tasks, and 2 code tasks, with the average length of most tasks ranging from 5k to 15k, and a total of 4,750 test data. For detailed statistics and construction methods of LongBench tasks, please refer [here](task.md). In addition, we provide LongBench-E, a test set with a more uniform length distribution constructed by uniform sampling, with comparable amounts of data in the 0-4k, 4k-8k, and 8k+ length intervals to provide an analysis of the model's performance variations at different input lengths.；from datasets import load_dataset

## 5. 数据构造目的
- 目标：评估长上下文模型在不同任务类型上的鲁棒性与泛化。

## 6. 你在使用前需要注意
- 关键注意事项：该目录是多子集集合，不是单一任务；报告结果时需分子任务汇总。
- README 摘要：--- task_categories: - question-answering - text-generation - summarization - text-classification language: - en - zh tags: - Long Context size_categories: - 1K<n<10K ---
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。