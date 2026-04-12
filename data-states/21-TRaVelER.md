# 21. TRaVelER 数据集说明

## 1. 数据集定位
- 任务类型：事件日志上的时间/指代检索推理
- 目录位置：data/TRaVelER
- README 来源：data/TRaVelER/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/TRaVelER/results/referential/gemma-7b-it/100Events.json: 102
- data/TRaVelER/results/explicit/gemma-7b-it/100Events.json: 102
- data/TRaVelER/results/referential/gemma-7b-it/90Events.json: 102
- data/TRaVelER/results/explicit/gemma-7b-it/90Events.json: 102
- data/TRaVelER/results/referential/gemma-7b-it/80Events.json: 102
- data/TRaVelER/results/explicit/gemma-7b-it/80Events.json: 102
- 已统计主文件合计（非去重）：612

## 3. 数据样例
- 样例来源：data/TRaVelER/results/referential/gemma-7b-it/100Events.json

```text
{'Response': "<bos><start_of_turn>user\nReview each event out of the event sets sequentially. Find all events where the action, object, subject and location match the information in the question. From the identified events, ascertain the one that occurred most ...
```

## 4. 数据构造方法
- 方法概述：合成事件序列并构造 explicit/referential 查询，评估模型从事件流中检索答案。
- README/文件线索：- Create new Events and Questions based on them: If you want to create a new Dataset with explicit and referential questions or not

## 5. 数据构造目的
- 目标：检验模型在结构化事件记忆上的时序检索与实体解析能力。

## 6. 你在使用前需要注意
- 关键注意事项：仓库中以结果文件为主，原始 dataset 可能在 dataset 子目录或外部来源。
- README 摘要：`BAMER` serves as a benchmark for assessing the capability of Large Language Models (LLMs) to interpret temporal references within extensive event sets. It comprises over 2,200 questions designed to evaluate LLM performance through a Question Answering task. Users can select from four state-of-the-art LLMs within the benchmark and analyze their performance based on the length of the event set and the clarity of the temporal references involved. <br>
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。