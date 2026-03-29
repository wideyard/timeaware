# 数据转换报告

## 一、概述

本文档记录了将多个数据集转换为 **Temporal World Modeling** 统一格式的过程。

### 目标格式

**输入格式（统一）**:
```
[Context / 对话历史]
[时间推进 Δt]
[事件 a_t]
[问题 Query]
```

**输出格式（强约束）**:
```json
{
  "answer": "...",
  "state": {...},
  "reasoning": "..."
}
```

### 三种转换方法

| 类型 | 方法 | 用途 |
|------|------|------|
| Temporalization | 加时间维度 | T1/T2 |
| State Structuring | 提取状态 | T2/T3 |
| Rule Perturbation | 改规则 | T5 |

---

## 二、转换结果汇总

| 数据集 | 原始格式 | 转换后 | 样本数 | Task | 答案 |
|--------|----------|--------|--------|------|------|
| TimeQA (annotated) | JSON | JSONL | 19,488 | T1 | ✅ 已填充 |
| DROP | Parquet | JSONL | 7,115 | T1 | ✅ 已填充 |
| ProPara | TSV | JSONL | 2,639 | T2 | ✅ 已填充 |
| CosmosQA | CSV | JSONL | 25,262 | T3 | ✅ |
| ATOMIC (fixed) | CSV | JSONL | 19,934 | T3 | ✅ 已过滤 |
| NarrativeQA | Parquet | JSONL | 5,000 | T4 | - |
| Winogrande | Parquet | JSONL | 320 | T5 | ✅ |
| HellaSwag | JSONL | JSONL | 59,950 | T5 | ✅ |
| MCTACO | TSV | JSONL | 1,229 | T1 | ✅ 已填充 |
| SocialIQA | JSONL | JSONL | 33,410 | T3 | ✅ |
| PIQA | JSONL | JSONL | 3,084 | T5 | ✅ |

**总计**: 177,431 个样本

---

## 三、各数据集转换详情

### 3.1 TimeQA → T1 时间计算

**原始格式** (annotated_*.json):
```json
{
  "index": "/wiki/Knox_Cunningham#P39",
  "paras": ["In the 1955 general election..."],
  "questions": [
    [["May 1955", "Apr 1956"], [{"para": 7, "from": 64, "end": 99, "answer": "Ulster Unionist MP for South Antrim"}]]
  ]
}
```

**转换方法**: Temporalization - 从 annotated 文件提取时间范围和答案

**转换后**:
```json
{
  "task": "T1",
  "sub_task": "T1-1",
  "context": "In the 1955 general election, Cunningham was chosen as the new Ulster Unionist MP for South Antrim...",
  "delta_t": "从 May 1955 到 Apr 1956",
  "event": "时间推理",
  "query": "What was the answer from May 1955 to Apr 1956?",
  "answer": "Ulster Unionist MP for South Antrim",
  "state": {"type": "temporal_position"},
  "original_id": "/wiki/Knox_Cunningham#P39"
}
```

**说明**: 使用 annotated_*.json 文件（包含答案），而非 easy/hard 版本。

---

### 3.2 DROP → T1 时间计算

**原始格式**: Parquet
```python
{
  "passage": "To start the season, the Lions traveled south...",
  "question": "How many points did the buccaneers need to tie in the first?",
  "answers_spans": {"spans": ["3"], "types": ["number"]}
}
```

**转换方法**: Temporalization - 从 answers_spans.spans 提取答案

**转换后**:
```json
{
  "task": "T1",
  "sub_task": "T1-2",
  "context": "To start the season, the Lions traveled south...",
  "delta_t": "计算中",
  "event": "数值推理",
  "query": "How many points did the buccaneers need to tie in the first?",
  "answer": "3",
  "state": {"type": "numerical_temporal"},
  "original_id": "f16c0ee7-f131-4a8b-a6ac-4d275ea68066"
}
```

**说明**: 只保留时间/数值相关问题，从 answers_spans 提取答案。

---

### 3.3 ProPara → T2 状态更新

**原始格式** (TSV):
```
7	SID	PARTICIPANTS	magma	lava	new rock
7		PROMPT: What causs a volcano to erupt?	-=====	-=====	-=====
7	state1		deep in the earth	-	-
7	event1	Magma rises from deep in the earth.
7	state2		deep in the earth	-	-
```

**转换方法**: State Structuring - 提取实体状态变化到 answer 字段

**转换后**:
```json
{
  "task": "T2",
  "sub_task": "T2-1",
  "context": "过程: What causs a volcano to erupt?\n步骤1: Magma rises from deep in the earth.\n步骤2: The magma goes into volcanos.",
  "delta_t": "步骤 1 到 2",
  "event": "Magma rises from deep in the earth.",
  "query": "在 步骤 1 到 2 后，实体状态是什么？",
  "answer": "magma: , lava: deep in the earth, new rock: -",
  "state": {"magma": "", "lava": "deep in the earth", "new rock": "-"},
  "reasoning": "从状态 ['', 'deep in the earth', '-', '-'] 变化到 ['', 'deep in the earth', '-', '-']",
  "original_id": "What causs a volcano to erupt?"
}
```

**说明**: 将 state 字段格式化为 answer 字符串，便于训练。

---

### 3.4 CosmosQA → T3 并发冲突

**原始格式** (CSV):
```
id,context,question,answer0,answer1,answer2,answer3,label
3Q9SPIIRWJKVQ824...,Good Old War...,"In the future, will this person...","None of the above...","This person likes music...",...,1
```

**转换方法**: State Structuring - 用于检测情境冲突

**转换后**:
```json
{
  "task": "T3",
  "sub_task": "T3-1",
  "context": "Good Old War and person L : I saw both of these bands Wednesday night...",
  "delta_t": "同一时间点",
  "event": "分析情境",
  "query": "In the future , will this person go to see other bands play ?",
  "answer": "This person likes music and likes to see the show , they will see other bands play .",
  "state": {"type": "commonsense_reasoning"},
  "original_id": "3Q9SPIIRWJKVQ824..."
}
```

---

### 3.5 Winogrande → T5 反事实

**原始格式** (Parquet):
```
sentence: "Ian volunteered to eat Dennis's menudo because _ enjoyed eating intestine."
option1: "Ian"
option2: "Dennis"
answer: 1
```

**转换方法**: Rule Perturbation - 创建反事实版本

**转换后**:
```json
{
  "task": "T5",
  "sub_task": "T5-1",
  "context": "Ian volunteered to eat Dennis's menudo because [BLANK] enjoyed eating intestine.",
  "delta_t": "当前情境",
  "event": "推理",
  "query": "谁[BLANK]?",
  "answer": "Dennis",
  "state": {"type": "winograd"},
  "original_id": "winogrande_0"
}
```

**反事实版本** (T5-2):
```json
{
  "task": "T5",
  "sub_task": "T5-2",
  "context": "Ian volunteered to eat Dennis's menudo despite [BLANK] enjoyed eating intestine. (contrary to expectation)",
  "delta_t": "反事实情境",
  "event": "反事实推理",
  "query": "谁[BLANK]?",
  "answer": "Ian",
  "state": {"type": "counterfactual", "modified": true},
  "original_id": "winogrande_cf_0"
}
```

---

### 3.6 HellaSwag → T5 反事实

**原始格式**: JSONL

**转换方法**: Rule Perturbation - 测试物理常识推理

**特点**:
- 活动结尾预测
- 用于测试模型对物理世界规则的理解
- 转换为 T5-3 (Physical commonsense)

---

## 四、转换脚本使用说明

### 运行转换

```bash
python convert_data.py
```

### 输出文件

转换后的文件保存在 `converted_data/` 目录下:

```
converted_data/
├── timeqa_train.jsonl   # T1 时间推理 (答案已填充)
├── timeqa_dev.jsonl     # T1 时间推理 (答案已填充)
├── timeqa_test.jsonl    # T1 时间推理 (答案已填充)
├── drop.jsonl           # T1 数值推理 (答案已填充)
├── propara_fixed.jsonl  # T2 状态跟踪 (答案已填充)
├── cosmosqa.jsonl       # T3 常识推理
├── atomic_fixed.jsonl  # T3 常识推理 (已过滤不匹配答案)
├── narrativeqa.jsonl    # T4 长文本理解
├── winogrande.jsonl     # T5 Winograd
├── hellaswag.jsonl     # T5 物理常识
├── mctaco.jsonl        # T1 时间常识 (答案已填充)
├── socialiqa_train.jsonl # T3 社会常识 (答案已填充)
└── piqa.jsonl          # T5 物理常识 (答案已填充)
```

### 数据格式

每个 JSONL 文件包含多个 JSON 对象，格式如下:

```json
{
  "task": "T1",           // 任务类型 (T1-T5)
  "sub_task": "T1-1",     // 子任务类型
  "context": "...",        // 上下文/对话历史
  "delta_t": "...",       // 时间推进
  "event": "...",         // 事件
  "query": "...",         // 问题
  "answer": "...",        // 答案 (待模型填写)
  "state": {...},         // 状态 (可选)
  "reasoning": "...",     // 推理过程 (可选)
  "original_id": "..."   // 原始数据ID
}
```

---

## 五、Task 映射表

| Task | 描述 | 数据集 | 转换方法 |
|------|------|--------|----------|
| T1-1 | Duration | TimeQA, MCTACO | Temporalization |
| T1-2 | Temporal Offset/Ordering | DROP | Temporalization |
| T1-3 | Temporal Ordering | MCTACO | Temporalization |
| T2-1 | State Tracking | ProPara | State Structuring |
| T2-2 | State Tracking | bAbI | State Structuring |
| T3-1 | Spatial/Emotional Conflict | CosmosQA, SocialIQA | State Structuring |
| T3-2 | Resource/Intent Conflict | ATOMIC (fixed) | State Structuring |
| T4-1 | Long-horizon Memory | NarrativeQA | - |
| T5-1 | Winograd Schema | Winogrande | Rule Perturbation |
| T5-2 | Counterfactual | Winogrande (反事实) | Rule Perturbation |
| T5-3 | Physical Commonsense | HellaSwag, PIQA | Rule Perturbation |

---

## 六、注意事项

1. **bAbI 数据集**: 由于 bAbI 使用 Lua 脚本生成数据，当前版本仅包含占位符示例
2. **ATOMIC 数据集**: 已过滤不匹配的答案（如 "She ran to bathroom" 与 "PersonX 'd better go" 不匹配）
3. **TimeQA**: 使用 annotated_*.json 文件（含答案），而非 easy/hard 版本
4. **DROP**: 只保留时间/数值相关问题，从 answers_spans 提取答案
5. **ProPara**: 将 state 字段格式化为 answer 字符串，便于模型训练
6. **NarrativeQA**: 答案字段待填充

---

## 七、新增数据集发现 (HuggingFace)

### 7.1 时间推理数据集

| 数据集 | HuggingFace ID | Task Type | 建议 |
|--------|---------------|-----------|------|
| UnSeenTimeQA | `nurakib/UnSeenTimeQA` | Time-sensitive QA | T1 |
| TSQA | `Time-MQA/TSQA` | Multi-task Temporal QA | T1 |
| ECT-QA | `austinmyc/ECT-QA` | Financial Temporal QA | T1 |
| Time-Bench | `ulab-ai/Time-Bench` | Temporal Reasoning | T1/T2 |
| TemporalBench | `microsoft/TemporalBench` | Video Temporal | T1 |
| Test of Time (ToT) | `baharef/ToT` | LLM Temporal | T1 |

### 7.2 事件序列数据集

| 数据集 | HuggingFace ID | Task Type | 建议 |
|--------|---------------|-----------|------|
| Event-Bench | `RUCAIBox/Event-Bench` | Event Video | T2 |
| TimeBench-event | `gagan3012/TimeBench-event` | Event Temporal | T2 |

### 7.3 时序知识图谱

| 数据集 | HuggingFace ID | Task Type | 建议 |
|--------|---------------|-----------|------|
| ICEWS14 | `linxy/ICEWS14` | Temporal KG | T2/T3 |
| GDELT | `linxy/GDELT` | Temporal KG | T2/T3 |

### 7.4 本地待处理数据集

| 数据集 | 位置 | 状态 | 建议 |
|--------|------|------|------|
| TimeDial | `data/TimeDial/test.json` | 待转换 | 1,104 条对话时间推理 |
| NarrativeQA | `data/narrative-qa/` | 待填充答案 | 5,000 条阅读理解 |

---

## 八、后续工作

1. 完成 bAbI 数据的完整转换
2. 添加更多反事实样本
3. 实现自动评测模块
4. 扩展更多数据集
5. 转换 TimeDial 数据集
6. 从 HuggingFace 下载新数据集
