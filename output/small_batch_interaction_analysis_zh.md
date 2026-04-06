# 三模型跨任务类型表现分析报告

## 1. 总体概览

本报告分析了三个大语言模型在五个时间感知任务类型上的表现，涵盖三种交互风格（单轮、清洁多轮、噪声多轮）。

### 1.1 模型与任务概览

| 模型 | 总样本 | 严格正确 | 部分正确 | 严格准确率 | 综合准确率 |
|------|-------:|---------:|---------:|----------:|----------:|
| gpt-4o-mini | 300 | 106 | 32 | 35.33% | **46.00%** |
| doubao-seed-1-8 | 300 | 91 | 30 | 30.33% | **40.33%** |
| doubao-seed-2-0-pro | 300 | 90 | 34 | 30.00% | **41.33%** |

### 1.2 答案类型分布

| 答案类型 | 样本数 | 说明 |
|----------|-------:|------|
| yesno | 51 | 是非题（二元判断） |
| mc | 60 | 多选题（A/B/C/D选择） |
| span | 84 | 短答案/片段提取 |
| free_form | 105 | 自由形式生成 |

---

## 2. T1-Counting（时间计算）任务分析

### 2.1 任务特点

T1-Counting 要求模型进行时间计算，包括时间加减、持续时间推算等。答案类型主要为 `span`（数值+单位）和 `mc`（多选题）。

### 2.2 性能表现

|模型 | single | clean | noisy |趋势 |
|------|-------:|------:|------:|-----|
| gpt-4o-mini | 30% | 65% | 70% | **↑ 显著提升** |
| doubao-seed-1-8 | 45% | 60% | 60% | ↑ 提升 |
| doubao-seed-2-0-pro | 55% | 65% | 70% | **↑ 显著提升** |

**关键发现**：
- 所有模型在多轮上下文中表现均优于单轮
- gpt-4o-mini 提升最大（+40个百分点）
- 噪声环境未造成明显性能下降

### 2.3 案例分析

#### ✅正确案例（gpt-4o-mini, multiturn_noisy）

**题目来源**: `drop_t1_add_754c3d74-dfde-4d25-a`

**对话内容**:
```
User: In week 6, the Lions hosted the NFC West Division-leading San Francisco 49ers.
Assistant: Got it. Please continue.
User: The Lions struck first, when Jason Hanson kicked a 25-yard field goal that came after a San Francisco turnover.
Assistant: All right, I have that. Continue when ready.
User: I run for 6 minutes first, then 25 more minutes.
Assistant: Makes sense. What comes next?
User: What's for dinner today?Assistant: I don't know your dinner plans.
User: How long did I run in total?
Assistant: Thanks, I am following. Go on.
User: If I run for 6 minutes and then 25 more minutes, how long in total?
```

**答案信息**:
- 答案类型: span
- 正确答案: 31 minutes
- 模型回答: 31 minutes
- 评分: strict_correct ✓

**分析**: 模型在噪声多轮环境下（包含无关的橄榄球赛信息和"吃什么"的噪声对话）仍能正确提取关键时间信息（6分钟+25分钟）并进行简单计算（31分钟）。

---

#### ❌ 错误案例（gpt-4o-mini, free_form）- 干扰项陷阱

**题目来源**: `timedial_t1_dist_120`

**对话内容**:
```
Context: A:Even with volume sales our costs for the Exec User won't go down much. 
B: Just what are you proposing? 
A: We could take a cut on the price. But 25% would reduce much our profit margin. We...

Question: Based on the conversation logic (not just text matching), fill in:
A: I understand. We propose a structured deal. For ___, we get a discount of 20% 
and the next six months we get 15%.
```

**答案信息**:
- 正确答案: The answer is the first six months. Note: 'the first 25 days' is a distractor...
- 模型回答: volume sales
- 评分: token_f1=0.0

**分析**: 模型完全偏离问题，陷入干扰项陷阱（文中出现的"volume sales"），未能识别正确的时间表达。这表明 T1-Distractor 子任务对模型的时间推理能力有较高要求。

---

## 3. T2-Status（状态追踪）任务分析

### 3.1 任务特点

T2-Status 要求模型追踪事件或活动的当前状态（如：已完成、进行中、将要发生），并可能需要描述下一步动作。这是**部分正确率最高**的任务类型。

### 3.2 性能表现

| 模型 | single | clean | noisy | 严格正确 | 部分正确 |
|------|-------:|------:|------:|---------:|---------:|
| gpt-4o-mini | 50% | 50% | 50% | 5% | 45% |
| doubao-seed-1-8 | 45% | 45% | 45% | 5-10% | 35-40% |
| doubao-seed-2-0-pro | 50% | 50% | 50% | 0-10% | 40-50% |

**关键发现**：
- 综合准确率稳定（50%），但严格准确率极低（5%）
- 部分正确贡献了约45个百分点
- 多轮上下文对性能影响不大

### 3.3 案例分析

#### ⚠️ 部分正确案例（gpt-4o-mini）- 状态对但缺少下一步

**题目来源**: `hellaswag_t2_prog_16781`

**正确答案**: Still in progress. The next logical step is: rubs his eye with his fingers.

**模型回答**: It is still in progress.

**部分正确原因**: status_only_without_next_step

**分析**: 模型正确识别了状态（进行中），但遗漏了题目要求的"下一步逻辑动作"。这反映出模型理解了问题的一半，但未完全遵循指令。

---

#### ✅ 完全正确案例 - 简洁状态判断

**题目来源**: `cosmos_t2_tense_31ODACBENWT90WRJTS0L`

**正确答案**: Already happened (past tense verbs: said, saw)

**模型回答**: Already happened

**评分**: strict_correct ✓

**分析**: 简洁状态判断任务，模型能准确识别时态并给出正确状态。

---

#### 示例对话（T2-Status multiturn_clean）

**题目来源**: `choice75_t2_state_3392604825589394064`

**对话内容**:
```
User: My goal is to go out for a picnic.
Assistant: Okay, that makes sense. Please continue.
User: I've decided to go out for a picnic.
Assistant: Thanks, I am following. Go on.
User: I've take a shower.
Assistant: Understood. Please continue.
User: After 'get ready for the day', what am I doing?
```

**正确答案**: get ready for the day

**分析**: 这是一个状态追踪问题，需要模型理解当前处于"准备出门野餐"过程中的哪个步骤。

---

#### ❌ 错误案例 - 状态误判

**题目来源**: `hellaswag_t2_state_11013`

**正确答案**: Currently in progress: throws the pink item on a game board on the floor.

**模型回答**: You are currently speaking in an office while holding a pink item.

**评分**: token_f1=0.38

**分析**: 模型误解了活动类型（说话 vs 游戏），未能正确追踪状态。

---

## 4. T3-SpaceConflict（空间冲突）任务分析

### 4.1 任务特点

T3-SpaceConflict 判断事件之间是否存在时间重叠（时空冲突）。答案类型为 `yesno`（是/否），是最简单的任务类型。

### 4.2 性能表现

| 模型 | single | clean | noisy | 答案类型 |
|------|-------:|------:|------:|----------|
| gpt-4o-mini | 85% | 80% | 85% | yesno |
| doubao-seed-1-8 | 55% | 60% | 60% | yesno |
| doubao-seed-2-0-pro | 40% | 65% | 55% | yesno |

**关键发现**：
- gpt-4o-mini 在是非题上表现优异（98% yesno准确率）
- doubao-seed-2-0-pro 从多轮上下文获益最大（+25个百分点）
- 噪声对 gpt-4o-mini 影响最小

### 4.3 案例分析

#### ✅ 正确案例（gpt-4o-mini, multiturn_clean）

**题目来源**: `hellaswag_t3_time_10035`

**对话内容**:
```
User: I scheduled washing hands for 2 PM.
Assistant: Noted, washing hands at 2 PM.
User: It will take about 30 minutes.
Assistant: Noted. I am with you so far.
User: But I also have a meeting at 2:30 PM.Assistant: All right, I have that. Continue when ready.
User: If washing hands takes 30 minutes starting at 2 PM, and I have another event 
     at 2:30 PM, is there a conflict?
```

**答案信息**:
- 答案类型: yesno
- 正确答案: Yes, there's a time overlap.
- 模型回答: yes
- 评分: strict_correct ✓

**分析**: 简单二元判断，模型在所有交互类型下均能正确回答。这是最简单的任务类型。

---

#### ❌ 错误案例 - 多轮清洁环境下的错误翻转

**题目来源**: `hellaswag_t3_time_11456`

**正确答案**: Yes, there's a time overlap.

**模型表现**:
- single: yes ✓
- clean: no ✗
- noisy:: yes ✓

**分析**: 有趣的是，模型在清洁多轮环境下反而给出了错误答案，而噪声环境下却正确。这表明某些情况下噪声可能起到"正则化"作用，防止模型过度拟合某些模式。

---

## 5. T4-NoiseRetrieval（噪声检索）任务分析

### 5.1 任务特点

T4-NoiseRetrieval 要求模型从包含噪声信息的对话中提取关键信息。这是最困难的任务类型之一，答案类型主要为 `free_form` 和 `span`。

### 5.2 性能表现

| 模型 | single | clean | noisy | 严格正确 | 部分正确 |
|------|-------:|------:|------:|---------:|---------:|
| gpt-4o-mini | 35%| 20% | 20% | 2/20 | 5/20 |
| doubao-seed-1-8 | 25% | 25% | 25% | 2-4/20 | 1-3/20 |
| doubao-seed-2-0-pro | 30% | 30% | 20% | 3-4/20 | 0-3/20 |

**关键发现**：
- 所有模型表现均较差（综合准确率 20-35%）
- 多轮上下文反而降低了 gpt-4o-mini 的表现（-15个百分点）
- 噪声环境对 doubao-seed-2-0-pro 影响显著

### 5.3 案例分析

#### 示例对话（T4-NoiseRetrieval single）

**题目来源**: `cosmos_t4_buried_3Q9SPIIRWJKVQ8244310`

**对话内容**:
```
Context: Good Old War and person L : I saw both of these bands Wednesday night, 
and they both blew me away. seriously. Good Old War is acoustic and makes me smile. 
I really can not help but be happy when I listen to them; I think it's the fact 
that they seemed so happy themselves when they played.Question: What important event did I mention earlier?
```

**正确答案**: I had an important event

**分析**: 这是一个需要从噪声文本中提取关键信息的任务，模型需要识别"Wednesday night"等时间相关表达。

---

#### ✅ 正确案例（T4-NoiseRetrieval）

**正确答案**: 2:30 PM

**模型回答**: 2:30 PM

**评分**: strict_correct ✓

**分析**: 当目标信息明确且局部化时，模型能够从噪声中正确检索。

---

#### ⚠️ 部分正确案例 - 语义接近但不精确

**正确答案**: He might thought it was funny.**模型回答**: He might be shocked.

**评分**: partial_correct (token_overlap)

**分析**: 模型捕捉了情感层面，但具体情绪判断错误。

---

#### ❌ 错误案例 - 完全偏离

**正确答案**: He might thought it was funny.

**模型回答**: How might my manager react when he finds out the truth?

**分析**: 模型未能理解问题意图，生成了与问题无关的反问句。

---

## 6. T5-RuleReversal（规则反转/反事实推理）任务分析

### 6.1 任务特点

T5-RuleReversal 要求模型进行反事实推理，即在假设规则改变的情况下预测结果。这是**最困难的任务类型**。

### 6.2 性能表现

| 模型 | single | clean | noisy | 下降幅度 |
|------|-------:|------:|------:|----------|
| gpt-4o-mini | 25% | 15% | 10% | **-15pp** |
| doubao-seed-1-8 | 25% | 15% | 15% | -10pp |
| doubao-seed-2-0-pro | 25% | 10% | 5% | **-20pp** |

**关键发现**：
- 所有模型在噪声多轮环境下表现最差
- doubao-seed-2-0-pro 下降最剧烈（从25%跌至5%）
- 单轮环境下所有模型表现相近（25%）

### 6.3 案例分析

#### 示例对话（T5-RuleReversal single）

**题目来源**: `choice75_t5_cf_3392604825589394064`

**对话内容**:
```
Question: In this opposite scenario, which option should I choose?
```

**正确答案**: Choose park along the street (because the reasoning is reversed)

**分析**: T5任务需要模型在反事实场景下进行推理，要求模型理解"opposite scenario"的含义并反转其推理逻辑。

---

#### ❌ 典型错误模式

T5 任务的数据显示，模型在反事实推理中常见错误包括：

1. **未能反转因果关系**: 模型仍然按照原有规则推理
2. **上下文干扰**: 多轮对话中的无关信息分散注意力
3. **逻辑跳跃**: 模型做出的推理缺乏清晰步骤

**关键观察**：T5 整体趋势表明：
- 单轮环境最有利于反事实推理
- 多轮上下文（尤其是噪声）严重干扰推理能力
- 这类任务需要更强的逻辑推理和假设追踪能力

---

## 7. 按答案类型分析

### 7.1 yesno（是非题）- 最简单

| 模型 | 准确率 | 样本数 |
|------|-------:|-------:|
| gpt-4o-mini | **98.04%** | 51 |
| doubao-seed-1-8 | 66.67% | 51 |
| doubao-seed-2-0-pro | 58.82% | 51 |

**分析**: gpt-4o-mini 在二元判断上表现卓越，接近人类水平。

### 7.2 mc（多选题）- 中等难度

| 模型 | 准确率 | 样本数 |
|------|-------:|-------:|
| gpt-4o-mini | 51.67% | 60 |
| doubao-seed-1-8 | 48.33% | 60 |
| doubao-seed-2-0-pro | 50.00% | 60 |

**分析**: 三模型表现相近，约有一半题目能正确作答。

### 7.3 span（片段提取）- 较难

| 模型 | 准确率 | 样本数 |
|------|-------:|-------:|
| gpt-4o-mini | 35.71% | 84 |
| doubao-seed-1-8 | 29.76% | 84 |
| doubao-seed-2-0-pro | 34.52% | 84 |

**分析**: 片段提取需要精确匹配，模型表现普遍偏低。

### 7.4 free_form（自由形式）- 最难

| 模型 | 严格准确率 | 部分准确率 | 综合准确率 |
|------|---------:|----------:|----------:|
| gpt-4o-mini | 2.86% | 22.86% | **25.71%** |
| doubao-seed-1-8 | 6.67% | 24.76% | **31.43%** |
| doubao-seed-2-0-pro | 8.57% | 24.76% | **33.33%** |

**分析**: 
- 自由形式生成是最具挑战性的任务类型
- doubao 模型略优于 gpt-4o-mini
- 部分正确贡献了大部分得分

---

## 8. 关键结论

### 8.1 模型能力排序

| 任务类型 | 最佳模型 |第二名 | 第三名 |
|----------|----------|--------|--------|
| T1-Counting | doubao-seed-2-0-pro | gpt-4o-mini | doubao-seed-1-8 |
| T2-Status | 三模型相近 | - | - |
| T3-SpaceConflict | gpt-4o-mini | doubao-seed-1-8 | doubao-seed-2-0-pro |
| T4-NoiseRetrieval | gpt-4o-mini | doubao-seed-2-0-pro | doubao-seed-1-8 |
| T5-RuleReversal | 三模型相近（均差） | - | - |

### 8.2 任务难度排序（从易到难）

1. **T3-SpaceConflict** - yesno 类型，平均准确率 60-85%
2. **T1-Counting** - span/mc 类型，多轮提升显著
3. **T2-Status** - free_form 类型，部分正确贡献大
4. **T4-NoiseRetrieval** - free_form/span 类型，噪声干扰严重
5. **T5-RuleReversal** - 反事实推理，所有模型表现差

### 8.3 交互风格影响

| 任务类型| clean vs single | noisy vs clean |
|----------|-----------------|----------------|
| T1-Counting | **+提升** | 持平/微升 |
| T2-Status | 持平 | 持平 |
| T3-SpaceConflict | 持平 | 持平 |
| T4-NoiseRetrieval | **-下降** | 持平 |
| T5-RuleReversal | **-下降** | **-下降** |

### 8.4 建议

1. **T1-Counting**: 利用多轮上下文提升性能
2. **T2-Status**: 优化prompt以要求完整答案（包含下一步动作）
3. **T3-SpaceConflict**: 保持当前设置，表现已接近天花板
4. **T4-NoiseRetrieval**: 需要改进噪声过滤机制
5. **T5-RuleReversal**: 需要专门的反事实推理能力增强

---

## 9. 附录：详细数据引用

本报告基于以下数据：
- JSON 数据: `output/small_batch_interaction_compare_t1_t5_s20_typed.json`
- 原始报告: `output/small_batch_interaction_compare_t1_t5_s20_typed_report.md`
- 案例文件: `output/small_batch_interaction_examples.md`
- 数据集目录: `dataset_final_v3/`

评估样本：900条（3模型×5子任务×20样本×3交互类型）