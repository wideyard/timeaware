# 10. pasta 数据集说明

## 1. 数据集定位
- 任务类型：故事断言支持性判断与时间一致性分析
- 目录位置：data/pasta
- README 来源：data/pasta/readme.md

## 2. 数据规模（基于仓库内可见文件）
- data/pasta/data/val_data.jsonl: 1350
- data/pasta/data/tr_data.jsonl: 8476
- data/pasta/data/te_data.jsonl: 917
- data/pasta/data/human_eval_dat.csv: 201
- data/pasta/human_eval_data/mturk_op/MturkOP_Te_full_t_7_m_t5-base_b_10_lr_0.0001_w_1e-06_s_0_epoch_6.csv: 1213
- data/pasta/human_eval_data/mturk_op/MturkOP_Te_full_t_7_m_t5-large_b_4_lr_0.0001_w_1e-06_s_0_epoch_4.csv: 1213
- 已统计主文件合计（非去重）：13370

## 3. 数据样例
- 样例来源：data/pasta/data/val_data.jsonl

```text
{"AssignmentId":"3YMU66OBIOWA65CMWNDWXA9YU6JHG8","Input.Title":"Falling Through","Input.storyid":"3aa6ed51-7bb8-4992-a5e7-c7cb7fb68dd8","Input.line1":"Jimmy was working on his roof on a hot afternoon.","Input.line2":"He went to step on a part of the roof and s ...
```

## 4. 数据构造方法
- 方法概述：基于五句故事与断言，标注断言由哪些句子支持，并提供人类评测导出。
- README/文件线索：<u>**```PASTA```:A Dataset for Modeling Participant States in Narratives**</u>；- **Dataset**；The train, validation and test dataset are in ```data/tr_data.jsonl```, `data/val_data.jsonl` and ```data/te_data.jsonl``` respectively.

## 5. 数据构造目的
- 目标：评估模型在短叙事中对事实支持、时序连贯和解释性的处理能力。

## 6. 你在使用前需要注意
- 关键注意事项：human_eval_data 体量较大，属于评测导出；训练主数据在 data/*.jsonl。
- README 摘要：<u>**```PASTA```:A Dataset for Modeling Participant States in Narratives**</u>
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。