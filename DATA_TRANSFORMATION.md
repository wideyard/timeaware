# 时间推理基准测试 - 数据转换文档

## 概述

本文档描述了 `arch/` 框架中各数据集的转换过程，包括原始数据格式、转换策略和转换后的数据规模。

---

## 统一数据格式 (TemporalSample)

所有数据集在转换后都遵循统一的 `TemporalSample` 格式：

```python
@dataclass
class TemporalSample:
    id: str                          # 唯一标识
    task_type: TaskType              # 任务类型 (T1-T5)
    context: str                     # 上下文/背景信息
    delta_t: Optional[str] = None    # 时间推进量
    event: Optional[str] = None      # 事件描述
    query: str                       # 问题
    answer: Optional[str] = None     # 答案
    state: Optional[Dict] = None     # 状态信息
    reasoning: Optional[str] = None  # 推理过程
    ground_truth: Optional[Dict] = None  # 真实答案
    metadata: Dict = {}              # 元数据
```

---

## 任务类型映射

| 任务类型 | 说明 | 对应任务 |
|----------|------|----------|
| T1 | 时间计算 (Temporal Calculation) | Duration, Offset, Ordering |
| T2 | 状态追踪 (State Tracking) | Location, Status |
| T3 | 并发冲突 (Concurrency) | Space Conflict, Resource Conflict |
| T4 | 长期记忆 (Long-term Memory) | Information Retrieval |
| T5 | 反事实推理 (Counterfactual) | Rule Perturbation |

---

## 数据集详细说明

### 1. MCTACO

| 属性 | 值 |
|------|-----|
| 来源 | Google Research, EMNLP 2019 |
| 原始格式 | TSV |
| 文件路径 | `data/MCTACO/dataset/dev_3783.tsv`, `data/MCTACO/dataset/test_9442.tsv` |
| 任务类型 | T1, T2 |
| 转换后规模 | 1,229 samples (dev) |

**原始格式示例：**
```
sentence	question	answer	label	category
"John turned on the light."	"Is it bright in the room?"	"yes"	1	temporal
```

**转换策略：**
- 将 `sentence1` 和 `sentence2` 组合为上下文
- `tag` 映射到任务类型
- `additional_note` 作为补充信息

---

### 2. UDST-DurationQA

| 属性 | 值 |
|------|-----|
| 来源 | UMass & Stanford |
| 原始格式 | TSV |
| 文件路径 | `data/UDST-DurationQA/data/train.tsv`, `data/UDST-DurationQA/data/dev.tsv`, `data/UDST-DurationQA/data/test.tsv` |
| 任务类型 | T1 |
| 转换后规模 | 16,140 samples |

**原始格式示例：**
```
context	question	answer	section
"The concert started at 7pm and lasted 2 hours."	"When did the concert end?"	"9pm"	duration
```

**转换策略：**
- `context` 包含时间信息
- `question` 作为查询
- `answer` 提供时间计算结果

---

### 3. TimeDial

| 属性 | 值 |
|------|-----|
| 来源 | UIUC & Allen AI, EMNLP 2021 |
| 原始格式 | JSON |
| 文件路径 | `data/TimeDial/test.json` |
| 任务类型 | T1 |
| 转换后规模 | 1,446 samples |

**原始格式示例：**
```json
[{
  "id": 1,
  "conversation": ["Hello!", "Hi, what time is it?", "It's around 9:15 AM."],
  "correct1": "9:15 AM",
  "correct2": "nine fifteen am",
  "incorrect1": "9:00 AM",
  "incorrect2": "ten fifteen AM"
}]
```

**转换策略：**
- `conversation` 作为对话上下文
- `correct1/correct2` 作为正确时间值
- `incorrect1/incorrect2` 用于干扰选项

---

### 4. TRACIE

| 属性 | 值 |
|------|-----|
| 来源 | UMass, NAACL 2021 |
| 原始格式 | TXT (制表符分隔) |
| 文件路径 | `data/tracie/data/iid/tracie_train.txt`, `data/tracie/data/iid/tracie_test.txt` |
| 任务类型 | T2 |
| 转换后规模 | 1,174 samples |

**原始格式示例：**
```
event: Chad looked for his baseball cap starts after he got off the ride story: Chad had gone to an amusement park...	answer: positive
```

**转换策略：**
- 解析 `event:` 和 `story:` 部分作为状态追踪上下文
- `answer: positive/negative` 表示时间推理判断

---

### 5. situated_gen

| 属性 | 值 |
|------|-----|
| 来源 | Allen AI |
| 原始格式 | JSONL |
| 文件路径 | `data/situated_gen/data/train.jsonl`, `data/situated_gen/data/dev.jsonl`, `data/situated_gen/data/test.jsonl` |
| 任务类型 | T2 |
| 转换后规模 | 5,641 samples |

**原始格式示例：**
```json
{
  "context": "Alice is in the kitchen. She picks up an apple.",
  "state_query": "Where is the apple?",
  "state_answer": "in Alice's hand"
}
```

**转换策略：**
- 保留完整的场景上下文
- 提取状态变化信息
- 映射到 T2 状态追踪任务

---

### 6. DROP

| 属性 | 值 |
|------|-----|
| 来源 | AI2, ACL 2019 |
| 原始格式 | Parquet |
| 文件路径 | `data/DROP/train.parquet`, `data/DROP/validation.parquet` |
| 任务类型 | T1 |
| 转换后规模 | 77,400 samples (train) |

**原始格式示例：**
```python
{
  "passage": "The battle lasted from 1861 to 1865.",
  "question": "How long did the battle last?",
  "answers_spans": {"spans": ["4 years"], "types": ["duration"]}
}
```

**转换策略：**
- `passage` 作为上下文
- `question` 提取时间相关问题
- `answers_spans` 提供数字/时间答案

---

### 7. TimeQA

| 属性 | 值 |
|------|-----|
| 来源 | EMNLP 2023 |
| 原始格式 | JSON |
| 文件路径 | `data/TimeQA/dataset/annotated_train.json` |
| 任务类型 | T1 |
| 转换后规模 | 3,561 samples (train) |

**原始格式示例：**
```json
{
  "paras": ["Paragraph text with temporal information..."],
  "questions": [["2020-01-01", [{"answer": "event description"}]],
  "type": "temporal_reasoning"
}
```

**转换策略：**
- `paras` 组合为上下文
- 提取时间范围 `questions[0]`
- 答案从 `questions[1]` 获取

---

### 8. SocialIQA

| 属性 | 值 |
|------|-----|
| 来源 | ICLR 2020 |
| 原始格式 | JSONL |
| 文件路径 | `data/SocialIQA/dev.jsonl` |
| 任务类型 | T3 |
| 转换后规模 | 1,954 samples (dev) |

**原始格式示例：**
```json
{
  "context": "Alex borrowed a book from Sam.",
  "question": "What does Sam need to do next?",
  "answerA": "Give the book to Alex",
  "answerB": "Read the book",
  "answerC": "Return the book"
}
```

**转换策略：**
- `context` 作为社会情境
- `question` 询问后续行为
- 三个选项对应不同的并发状态
- 映射到 T3 并发冲突检测

---

### 9. CosmosQA

| 属性 | 值 |
|------|-----|
| 来源 | EMNLP 2019 |
| 原始格式 | CSV |
| 文件路径 | `data/CosmosQA/data/train.csv`, `data/CosmosQA/data/valid.csv` |
| 任务类型 | T3 |
| 转换后规模 | 28,247 samples (train+valid) |

**原始格式示例：**
```json
{
  "id": "train_1",
  "context": "The cake was eaten by everyone.",
  "question": "Why was the cake eaten?",
  "answer0": "It was delicious",
  "answer1": "It was rotting",
  "answer2": "Everyone was hungry",
  "answer3": "The cake was the only food"
}
```

**转换策略：**
- `context` 作为常识推理背景
- `question` 询问因果关系
- 四个选项用于测试推理一致性
- 映射到 T3 并发/因果推理

---

### 10. PIQA

| 属性 | 值 |
|------|-----|
| 来源 | NeurIPS 2019 |
| 原始格式 | JSONL |
| 文件路径 | `data/PIQA/tests.jsonl` |
| 任务类型 | T5 |
| 转换后规模 | 3,084 samples (test) |

**原始格式示例：**
```json
{
  "goal": "To make a cake rise, you can",
  "sol1": "Put it in the oven",
  "sol2": "Put it in the fridge"
}
```

**转换策略：**
- `goal` 作为物理常识问题
- `sol1` 和 `sol2` 是两个解决方案
- 需要在虚构规则下推理
- 映射到 T5 反事实/规则推理

---

### 11. LongBench

| 属性 | 值 |
|------|-----|
| 来源 | NeurIPS 2023 |
| 原始格式 | JSONL (本地) |
| 文件路径 | `data/LongBench/data/*.jsonl` |
| 任务类型 | T4 |
| 转换后规模 | 5,924 samples (all subsets) |

**子集分布：**
| 子集 | 样本数 |
|------|--------|
| narrativeqa | 200 |
| qasper | ~400 |
| hotpotqa | ~600 |
| ... | ... |

**原始格式示例：**
```json
{
  "input": "What happened to Saltram?",
  "context": "Long document text...",
  "answers": ["He became a doctor"],
  "dataset": "narrativeqa",
  "length": 127309
}
```

**转换策略：**
- `context` 是长文本 (平均 10K+ 字符)
- `input` 是检索查询
- `answers` 是真实答案
- 映射到 T4 长期记忆检索任务

---

### 12. ATOMIC

| 属性 | 值 |
|------|-----|
| 来源 | Allen AI, AAAI 2021 |
| 原始格式 | TSV |
| 文件路径 | `data/ATOMIC/system_eval/test.tsv` |
| 任务类型 | T5 |
| 转换后规模 | 5,000 samples (test) |

**原始格式示例：**
```
PersonX takes things for granted @@ xNeed	to have been lazy at work| to have wasted resources| none
```

**转换策略：**
- `@@` 前是前提 (head)
- `@@` 后是关系类型 (relation)
- `|` 分隔多个可能的尾部 (tail)
- 映射到 T5 反事实规则推理

---

### 13. NarrativeQA

| 属性 | 值 |
|------|-----|
| 来源 | Google, TACL 2018 |
| 原始格式 | CSV |
| 文件路径 | `data/NarrativeQA/qaps.csv` |
| 任务类型 | T4 |
| 转换后规模 | 10,557 samples (test) |

**原始格式示例：**
```csv
document_id,set,question,answer1,answer2,question_tokenized,answer1_tokenized,answer2_tokenized
0025577043f5090cd603c6aea60f26e236195594,test,Who is Mark Hunter?,He is a high school student in Phoenix.,A loner and outsider student...
```

**转换策略：**
- `document_id` 用于关联完整文档
- `question` 是关于故事的问题
- `answer1` 和 `answer2` 是两个参考答案
- 映射到 T4 长文本问答记忆任务

---

### 14. Winogrande

| 属性 | 值 |
|------|-----|
| 来源 | Allen AI, NeurIPS 2020 |
| 原始格式 | Parquet |
| 文件路径 | `data/Winogrande/winogrande_{xs,s,m,l,xl,debiased}/{train,test,validation}-*-of-*.parquet` |
| 任务类型 | T5 |
| 转换后规模 | 9,248 samples (all subsets) |

**子集：** xs, s, m, l, xl, debiased

**原始格式示例：**
```json
{
  "sentence": "Sam took the glass of water and gave it to _.",
  "option1": "Todd",
  "option2": "Jeff",
  "answer": "1",
  "license": "CC-BY-SA"
}
```

**转换策略：**
- `sentence` 中 `_` 是待填充的占位符
- `option1` 和 `option2` 是两个选项
- 需要理解反事实代词指代
- 映射到 T5 反事实推理

---

### 15. QASPer

| 属性 | 值 |
|------|-----|
| 来源 | Allen AI, NAACL 2021 |
| 原始格式 | JSON |
| 文件路径 | `data/qasper/qasper-{train,dev,test}-v0.3.json` |
| 任务类型 | T4 |
| 转换后规模 | 2,135 samples |

**原始格式示例：**
```json
{
  "id": "qasper_paper_1",
  "title": "Paper Title",
  "abstract": "...",
  "full_text": {...},
  "qas": [{
    "question": "What method was proposed?",
    "answers": [{"answer": "...", "answer_start": 123}]
  }]
}
```

**转换策略：**
- 论文全文作为上下文
- 问题来自 `qas`
- 答案提取自 `answers`
- 映射到 T4 学术文档长期记忆

---

### 16. ProPara

| 属性 | 值 |
|------|-----|
| 来源 | AI2, EMNLP 2018 |
| 原始格式 | TSV |
| 文件路径 | `data/ProPara/data/emnlp18/grids.v1.{split}.tsv` |
| 任务类型 | T2 |
| 转换后规模 | 482 samples (train+dev+test) |

**原始格式示例：**
```
doc_id	step	entity	action	location
1	0	John	entered	the kitchen
1	1	John	moved	to the living room
```

**转换策略：**
- 过程步骤作为状态追踪序列
- 追踪每个实体的位置/状态变化
- 提取最终状态作为答案
- 映射到 T2 状态追踪

---

### 17. TRIP (TripCraft)

| 属性 | 值 |
|------|-----|
| 来源 | Microsoft, ACL 2025 |
| 原始格式 | JSONL |
| 文件路径 | 需要申请访问 |
| 任务类型 | T2, T3 |
| 转换后规模 | 待定 (需申请访问) |

**说明：** 该数据集需要向作者发送邮件申请访问权限。

---

### 18. bAbI

| 属性 | 值 |
|------|-----|
| 来源 | Facebook AI Research |
| 原始格式 | TXT |
| 文件路径 | `data/bAbI/tasks_1-20_v1-2/` |
| 任务类型 | T2 |
| 转换后规模 | 未下载 (仅有源码) |

**说明：** 该目录包含 bAbI 任务的源码仓库，需要另行下载数据文件。

---

## 数据规模汇总

| 数据集 | 任务类型 | 训练集 | 开发集 | 测试集 | 总计 |
|--------|----------|--------|--------|--------|------|
| MCTACO | T1, T2 | - | 1,229 | - | 1,229 |
| UDST-DurationQA | T1 | 16,140 | - | - | 16,140 |
| TimeDial | T1 | - | 1,446 | - | 1,446 |
| TRACIE | T2 | - | - | 1,174 | 1,174 |
| situated_gen | T2 | 5,641 | - | - | 5,641 |
| DROP | T1 | 77,400 | - | 9,536 | 86,936 |
| TimeQA | T1 | 3,561 | - | 422 | 3,983 |
| SocialIQA | T3 | 33,410 | 1,954 | 2,021 | 37,385 |
| CosmosQA | T3 | 25,262 | 3,863 | 6,963 | 36,088 |
| PIQA | T5 | 58,129 | 1,838 | 3,084 | 63,051 |
| LongBench | T4 | - | - | 5,924 | 5,924 |
| ATOMIC | T5 | - | - | 5,000 | 5,000 |
| NarrativeQA | T4 | - | - | 10,557 | 10,557 |
| Winogrande | T5 | - | - | 9,248 | 9,248 |
| QASPer | T4 | - | - | 2,135 | 2,135 |
| ProPara | T2 | 385 | 43 | 54 | 482 |
| TRIP | T2, T3 | - | - | 待定 | - |
| **总计** | | 219,928 | 10,373 | 46,108 | **276,409** |

---

## 评测方法

### 三层评测体系

框架实现了三层评测机制：

#### 1. Answer-Level (答案层)
- **指标**: Exact Match (EM), F1 Score
- **适用任务**: T1, T4, T5
- **评价方式**: 直接比较生成答案与参考答案

```python
from arch.evaluation import AnswerLevelEvaluator

evaluator = AnswerLevelEvaluator()
result = evaluator.evaluate(sample, predicted_answer)
```

#### 2. State-Level (状态层)
- **指标**: State Accuracy, Consistency
- **适用任务**: T2, T3
- **评价方式**: 追踪状态序列的正确性

```python
from arch.evaluation import StateLevelEvaluator

evaluator = StateLevelEvaluator()
result = evaluator.evaluate(sample, predicted_state)
```

#### 3. Chain-Level (链条层)
- **指标**: Chain Accuracy, Step Precision/Recall
- **适用任务**: T2, T3
- **评价方式**: 评估完整推理链的连贯性

```python
from arch.evaluation import ChainLevelEvaluator

evaluator = ChainLevelEvaluator()
result = evaluator.evaluate(sample, predicted_chain)
```

### 运行评测

```python
from arch import TemporalBenchmarkEvaluator, generate_tasks

# 生成任务
tasks = generate_tasks(dataset_name="all")

# 初始化评测器
evaluator = TemporalBenchmarkEvaluator(tasks)

# 运行评测
results = evaluator.evaluate_all()

# 输出结果
evaluator.print_summary(results)
```

---

## 附录：数据集文件位置

```
data/
├── MCTACO/
│   └── dataset/
│       ├── dev_3783.tsv
│       └── test_9442.tsv
├── UDST-DurationQA/
│   └── data/
│       ├── train.tsv
│       ├── dev.tsv
│       └── test.tsv
├── TimeDial/
│   └── test.json
├── tracie/
│   └── data/iid/
│       ├── tracie_train.txt
│       └── tracie_test.txt
├── situated_gen/
│   └── data/
│       ├── train.jsonl
│       ├── dev.jsonl
│       └── test.jsonl
├── DROP/
│   ├── train.parquet
│   └── validation.parquet
├── TimeQA/
│   └── dataset/
│       ├── annotated_train.json
│       └── annotated_dev.json
├── SocialIQA/
│   └── *.jsonl
├── CosmosQA/
│   └── data/
│       └── *.jsonl
├── PIQA/
│   ├── tests.jsonl
│   └── physicaliqa-train-dev/
├── LongBench/
│   └── data/
│       └── *.jsonl
├── ATOMIC/
│   └── system_eval/
│       └── test.tsv  (latin-1 编码)
├── NarrativeQA/
│   └── qaps.csv
├── Winogrande/
│   └── winogrande_{xs,s,m,l,xl,debiased}/
│       └── {train,test,validation}-*-of-*.parquet
├── qasper/
│   └── qasper-{train,dev,test}-v0.3.json
├── ProPara/
│   └── data/emnlp18/
│       └── grids.v1.{train,dev,test}.tsv
└── TRIP/  (需要申请访问)
```

---

*文档生成时间: 2026-03-29*
