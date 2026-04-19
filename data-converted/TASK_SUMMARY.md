# TimeAware Benchmark 任务定义与数据集总览

## 任务层级概览

本基准（benchmark）包含 **4 个递进的任务层级（T1–T4）**，从基础时间常识到高阶反事实推理逐步增加难度。每个层级考察模型对时间信息不同的认知能力。

| 层级 | 核心能力 | 一句话定义 | 与前一层级的区别 |
|---|---|---|---|
| **T1** | 时间信息理解与提取 | 在给定文本/对话中识别、提取时间相关事实 | — (基准层) |
| **T2** | 常识与时序推理 | 判断事件时序合理性、事件关系一致性、常识合理性 | 从"找到时间信息"升级为"判断时序是否合理/一致" |
| **T3** | 场景理解与时间推理 | 在复杂场景(长文/对话/社会情境)中进行时间相关推理 | 从"纯时序判断"升级为"在富含上下文的场景中综合推理" |
| **T4** | 反事实时间推理 | 在虚构的时序规则下推演新的结论 | 从"现实世界判断"升级为"假设世界推演" |

---

## 各层级详细说明

### T1 — 时间信息理解与提取

**定义**：给定一段包含时间信息的文本或对话，模型需要识别并提取其中的时间事实，回答与时间相关的问题。

**核心难点**：
- 时间表达式在自然语言中隐含、模糊或依赖上下文
- 部分问题需要多步时间推理（如"从1997年到2009年担任议员"→"担任了多久"）
- 时间对话中的填空题（TimeDial）允许多正确答案

**数据集**：

| 数据集 | 样本数(full) | 选项数 | 特点 |
|---|---|---|---|
| **TimeDial** | 1,446 | 4 | 对话中的时间填空，**允许多正确答案**(2选) |
| **TimeQA** | 2,674 | 4 | 长文本中的时间实体提取（人物担任职位的时间等） |
| **TempReason** | 400,000 | 4 | 日期算术推理（如"1873年3月之后的1年7个月是？"） |
| **UDST-DurationQA** | 40,102 | 2 | 时长合理性判断（如"打电话10次用了52分钟合理吗？"） |
| **MCTACO** | 3,783 | 2 | 事件持续时间合理性判断 |

**典型问题形式**：
```
TimeDial: "We've allowed <MASK> to be on the safe side." → 哪些选项填入<MASK>合理？
TimeQA:   What was the position of Ian Gibson from May 1997 to May 2001? → 从长文中提取
TempReason: What is the time 1 year and 7 month after Mar, 1873? → 日期算术
UDST:     Is it reasonable that the duration is "52 minutes"? → 时长合理性
MCTACO:   How long did it take to make the movie? → 事件时长判断
```

---

### T2 — 常识与时序推理

**定义**：给定情境描述，模型需要基于对事件时序关系的理解来判断合理性或一致性。包含三种推理类型：事件时序一致性判断、常识合理性判断、文本归因。

**核心难点**：
- 事件间的时序关系判断（starts before/after 需要理解隐含的时间方向）
- 物理和社会常识推理（判断行为合理性）
- 文本归因（哪些行支持某个论断）

**与 T1 的关键区别**：T1 的答案在文本中可以找到时间线索；T2 需要理解隐含的时序关系或运用常识来补充文本中没有直接说出的信息。

**数据集**：

| 数据集 | 样本数(full) | 选项数 | 特点 |
|---|---|---|---|
| **tracie** | 1,174 | 2 | 事件时序一致性判断（事件A是否在B之前开始？） |
| **PIQA** | 16,113 | 2 | 物理常识：哪个做法更合理 |
| **HellaSwag** | 39,905 | 4 | 事件续写：哪个后续最合理 |
| **pasta** | 8,476 | 5(含E) | 文本归因：哪几行支持论断 |

**典型问题形式**：
```
tracie:    "Chad had gone to an amusement park..." → "Chad looked for his baseball cap starts 
           after he got off the ride" 时序一致吗？ (positive/negative)
PIQA:      "When boiling butter, when it's ready, you can" → A. Pour into jar / B. Pour onto plate
HellaSwag: "Then, the man wrings out the sponge" → 哪个后续事件合理
pasta:     "Bill and Ted were best friends." → Assertion: "Bill and Ted were older teenagers." 
           哪些行支持此论断？
```

---

### T3 — 场景理解与时间推理

**定义**：在复杂的场景（长文、对话、社会情境）中，模型需要综合上下文理解并回答与时序或社会因果关系相关的问题。

**核心难点**：
- 上下文更长、更复杂（学术论文、叙事文本、社交对话）
- 需要深度的阅读理解能力
- 包含中文数据集（SI-Bench）
- 部分数据集的选项内容很长（narrative-qa）

**与 T2 的关键区别**：T2 的推理基于单段简短描述即可完成；T3 需要在复杂长上下文中理解隐含含义、社会意图和因果链。

**数据集**：

| 数据集 | 样本数(full) | 选项数 | 特点 |
|---|---|---|---|
| **SocialIQA** | 33,410 | 3 | 社会情境推理：人的感受/行为 |
| **CosmosQA** | 25,262 | 4 | 常识阅读理解 |
| **DROP** | 86,935 | 4 | 离散推理（数值/集合操作+阅读理解） |
| **narrative-qa** | 39,447 | 4 | 叙事文档问答（选项可能很长） |
| **SI-Bench** | 2,221 | 4 | **中文**社交意图理解（对话场景标签分类） |
| **qasper** | 615 | 4 | 学术论文问答 |

**典型问题形式**：
```
SocialIQA:  "Cameron decided to have a barbecue" → How would Others feel? 
             A. like staying home  B. like attending  C. a good friend to have
CosmosQA:   长文本阅读理解 + 常识推理
DROP:       "To start the season, the Lions won against..." → 数值/集合推理
SI-Bench:   中文对话 → 该对话最符合哪类场景标签？（幽默/暗示/真实性测试/讽刺）
narrative-qa: 长叙事文本 → 阅读理解问答
qasper:     学术论文 → 基于论文内容的问题
```

---

### T4 — 反事实时间推理

**定义**：在虚构的时序规则/时间体系下，模型需要放弃现实世界的常识，按照新规则重新推理出答案。

**核心难点**：
- 必须抑制现实世界的知识，遵循虚构规则
- 部分数据涉及日期算术（在偏移量下的新日期）
- 是唯一使用 `multi_turn` 对话格式的任务层级
- 答案由"规则推演"决定，而非从文本中提取

**与 T3 的关键区别**：T3 问题在现实世界中只有一个正解；T4 问题在"如果世界规则不同"的情况下会有不同答案，需要模型放弃常识、遵循新规则。

**数据集**：

| 数据集 | 样本数 | 选项数 | 特点 |
|---|---|---|---|
| **MCTACO** (T4) | 100(sample)/2,000(full) | 2 | 反事实时长判断：原标"no"→新规则下变"yes" |
| **TempReason** (T4) | 100(sample) | 2 | 反事实日期算术：偏移量下计算新日期 |
| **UDST** (T4) | 100(sample)/1,241(full) | 2 | 反事实时长判断：原标"yes"→新规则下变"no" |

**典型问题形式**：
```
MCTACO T4:    "In this world, typical activities last 5-15 seconds.
               Is '10 seconds' reasonable?" → 在新规则下判断
TempReason T4: "In this world, the date arithmetic uses +20 days from the reference date.
               Original: January 11, 1948 → 新日期是？" → 日期推算
UDST T4:      "In this world, NO activity can exceed 30 minutes.
               Would '1 day' be reasonable?" → 在新规则下判断
```

---

## 结构性差异总结

### 交互格式

| 格式 | 说明 | 使用层级 |
|---|---|---|
| `single_turn` | 系统提示 + 用户问题，一次作答 | T1, T2, T3 |
| `multi_turn` (noise) | 多轮对话含噪音（闲聊/打断），最后才给出问题和选项 | T1–T3 的 `_multi_v1/v2/v3` 变体 |
| `multi_turn` (counterfactual) | 多轮对话设定虚构世界规则，模型需在新规则下推理 | T4 |

### 数据集变体

每个数据集包含以下变体：

| 变体后缀 | 说明 |
|---|---|
| `_single` | 单轮，无噪音 |
| `_multi_v1` | 多轮，轻度噪音 |
| `_multi_v2` | 多轮，中度噪音 |
| `_multi_v3` | 多轮，重度噪音 |

每个数据集可能有 `full_T{N}` 或 `sample_T{N}` 目录：
- `full_T{N}`: 完整数据集（可能数万条）
- `sample_T{N}`: 抽取的 100 条样本

### 选项与答案格式

| 特征 | 详情 |
|---|---|
| 选项格式 | `{"key": "A", "text": "选项文本"}` |
| 答案格式 | `answer_key` 始终为字母列表，如 `["A"]` 或 `["A", "D"]` |
| 多答案 | 仅 TimeDial (T1) 允许 `answer_key` 包含多个字母 |
| 选项数量 | 2–5 不等，以 4 选项最常见 |

### 评测代码中的关键区别

- **T1–T3 single/multi（现实世界问题）**：答案从上下文推导，不依赖假设规则
- **T4 counterfactual（反事实问题）**：答案由 `metadata.computed_answer` 决定，可能与原始标签相反
  - MCTACO T4: 原标签"no" → 新规则下变为"yes" (选项A)
  - UDST T4: 原标签"yes" → 新规则下变为"no" (选项B)
  - TempReason T4: 原日期正确 → 新偏移量下变为新日期 (选项A)

---

## 数据集→任务层级 映射表

| 数据集 | T1 | T2 | T3 | T4 | 语言 |
|---|:---:|:---:|:---:|:---:|:---:|
| TimeDial | ✅ | | | | en |
| TimeQA | ✅ | | | | en |
| TempReason | ✅ | | | ✅⃰ | en |
| UDST-DurationQA | ✅ | | | ✅⃰ | en |
| MCTACO | ✅ | | | ✅⃰ | en |
| tracie | | ✅ | | | en |
| PIQA | | ✅ | | | en |
| HellaSwag | | ✅ | | | en |
| pasta | | ✅ | | | en |
| SocialIQA | | | ✅ | | en |
| CosmosQA | | | ✅ | | en |
| DROP | | | ✅ | | en |
| qasper | | | ✅ | | en |
| narrative-qa | | | ✅ | | en |
| SI-Bench | | | ✅ | | **zh** |
| TempReason (T4) | | | | ✅ | en |
| UDST (T4) | | | | ✅ | en |
| MCTACO (T4) | | | | ✅ | en |

> ⃰ 标注表示同一原始数据集在不同任务层级有不同转换（T1 为原始问题，T4 为反事实版本）

---

## 总样本量统计

| 任务层级 | full 样本总量 | 数据集数 | 格式 | 特点 |
|:---:|---:|:---:|---|---|
| **T1** | ~448K | 5 | single_turn | 时间信息提取与推理 |
| **T2** | ~66K | 4 | single_turn | 常识与时序推理 |
| **T3** | ~188K | 6 | single_turn | 复杂场景理解 |
| **T4** | ~3.4K ⃰ | 3 | **multi_turn** | 反事实推理 |

> ⃰ T4 使用 counterfactual multi_turn 格式；sample 版本各 100 条，full 版本数量不等