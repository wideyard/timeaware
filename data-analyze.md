# TimeAware 项目数据集综合分析报告

**生成时间**: 2026年3月30日  
**最后更新**: 2026年3月30日  
**项目**: Temporal World Modeling (时间感知世界建模)  
**数据集总数**: 20个  
**转换后总样本数**: 177,431+

---

## 一、项目概述

### 1.1 核心框架

本项目旨在构建 **Temporal World Modeling** 统一评估框架，将多个现有数据集映射到五种时间感知任务类型：

| 任务类型 | 描述 | 核心能力 |
|---------|------|---------|
| **T1** | 时间计算 (Temporal Calculation) | Duration, Offset, Ordering |
| **T2** | 状态追踪 (State Tracking) | Location, Status 变化追踪 |
| **T3** | 并发冲突 (Concurrency) | Space Conflict, Resource Conflict |
| **T4** | 长期记忆 (Long-term Memory) | 跨长文本信息检索 |
| **T5** | 反事实推理 (Counterfactual) | Rule Perturbation, 规则变换 |

### 1.2 统一数据格式

所有数据集转换为统一的 `TemporalSample` 格式：

```json
{
  "task": "T1",              // 任务类型 (T1-T5)
  "sub_task": "T1-1",        // 子任务类型
  "context": "...",          // 上下文/对话历史
  "delta_t": "...",          // 时间推进量
  "event": "...",            // 事件描述
  "query": "...",            // 问题
  "answer": "...",           // 答案 (待模型填写)
  "state": {...},            // 状态信息 (可选)
  "reasoning": "...",        // 推理过程 (可选)
  "original_id": "..."       // 原始数据ID
}
```

---

## 二、数据集全景分析

### 2.1 数据集分布概览

```
总计: 20 个数据集
├── 核心时间推理数据集: 7 个 (★★★★★)
├── 时间感知应用数据集: 2 个 (★★★★☆)
├── 过程/状态追踪数据集: 1 个 (★★★★★)
├── 通用阅读理解/QA: 5 个 (☆☆☆★☆)
└── 其他推理数据集: 5 个 (★★☆☆☆)
```

### 2.2 README 文件覆盖情况

| 状态 | 数量 | 数据集 |
|------|------|--------|
| **有 README** | 17 | ATOMIC, CosmosQA, HellaSwag, LongBench, MCTACO, ProPara, TRIP, TempReason, TimeQA, UDST-DurationQA, UDS_T_v1.0, qasper, situated_gen, timedial, tracie |
| **无 README** | 5 | DROP, PIQA, narrative-qa, SocialIQA, winogrande |

---

## 三、按时间感知能力分类详解

### 3.1 ★★★★★ 核心时间推理数据集 (Category 1)

#### 3.1.1 MCTACO
| 属性 | 值 |
|------|-----|
| **来源** | Google Research, EMNLP 2019 |
| **论文** | "Going on a vacation" takes longer than "Going for a walk": A Study of Temporal Commonsense Understanding |
| **任务类型** | T1, T2 |
| **数据规模** | Dev: 3,783 / Test: 9,442 |
| **格式** | TSV |
| **路径** | `data/MCTACO/dataset/` |
| **核心能力** | 事件持续时间、时间顺序、稳态性判断 |

**数据格式示例：**
```tsv
sentence	question	answer	label	category
"John turned on the light."	"Is it bright in the room?"	"yes"	1	temporal
"Islam later emerged as majority religion..."	"Is Islam still the majority religion?"	"it sometimes was"	yes	Stationarity
```

**时间属性类型：**
- Event Duration (事件持续时间)
- Stationarity (稳态性)
- Typical Time (典型时间)
- Frequency (频率)
- Event Ordering (事件顺序)

---

#### 3.1.2 TimeQA
| 属性 | 值 |
|------|-----|
| **来源** | UCSB NLP, NeurIPS 2021 (Dataset Track) |
| **论文** | Time-Sensitive Question Answering |
| **任务类型** | T1 |
| **数据规模** | Train: 3,561 / Dev: 422 / Test: ✓ |
| **格式** | JSON |
| **路径** | `data/TimeQA/dataset/` |
| **核心能力** | 时间敏感阅读理解 |

**数据格式示例：**
```json
{
  "index": "/wiki/Knox_Cunningham#P39",
  "paras": ["In the 1955 general election..."],
  "questions": [
    [["May 1955", "Apr 1956"], 
     [{"para": 7, "from": 64, "end": 99, "answer": "Ulster Unionist MP"}]
    ]
  ]
}
```

**版本划分：**
- `annotated_train/dev/test.json` — 人工标注版本（推荐使用）
- `train.easy/hard.json` — 模板合成版本

---

#### 3.1.3 TimeDial
| 属性 | 值 |
|------|-----|
| **来源** | UIUC & Allen AI, ACL 2021 |
| **论文** | TimeDial: Temporal Commonsense Understanding in Dialog |
| **任务类型** | T1 |
| **数据规模** | Test: 1,104 条对话实例 |
| **格式** | JSON |
| **路径** | `data/timedial/test.json` |
| **核心能力** | 对话中的时间常识推理 |

**数据格式示例：**
```json
{
  "id": 1,
  "conversation": ["Hello!", "Hi, what time is it?", "It's around 9:15 AM."],
  "correct1": "9:15 AM",
  "correct2": "nine fifteen am",
  "incorrect1": "9:00 AM",
  "incorrect2": "ten fifteen AM"
}
```

**特点：**
- 多选题形式（完形填空）
- 涉及时间表达式歧义处理
- 对话场景下的时间推理

---

#### 3.1.4 TRACIE
| 属性 | 值 |
|------|-----|
| **来源** | UMass, NAACL 2021 |
| **论文** | TRACIE: Temporal Reasoning on Implicit Events |
| **任务类型** | T2 |
| **数据规模** | Train: 1,174 / Test: ✓ |
| **格式** | TXT (NLI格式) |
| **路径** | `data/tracie/data/iid/` |
| **核心能力** | 隐式事件的时间推理 |

**数据格式示例：**
```
event: Chad looked for his baseball cap starts after he got off the ride 
story: Chad had gone to an amusement park...	
answer: positive
```

**划分版本：**
- `iid/` — IID 划分
- `uniform-prior/` — 均匀先验划分
- `matres/` — MATRES 格式数据

---

#### 3.1.5 UDS_T_v1.0
| 属性 | 值 |
|------|-----|
| **来源** | EMNLP 2019 |
| **论文** | Universal Datasets for Temporal Relations |
| **任务类型** | T1, T2 |
| **数据规模** | 完整数据集 |
| **格式** | TSV (25列) |
| **路径** | `data/UDS_T_v1.0/` |
| **核心能力** | 细粒度时间关系抽取 |

**数据列：**
- Split, Event1/2.ID, Pred1/2.*
- Duration, Beg, End
- Relation.Confidence 等25列

---

#### 3.1.6 UDST-DurationQA
| 属性 | 值 |
|------|-----|
| **来源** | UMass & Stanford, LREC 2022 |
| **任务类型** | T1 |
| **数据规模** | Train: 16,140 / Dev: 1,000 / Test: 1,000 |
| **格式** | TSV |
| **路径** | `data/UDST-DurationQA/data/` |
| **核心能力** | 事件持续时间问答 |

**数据格式示例：**
```tsv
context	question	answer	label
"The concert started at 7pm and lasted 2 hours."	"When did the concert end?"	"9pm"	yes
```

**特点：**
- 从 UDS-T 改造而来
- 专注事件持续时间推理

---

#### 3.1.7 TempReason
| 属性 | 值 |
|------|-----|
| **来源** | ACL 2023 |
| **论文** | Towards Benchmarking and Improving the Temporal Reasoning Capability of Large Language Models |
| **任务类型** | T1, T2 |
| **数据规模** | Train: ~361 MB / Val: ~107 MB / Test: ~124 MB |
| **格式** | JSONL |
| **路径** | `data/TempReason/tempreason_data/` |
| **核心能力** | 全面时间推理能力评估 |
| **状态** | ✅ 已下载 |

**数据文件：**
| 文件 | 大小 | 说明 |
|------|------|------|
| train_l1.json | 63.32 MB | Level 1 训练集 |
| train_l2.json | 157.89 MB | Level 2 训练集 |
| train_l3.json | 140.17 MB | Level 3 训练集 |
| val_l1.json | 0.63 MB | Level 1 验证集 |
| val_l2.json | 55.90 MB | Level 2 验证集 |
| val_l3.json | 51.06 MB | Level 3 验证集 |
| test_l1.json | 0.63 MB | Level 1 测试集 |
| test_l2.json | 64.35 MB | Level 2 测试集 |
| test_l3.json | 59.30 MB | Level 3 测试集 |
| test_l1_future.json | 0.31 MB | Level 1 未来测试集 |

**数据格式示例：**
```json
{
  "question": "What is the time 1 year and 7 month after Mar, 1873",
  "date": "March 26, 1873",
  "text_answers": {"text": ["Oct, 1874"]},
  "id": "0",
  "context": ""
}
```

**特点：**
- 提供训练脚本 (`tempreason_train.sh`)
- 支持 T5 模型微调
- 包含 TSRL 训练代码
- 三个难度级别 (L1/L2/L3) 对应不同复杂度的时间推理

---

### 3.2 ★★★★☆ 时间感知应用数据集 (Category 2)

#### 3.2.1 TRIP (TripCraft)
| 属性 | 值 |
|------|-----|
| **来源** | Microsoft, ACL 2025 (Main Track) |
| **论文** | TripCraft: A Benchmark for Spatio-Temporally Fine Grained Travel Planning |
| **任务类型** | T2, T3 |
| **数据规模** | 需申请访问 |
| **格式** | JSONL |
| **路径** | `data/TRIP/` |
| **核心能力** | 时空精细化旅行规划 |

**评估指标：**
- Temporal Meal Score — 餐饮时间合理性
- Temporal Attraction Score — 景点时间安排
- Spatial Score — 空间移动合理性
- Ordering Score — 活动顺序合理性
- Persona Score — 个性化程度

**申请方式：**
发送邮件至 AcadGrants@service.microsoft.com

---

#### 3.2.2 situated_gen
| 属性 | 值 |
|------|-----|
| **来源** | Allen AI, NeurIPS 2023 |
| **论文** | SituatedGen: Generative Commonsense with Temporal/Geographical Context |
| **任务类型** | T2 |
| **数据规模** | Train: 5,641 / Dev: 1,407 / Test: 1,220 |
| **格式** | JSONL |
| **路径** | `data/situated_gen/data/` |
| **核心能力** | 基于情境的常识生成 |

**数据格式示例：**
```json
{
  "keywords": ["December", "365 days", "every 24 hours"],
  "statement": "A year has 365 days and December is one of its months.",
  "ids": "...",
  "keywords_pos": [...],
  "statements": [...]
}
```

**时间相关内容：**
- 包含时间关键词: "365 days", "every 24 hours", "December", "March"
- 地理位置与时间上下文组合

---

### 3.3 ★★★★★ 过程/状态追踪数据集 (Category 3)

#### 3.3.1 ProPara
| 属性 | 值 |
|------|-----|
| **来源** | AI2, EMNLP 2018 |
| **论文** | ProPara: Procedure comprehension |
| **任务类型** | T2 |
| **数据规模** | Train: 385 / Dev: 43 / Test: 54 |
| **格式** | TSV |
| **路径** | `data/ProPara/data/emnlp18/` |
| **核心能力** | 过程文本实体状态追踪 |

**数据格式示例：**
```tsv
7	SID	PARTICIPANTS	magma	lava	new rock
7		PROMPT: What causes a volcano to erupt?
7	state1		deep in the earth	-	-
7	event1	Magma rises from deep in the earth.
7	state2		deep in the earth	-	-
```

**状态追踪维度：**
- 实体位置变化 (Location)
- 实体状态变化 (Status)
- 过程步骤关系 (Steps)

---

### 3.4 ☆★★☆☆ 通用阅读理解/QA数据集 (Category 4)

#### 3.4.1 LongBench
| 属性 | 值 |
|------|-----|
| **来源** | THUDM |
| **论文** | LongBench: A Bilingual Benchmark for Long Context Understanding |
| **任务类型** | T4 |
| **数据规模** | Test: 4,750 samples (21 tasks) |
| **格式** | JSONL |
| **路径** | `data/LongBench/data/` |
| **核心能力** | 长上下文理解 |

**任务组成：**
| 子集 | 样本数 | 平均长度 |
|------|--------|---------|
| narrativeqa | 200 | 47,507 |
| qasper | 200 | 9,291 |
| hotpotqa | 200 | 9,231 |
| gov_report | 200 | 10,145 |
| ... | ... | ... |

**数据格式：**
```json
{
  "input": "问题",
  "context": "长文本...",
  "answers": ["答案列表"],
  "length": 127309,
  "dataset": "narrativeqa",
  "language": "en"
}
```

---

#### 3.4.2 qasper
| 属性 | 值 |
|------|-----|
| **来源** | Allen AI, NAACL 2021 |
| **论文** | QASPER: Dataset for Question Answering on NLP Papers |
| **任务类型** | T4 |
| **数据规模** | Train: 1,073 / Dev: 505 / Test: 557 |
| **格式** | JSON |
| **路径** | `data/qasper/` |
| **核心能力** | 论文阅读理解 |

**数据结构：**
```json
{
  "id": "arxiv_paper_id",
  "title": "Paper Title",
  "abstract": "...",
  "full_text": {...},
  "qas": [{
    "question": "What method was proposed?",
    "answers": [{"answer": "...", "answer_start": 123}]
  }]
}
```

---

#### 3.4.3 DROP
| 属性 | 值 |
|------|-----|
| **来源** | AI2, ACL 2019 |
| **论文** | DROP: Discrete Reasoning Over Paragraphs |
| **任务类型** | T1 |
| **数据规模** | Train: 77,400 / Validation: 9,536 |
| **格式** | Parquet |
| **路径** | `data/DROP/` |
| **核心能力** | 离散数值推理 |

**数据格式示例：**
```python
{
  "passage": "The battle lasted from 1861 to 1865.",
  "question": "How long did the battle last?",
  "answers_spans": {
    "spans": ["4 years"],
    "types": ["duration"]
  }
}
```

**特点：**
- 包含数值/时间计算问题
- 需要从 answers_spans 提取答案

---

#### 3.4.4 CosmosQA
| 属性 | 值 |
|------|-----|
| **来源** | EMNLP 2019 |
| **任务类型** | T3 |
| **数据规模** | Train: 25,262 / Valid: 2,986 / Test: 6,963 |
| **格式** | CSV |
| **路径** | `data/CosmosQA/data/` |
| **核心能力** | 常识推理 |

**数据格式示例：**
```csv
id,context,question,answer0,answer1,answer2,answer3,label
train_1,"The cake was eaten...","Why?",...
```

---

#### 3.4.5 narrative-qa
| 属性 | 值 |
|------|-----|
| **来源** | Google, TACL 2018 |
| **任务类型** | T4 |
| **数据规模** | 已整合入 LongBench |
| **路径** | `data/narrative-qa/` (空目录) |
| **核心能力** | 故事理解 |

**说明：**
- 原始 narrative-qa 数据已整合在 LongBench 中 (`narrativeqa.jsonl`)
- 单独目录为空

---

### 3.5 ★★☆☆☆ 其他推理数据集 (Category 5)

#### 3.5.1 ATOMIC
| 属性 | 值 |
|------|-----|
| **来源** | Allen AI, AAAI 2021 |
| **论文** | ATOMIC: If-Then Reasoning Knowledge Graph |
| **任务类型** | T3, T5 |
| **数据规模** | Train: 202,272 / Dev: ✓ / Test: ✓ |
| **格式** | CSV |
| **路径** | `data/ATOMIC/` |
| **核心能力** | If-Then 常识推理 |

**数据格式示例：**
```csv
event,oEffect,oReact,oWant,xAttr,xEffect,xIntent,xNeed,xReact,xWant
PersonX uses PersonX's ___ to obtain,["annoyed"],...
```

**推理维度：**
- oEffect: 他人反应效应
- oReact: 他人的情绪反应
- oWant: 他人的需求
- xAttr: PersonX 的属性
- xEffect: PersonX 的效应
- xIntent: PersonX 的意图
- xNeed: PersonX 的需求
- xReact: PersonX 的情绪
- xWant: PersonX 的需求

---

#### 3.5.2 HellaSwag
| 属性 | 值 |
|------|-----|
| **来源** | ACL 2019 |
| **论文** | HellaSwag: Commonsense Reasoning about Activity Sequences |
| **任务类型** | T5 |
| **数据规模** | Train: 39,905 / Val: ✓ / Test: ✓ |
| **格式** | JSONL |
| **路径** | `data/HellaSwag/data/` |
| **核心能力** | 活动序列完成 |

**数据格式示例：**
```json
{
  "activity_label": "Removing ice from car",
  "ctx": "Then, the man writes over the snow...",
  "label": 3,
  "endings": ["the man adds wax...", "a person boards a ski lift..."]
}
```

---

#### 3.5.3 SocialIQA
| 属性 | 值 |
|------|-----|
| **来源** | ICLR 2020 |
| **论文** | SocialIQA: Commonsense Reasoning about Social Interactions |
| **任务类型** | T3 |
| **数据规模** | Train: 33,410 / Dev: 1,954 |
| **格式** | JSONL |
| **路径** | `data/SocialIQA/` |
| **核心能力** | 社会常识推理 |

**数据格式示例：**
```json
{
  "context": "Alex borrowed a book from Sam.",
  "question": "What does Sam need to do next?",
  "answerA": "Give the book to Alex",
  "answerB": "Read the book",
  "answerC": "Return the book"
}
```

---

#### 3.5.4 PIQA
| 属性 | 值 |
|------|-----|
| **来源** | NeurIPS 2019 |
| **论文** | PIQA: Physical Interaction QA |
| **任务类型** | T5 |
| **数据规模** | Train: 16,113 / Dev: 1,838 / Test: 3,084 |
| **格式** | JSONL |
| **路径** | `data/PIQA/` |
| **核心能力** | 物理常识推理 |

**数据格式示例：**
```json
{
  "goal": "To make a cake rise, you can",
  "sol1": "Put it in the oven",
  "sol2": "Put it in the fridge"
}
```

---

#### 3.5.5 winogrande
| 属性 | 值 |
|------|-----|
| **来源** | Allen AI, NeurIPS 2020 |
| **论文** | Winogrande: Adversarial Winograd Schema Challenge |
| **任务类型** | T5 |
| **数据规模** | 总计 81,442 样本（6个子集） |
| **格式** | Parquet |
| **路径** | `data/winogrande/` |
| **状态** | ✅ **已下载** |
| **核心能力** | 代词指代推理 |

**子集分布：**
| 子集 | Train | Validation | Test | 总计 |
|------|-------|------------|------|------|
| winogrande_xs | 160 | 1,267 | 1,767 | 3,194 |
| winogrande_s | 640 | 1,267 | 1,767 | 3,674 |
| winogrande_m | 2,558 | 1,267 | 1,767 | 5,592 |
| winogrande_l | 10,234 | 1,267 | 1,767 | 13,268 |
| winogrande_xl | 40,398 | 1,267 | 1,767 | 43,432 |
| winogrande_debiased | 9,248 | 1,267 | 1,767 | 12,282 |

**数据格式示例：**
```json
{
  "sentence": "John moved the couch from the garage to the backyard to create space. The _ is small.",
  "option1": "garage",
  "option2": "backyard",
  "answer": "1"
}
```

**说明：**
- `winogrande_debiased` 是最常用的子集，已去偏差
- `winogrande_xl` 是最大子集，适合大规模训练
- 所有子集共享相同的验证集和测试集

---

## 四、数据转换状态汇总

### 4.1 已完成转换的数据集

| 数据集 | 原始格式 | 转换后 | 样本数 | Task | 答案状态 |
|--------|----------|--------|--------|------|---------|
| TimeQA (annotated) | JSON | JSONL | 19,488 | T1 | ✅ 已填充 |
| DROP | Parquet | JSONL | 7,115 | T1 | ✅ 已填充 |
| ProPara | TSV | JSONL | 2,639 | T2 | ✅ 已填充 |
| CosmosQA | CSV | JSONL | 25,262 | T3 | ✅ |
| ATOMIC (fixed) | CSV | JSONL | 19,934 | T3 | ✅ 已过滤 |
| NarrativeQA | Parquet | JSONL | 5,000 | T4 | ✅ 已填充 |
| Winogrande | Parquet | JSONL | 320 | T5 | ✅ |
| HellaSwag | JSONL | JSONL | 59,950 | T5 | ✅ |
| MCTACO | TSV | JSONL | 1,229 | T1 | ✅ 已填充 |
| SocialIQA | JSONL | JSONL | 33,410 | T3 | ✅ |
| PIQA | JSONL | JSONL | 3,084 | T5 | ✅ |

**总计**: 177,431 个样本 (来自 CONVERSION_REPORT)

### 4.2 待处理数据集

| 数据集 | 位置 | 状态 | 建议 |
|--------|------|------|------|
| TimeDial | `data/timedial/test.json` | 待转换 | T1 时间推理 |
| TempReason | `data/TempReason/tempreason_data/` | ✅已下载 | T1/T2 |
| TRACIE | `data/tracie/` | 已有原始数据可用 | T2 |
| UDST-DurationQA | `data/UDST-DurationQA/` | 已有原始数据可用 | T1 |
| UDS_T_v1.0 | `data/UDS_T_v1.0/` | 已有原始数据可用 | T1/T2 |
| situated_gen | `data/situated_gen/` | 已有原始数据可用 | T2 |
| TRIP | `data/TRIP/` | 需申请访问 | T2/T3 |
| winogrande | `data/winogrande/` | **空目录** | 需重新下载 |

---

## 五、数据统计总览

### 5.1 按任务类型分布

| Task | 描述 | 数据集数 | 总样本数 |
|------|------|---------|---------|
| T1 | 时间计算 | 8 | ~28,000+ |
| T2 | 状态追踪 | 5 | ~12,000+ |
| T3 | 并发冲突 | 3 | ~78,000+ |
| T4 | 长期记忆 | 3 | ~18,000+ |
| T5 | 反事实推理 | 3 | ~63,000+ |

### 5.2 按数据格式分布

| 格式 | 数据集数 | 数据集列表 |
|------|---------|-----------|
| JSONL | 8 | HellaSwag, LongBench, PIQA, SocialIQA, situated_gen |
| JSON | 5 | TimeQA, TimeDial, qasper, TRIP |
| TSV | 5 | MCTACO, ProPara, TRACIE, UDS_T_v1.0, UDST-DurationQA |
| CSV | 2 | ATOMIC, CosmosQA |
| Parquet | 1 | DROP |
| TXT | 1 | winogrande |

### 5.3 按会议/年份分布

| 会议 | 数据集 |
|------|--------|
| ACL 2025 | TRIP |
| NeurIPS 2023 | situated_gen, LongBench |
| ACL 2023 | TempReason |
| LREC 2022 | UDST-DurationQA |
| NeurIPS 2021 | TimeQA, PIQA |
| ACL 2021 | TimeDial |
| NAACL 2021 | qasper, TRACIE |
| EMNLP 2019 | MCTACO, CosmosQA, UDS_T_v1.0 |
| NeurIPS 2019 | PIQA, ATOMIC |
| ACL 2019 | DROP, HellaSwag |
| EMNLP 2018 | ProPara |
| NeurIPS 2020 | Winogrande |

---

## 六、评测体系

### 6.1 三层评测机制

| 层级 | 指标 | 适用任务 |
|------|------|---------|
| **Answer-Level** | Exact Match, F1 Score | T1, T4, T5 |
| **State-Level** | State Accuracy, Consistency | T2, T3 |
| **Chain-Level** | Chain Accuracy, Step Precision/Recall | T2, T3 |

### 6.2 评测代码示例

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

## 七、关键发现与建议

### 7.1 核心发现

1. **时间推理数据集丰富**: 核心时间数据集有8个（MCTACO, TimeQA, TimeDial, TRACIE, UDS_T, UDST-DurationQA, TempReason, TRIP），覆盖时序推理的多个维度。

2. **数据格式多样**: 需要统一的转换流程将 TSV/CSV/JSON/Parquet 格式转换为 JSONL 标准格式。

3. **TempReason 已下载**: TempReason 数据集已成功从 HuggingFace 下载（592 MB），包含 L1/L2/L3 三个难度级别的训练/验证/测试数据。

4. **NarrativeQA 答案已填充**: NarrativeQA 的 5,000 个样本答案字段已完整填充，转换后的数据位于 `converted_data/narrativeqa.jsonl`。

5. **Winogrande 已下载**: Winogrande 数据集已成功下载（81,442 样本），包含6个子集（xs/s/m/l/xl/debiased），格式为 Parquet。

6. **最新研究进展**: TRIP (ACL 2025) 和 situated_gen (NeurIPS 2023) 代表了时空推理的最新发展方向。

### 7.2 建议优先级

**高优先级：**
1. ✅ ~~下载 TempReason 数据~~ (已完成)
2. ✅ ~~完成 NarrativeQA 答案填充~~ (已完成)
3. ✅ ~~下载 Winogrande 数据~~ (已完成)
4. 🔴 申请 TRIP 数据集访问权限

**中优先级：**
1. 验证 UDST-DurationQA 和 UDS_T 数据转换
2. 检查 ATOMIC 数据过滤正确性
3. 添加更多反事实样本 (T5)

**低优先级：**
1. 扩展 HuggingFace 上发现的新数据集
2. 实现自动评测模块优化
3. 添加更多增强后的 T2/T3 数据

### 7.3 推荐的数据集组合

| 研究方向 | 推荐数据集组合 |
|---------|---------------|
| **时间推理基准** | MCTACO + TimeQA + TimeDial + TRACIE |
| **状态追踪研究** | ProPara + TRIP + situated_gen |
| **长久记忆测试** | LongBench + qasper |
| **常识推理** | ATOMIC + CosmosQA + SocialIQA |
| **反事实研究** | PIQA + HellaSwag + Winogrande |

---

## 八、附录

### 8.1 数据集文件路径映射

```
data/
├── ATOMIC/
│   ├── v4_atomic_all.csv
│   ├── v4_atomic_trn.csv
│   ├── v4_atomic_dev.csv
│   └── v4_atomic_tst.csv
├── CosmosQA/data/
│   ├── train.csv
│   ├── valid.csv
│   └── test.jsonl
├── DROP/
│   ├── train-00000-of-00001.parquet
│   └── validation-00000-of-00001.parquet
├── HellaSwag/data/
│   ├── hellaswag_train.jsonl
│   ├── hellaswag_val.jsonl
│   └── hellaswag_test.jsonl
├── LongBench/data/
│   ├── narrativeqa.jsonl
│   ├── qasper.jsonl
│   └── ... (21 tasks)
├── MCTACO/dataset/
│   ├── dev_3783.tsv
│   └── test_9442.tsv
├── PIQA/
│   ├── tests.jsonl
│   └── physicaliqa-train-dev/
├── ProPara/data/emnlp18/
│   ├── grids.v1.train.tsv
│   ├── grids.v1.dev.tsv
│   └── grids.v1.test.tsv
├── SocialIQA/
│   ├── train.jsonl
│   ├── dev.jsonl
│   └── train-labels.lst
├── TempReason/
│   ├── run_seq2seq_qa.py
│   └── trlx/
├── TimeQA/dataset/
│   ├── annotated_train.json
│   ├── annotated_dev.json
│   └── train.easy/hard.json
├── TimeDial/
│   └── test.json
├── TRACIE/data/
│   ├── iid/
│   ├── uniform-prior/
│   └── matres/
├── TRIP/
│   ├── agents/
│   ├── evaluation/
│   └── tools/
├── UDS_T_v1.0/
│   └── time_eng_ud_v1.2_2015_10_30.tsv
├── UDST-DurationQA/data/
│   ├── train.tsv
│   ├── dev.tsv
│   └── test.tsv
├── qasper/
│   ├── qasper-train-v0.3.json
│   ├── qasper-dev-v0.3.json
│   └── qasper-test-v0.3.json
├── situated_gen/data/
│   ├── train.jsonl
│   ├── dev.jsonl
│   └── test.jsonl
└── winogrande/   (空目录)
```

### 8.2 引用格式

请参阅各数据集 README 文件中的 BibTeX 引用格式。

---

**报告结束**

*本报告由数据分析系统自动生成，数据来源包括数据集 README 文件、项目文档 CONVERSION_REPORT.md、DATA_TRANSFORMATION.md 和 data_.md，以及数据集文件结构扫描结果。*