# 12. ProPara 数据集说明

## 1. 数据集定位
- 任务类型：过程段落中的参与者状态变化追踪
- 目录位置：data/ProPara
- README 来源：data/ProPara/EMNLP18-README.md, data/ProPara/LICENSE, data/ProPara/README.md, data/ProPara/XPAD_README.md, data/ProPara/data/naacl18/proglobal/README.md, data/ProPara/data/naacl18/prolocal/README.md, data/ProPara/data/naacl18/prolocal/output/README

## 2. 数据规模（基于仓库内可见文件）
- data/ProPara/data/naacl18/proglobal/all.chain.train.v3.recurssive.json: 1563
- data/ProPara/data/naacl18/prolocal/output/propara.run1.train.pred.json: 3133
- data/ProPara/data/naacl18/proglobal/all.chain.test.v3.recurssive.json: 256
- data/ProPara/data/naacl18/prolocal/propara.run1.train.json: 3133
- data/ProPara/data/naacl18/proglobal/all.chain.dev.v3.recurssive.json: 187
- data/ProPara/data/naacl18/prolocal/propara.run1.train.tsv: 3133
- 已统计主文件合计（非去重）：11405

## 3. 数据样例
- 样例来源：data/ProPara/data/naacl18/proglobal/all.chain.train.v3.recurssive.json

```text
{"instance":"908\trock\t7####when water freeze it become 10 % bigger , or take up 10 % more space . as water expand it put great pressure on the wall of anything contain it , include any rock which happen to be surround it . the force of the pressure exert on  ...
```

## 4. 数据构造方法
- 方法概述：围绕自然过程（如“油如何形成”）标注实体在每步的存在/位置变化，并扩展了多种子任务格式。
- README/文件线索：The ProPara dataset is designed to train and test comprehension of simple paragraphs describing processes, e.g., photosynthesis. We treat the comprehension task as that of predicting, tracking, and answering questions about how entities change during the process.；# Download the dataset；You can download the ProPara dataset from

## 5. 数据构造目的
- 目标：衡量模型对过程类文本中的动态状态更新与结构化推理能力。

## 6. 你在使用前需要注意
- 关键注意事项：目录同时包含官方数据、派生格式与测试夹具；统计时需区分真实训练集与测试资源。
- README 摘要：Data and code related to our recent [EMNLP'18 paper] (https://arxiv.org/abs/1808.10012) is released on 31st Oct 2018.
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。