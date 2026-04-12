# 19. TimeQA 数据集说明

## 1. 数据集定位
- 任务类型：时间约束问答（知识 + 文本）
- 目录位置：data/TimeQA
- README 来源：data/TimeQA/LICENSE, data/TimeQA/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/TimeQA/dataset/test.hard.json: 3078
- data/TimeQA/dataset/dev.hard.json: 3087
- data/TimeQA/dataset/test.easy.json: 2997
- data/TimeQA/dataset/dev.easy.json: 3021
- data/TimeQA/dataset/annotated_train.json: 3561
- data/TimeQA/dataset/human_test.easy.json: 989
- 已统计主文件合计（非去重）：16733

## 3. 数据样例
- 样例来源：data/TimeQA/dataset/test.hard.json

```text
{"idx": "/wiki/Attaphol_Buspakom#P54#0", "question": "Which team did Attaphol Buspakom play for between Apr 1987 and Nov 1988?", "context": "Attaphol Buspakom Attaphol Buspakom ( ; ) , nicknamed Tak ( ; ) ; 1 October 1962 \u2013 16 April 2015 ) was a Thai nati ...
```

## 4. 数据构造方法
- 方法概述：围绕时间区间构造问题，并区分 easy/hard、human test 等切分。
- README/文件线索：The repo contains the dataset and code for NeurIPS2021 (dataset track) paper [Time-Sensitive Question Answering dataset](https://arxiv.org/abs/2108.06314). The dataset is collected by UCSB NLP group and issued under BSD 3-Clause "New" or "Revised" License.；This dataset is aimed to study the existing reading comprehension models' capability to perform temporal reasoning, and see whether they are sensitive to the temporal description in the given question. An example of annotated question-answer pairs are listed as follows:；- dataset/: this folder contains all the dataset

## 5. 数据构造目的
- 目标：评测模型在时间限定条件下进行实体关系问答与证据定位能力。

## 6. 你在使用前需要注意
- 关键注意事项：多个 .json 为逐行对象格式，解析时按 jsonl 处理更稳妥。
- README 摘要：The repo contains the dataset and code for NeurIPS2021 (dataset track) paper [Time-Sensitive Question Answering dataset](https://arxiv.org/abs/2108.06314). The dataset is collected by UCSB NLP group and issued under BSD 3-Clause "New" or "Revised" License.
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。