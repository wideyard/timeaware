# 07. MCTACO 数据集说明

## 1. 数据集定位
- 任务类型：时间常识问答（二分类 yes/no）
- 目录位置：data/MCTACO
- README 来源：data/MCTACO/README.md, data/MCTACO/_config.yml, data/MCTACO/dataset/readme.txt

## 2. 数据规模（基于仓库内可见文件）
- data/MCTACO/dataset/test_9442.tsv: 9442
- data/MCTACO/dataset/dev_3783.tsv: 3783
- data/MCTACO/experiments/roberta/roberta.output.txt: 9442
- data/MCTACO/experiments/esim/esim.glove.output.txt: 9442
- data/MCTACO/experiments/bert/bert.norm.output.txt: 9442
- data/MCTACO/experiments/esim/esim.elmo.output.txt: 9442
- 已统计主文件合计（非去重）：50993

## 3. 数据样例
- 样例来源：data/MCTACO/dataset/test_9442.tsv

```text
Durer's father died in 1502, and his mother died in 1513.	How long was his mother ill?	she was ill for 30 seconds	no	Event Duration Durer's father died in 1502, and his mother died in 1513.	How long was his mother ill?	six centuries	no	Event Duration
```

## 4. 数据构造方法
- 方法概述：给定句子、问题、候选答案和类别标签（如 Duration、Stationarity），判断候选是否成立。
- README/文件线索：Dataset and code for “Going on a vacation” takes longer than “Going for a walk”: A Study of Temporal Commonsense Understanding EMNLP 2019. ([link](https://arxiv.org/abs/1909.03065))；## Dataset；We provide the dev/test split as specified in the paper, along with a detailed readme.txt file under `dataset/`

## 5. 数据构造目的
- 目标：测试模型对时间范围、频率、顺序、持续时长等时间常识的掌握。

## 6. 你在使用前需要注意
- 关键注意事项：tsv 最后一列是 temporal category，可用于细粒度分析。
- README 摘要：Dataset and code for “Going on a vacation” takes longer than “Going for a walk”: A Study of Temporal Commonsense Understanding EMNLP 2019. ([link](https://arxiv.org/abs/1909.03065))
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。