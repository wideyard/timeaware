# 20. tracie 数据集说明

## 1. 数据集定位
- 任务类型：时间关系一致性判断（before/after）
- 目录位置：data/tracie
- README 来源：data/tracie/LICENSE, data/tracie/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/tracie/data/matres/matres_train_before_after_tracie_style.txt: 20826
- data/tracie/data/iid-symbolic-format/test.txt: 4248
- data/tracie/data/uniform-prior-symbolic-format/test.txt: 4248
- data/tracie/data/iid-symbolic-format/train.txt: 1174
- data/tracie/data/iid/tracie_test.txt: 4248
- data/tracie/data/uniform-prior/tracie_test.txt: 4248
- 已统计主文件合计（非去重）：38992

## 3. 数据样例
- 样例来源：data/tracie/data/matres/matres_train_before_after_tracie_style.txt

```text
event: Valley Federal Savings amp Loan Association took an $ 89.9 million charge as it reported a third - quarter loss of $ 70.7 million , or $ 12.09 a share starts after it reported a third - quarter loss of $ 70.7 million , or $ 12.09 a share story: Valley F ...
```

## 4. 数据构造方法
- 方法概述：将故事与事件关系改写为正负样本，判断事件时间关系是否与叙事一致。
- README/文件线索：We include the dataset TRACIE and the proposed reasoning model SymTime here.；TRACIE is our crowdsourced dataset that is designed to evaluate system's ability for temporal reasoning over implicit events.；## Dataset

## 5. 数据构造目的
- 目标：测试模型在短叙事中的时序推断与矛盾识别能力。

## 6. 你在使用前需要注意
- 关键注意事项：包含 iid 与 uniform-prior 等不同采样设置，比较实验需保持同分布。
- README 摘要：This is the data and code repository for our NAACL 2021 paper "Temporal Reasoning on Implicit Events from Distant Supervision". We include the dataset TRACIE and the proposed reasoning model SymTime here.
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。