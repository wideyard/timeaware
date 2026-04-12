# 01. ATOMIC 数据集说明

## 1. 数据集定位
- 任务类型：常识时序与因果推理（事件后果、意图、反应）
- 目录位置：data/ATOMIC
- README 来源：data/ATOMIC/LICENSE, data/ATOMIC/README.md, data/ATOMIC/atomic2020_data-feb2021/LICENSE, data/ATOMIC/atomic2020_data-feb2021/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/ATOMIC/atomic2020_data-feb2021/train.tsv: 1076880
- data/ATOMIC/atomic2020_data-feb2021/test.tsv: 152209
- data/ATOMIC/atomic2020_data-feb2021/dev.tsv: 102024
- data/ATOMIC/v4_atomic_dev.csv: 22621
- data/ATOMIC/v4_atomic_all.csv: 249748
- data/ATOMIC/v4_atomic_trn.csv: 202272
- 已统计主文件合计（非去重）：1805754

## 3. 数据样例
- 样例来源：data/ATOMIC/atomic2020_data-feb2021/train.tsv

```text
PersonX abandons ___ altogether	oEffect	none PersonX abandons ___ altogether	oEffect	none
```

## 4. 数据构造方法
- 方法概述：以事件短语为锚点，人工/众包补全 xIntent、xEffect、oReact 等关系；同时保留 ATOMIC 2020 的三元组格式。
- README/文件线索：- `v4_atomic_all_agg.csv`: contains one event per line, with all annotations aggregated into one list (but not de-duplicated, so there might be repeats).；- `v4_atomic_all.csv`: keeps track of which worker did which annotations. Each line is the answers from one worker only, so there are multiple lines for the same event.；- `v4_atomic_trn.csv`, `v4_atomic_dev.csv`, `v4_atomic_tst.csv`: same as above, but split based on train/dev/test split.

## 5. 数据构造目的
- 目标：训练模型进行 if-then 常识推理，增强对事件因果链与人物心理状态的建模能力。

## 6. 你在使用前需要注意
- 关键注意事项：目录内同时包含 v4 csv 与 atomic2020 tsv 两种版本，字段定义不同，建模前需统一 schema。
- README 摘要：This tarball contains the ATOMIC knowledge graph. Files present: - `v4_atomic_all_agg.csv`: contains one event per line, with all annotations aggregated into one list (but not de-duplicated, so there might be repeats). - `v4_atomic_all.csv`: keeps track of which worker did which annotations. Each line is the answers from one worker only, so there are multiple lines for the same event.
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。