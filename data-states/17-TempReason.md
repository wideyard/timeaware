# 17. TempReason 数据集说明

## 1. 数据集定位
- 任务类型：时间算术与日期推理
- 目录位置：data/TempReason
- README 来源：data/TempReason/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/TempReason/train_l2.json: 16017
- data/TempReason/train_l3.json: 13014
- data/TempReason/test_l2.json: 5397
- data/TempReason/train_l1.json: 400000
- data/TempReason/test_l3.json: 4426
- data/TempReason/val_l2.json: 5521
- 已统计主文件合计（非去重）：444375

## 3. 数据样例
- 样例来源：data/TempReason/train_l2.json

```text
{"question": "Which position did Clarence Norman Brunsdale hold in May, 1946?", "date": "May 27, 1946", "text_answers": {"text": ["member of the State Senate of North Dakota"]}, "id": "L2_Q367750_P39_0", "fact_context": "Clarence Norman Brunsdale holds the pos ...
```

## 4. 数据构造方法
- 方法概述：自动生成“若干年/月之后（或之前）”类问题，配对标准化日期答案。
- README/文件线索：Due to the size limit of Github repositories, please download the dataset by the following commands:；git clone https://huggingface.co/datasets/tonytan48/TempReason；The TempReason dataset to evaluate the temporal reasoning capability of Large Language Models.

## 5. 数据构造目的
- 目标：测试模型在公历日期上的算术推理和格式化输出能力。

## 6. 你在使用前需要注意
- 关键注意事项：部分 .json 实际为 jsonl（逐行 JSON），读取时应按行解析。
- README 摘要：Data and implementation for "Towards Benchmarking and Improving the Temporal Reasoning Capability of Large Language Models"
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。