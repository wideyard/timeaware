# 03. CosmosQA 数据集说明

## 1. 数据集定位
- 任务类型：阅读理解 + 常识选择题（四选一）
- 目录位置：data/CosmosQA
- README 来源：data/CosmosQA/README.md, data/CosmosQA/data/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/CosmosQA/data/train.csv: 25263
- data/CosmosQA/data/test.jsonl: 6963
- data/CosmosQA/data/valid.csv: 2986
- data/CosmosQA/data/sample_prediction.csv: 6964
- 已统计主文件合计（非去重）：42176

## 3. 数据样例
- 样例来源：data/CosmosQA/data/train.csv

```text
id,context,question,answer0,answer1,answer2,answer3,label 3Q9SPIIRWJKVQ8244310E8TUS6YWAC##34V1S5K3GTZMDUBNBIGY93FLDOB690##A1S1K7134S2VUC##Blog_1044056##q1_a1##3XU9MCX6VQQG7YPLCSAFDPQNH4GR20,"Good Old War and person L : I saw both of these bands Wednesday night ...
```

## 4. 数据构造方法
- 方法概述：基于叙事段落（多来自博客/故事）构造问题与 4 个候选答案，人工标注正确选项。
- README/文件线索：* The training/dev/test datasets for Cosmos QA can be found in ```data/```

## 5. 数据构造目的
- 目标：测试模型在给定上下文下进行隐含因果和社会常识推断的能力。

## 6. 你在使用前需要注意
- 关键注意事项：train/valid 为 csv，test 为 jsonl；提交格式通常是 id,label。
- README 摘要：This repository includes the source code and data for Cosmos QA.
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。