# 16. SocialIQA 数据集说明

## 1. 数据集定位
- 任务类型：社会常识问答（三选一）
- 目录位置：data/SocialIQA
- README 来源：无

## 2. 数据规模（基于仓库内可见文件）
- data/SocialIQA/train.jsonl: 33410
- data/SocialIQA/dev.jsonl: 1954
- data/SocialIQA/train-labels.lst: 33410
- data/SocialIQA/dev-labels.lst: 1954
- 已统计主文件合计（非去重）：70728

## 3. 数据样例
- 样例来源：data/SocialIQA/train.jsonl

```text
{"context": "Cameron decided to have a barbecue and gathered her friends together.", "question": "How would Others feel as a result?", "answerA": "like attending", "answerB": "like staying home", "answerC": "a good friend to have"} {"context": "Jan needed to g ...
```

## 4. 数据构造方法
- 方法概述：给定 context+question+3 个选项，通过标签文件给出正确答案。
- README/文件线索：未提取到显式数据构造描述。

## 5. 数据构造目的
- 目标：评估模型对人物动机、反应和社会互动结果的常识推理能力。

## 6. 你在使用前需要注意
- 关键注意事项：与 PIQA 类似，标签在独立 lst 文件中。
- README 摘要：未找到 README。
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。