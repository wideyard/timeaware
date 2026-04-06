# 时间感知基准数据集清理与合并报告

## 执行摘要

**原始数据**: 2,006,561 条
**去重后**: 1,738,287 条（移除268,274重复）
**最终数据**: **20,527** 条（按维度合并后）

---

## 1. 维度重组方案

### T1: 时间计算 (5,565条)

| 子维度 | 数据量 | 来源 |
|--------|--------|------|
| **Duration** | 1,070 | T1-Duration, T1-TypicalTime, T1-Convo-CommonSense, T1-DurationCompare |
| **Ordering** | 975 | T1-Ordering, T1-Sequence, T1-Causal |
| **Counting** | 3,026 | T1-TimeCalc-*, T1-MultiChoice, T1-Addition, T1-Parallel, T1-Multihop, T1-Distractor |
| **TimeBoundary** | 494 | T1-TimeBoundary |

### T2: 状态追踪 (5,448条)

| 子维度 | 数据量 | 来源 |
|--------|--------|------|
| **Location** | 1,548 | T2-PositionTrack-* |
| **Status** | 2,055 | T2-StateTrack, T2-SocialState, T2-Progressive, T2-Tense, T2-Stationarity |
| **Consequence** | 1,845 | T2-Consequence, T2-Evidence, T2-StateTransition-*, T2-Location, T2-Ordering |

### T3: 并发冲突 (1,354条)

| 子维度 | 数据量 | 来源 |
|--------|--------|------|
| **SpaceConflict** | 513 | T3-Conflict, T3-TimeConflict, T3-TimeOverlap |
| **ResourceConflict** | 841 | T3-Resource, T3-Concurrent |

### T4: 长期记忆 (4,694条)

| 子维度 | 数据量 | 来源 |
|--------|--------|------|
| **NoiseRetrieval** | 4,095 | T4-Buried-*, T4-Noise-*, T4-Distractor, T4-Detail, T4-Section-Nav, T4-Convo-* |
| **MultiHop** | 599 | T4-Convo-Cross, T4-Multi-hop(新创建) |

### T5: 规则反转 (3,466条)

| 子维度 | 数据量 | 来源 |
|--------|--------|------|
| **RuleReversal** | 3,466 | T5-Counterfactual, T5-RulePerturbation, T5-RuleChange, T5-Confusion, T5-Emotion, T5-SocialReverse, T5-ProcessReverse, T5-Twist, T5-WrongToRight, T5-ChoiceInversion |

---

## 2. 数据修复

### 2.1 截断问题修复

修复了以下转换器中的截断问题：

| 转换器 | 修复处 | 影响数据集 |
|--------|--------|-----------|
| cosmosqa_conversational_converter.py | 5处 | T5-Emotion, T4-Convo-Dialog |
| drop_conversational_converter.py | 7处 | T3-TimeOverlap |
| hellaswag_conversational_converter.py | 6处 | T3-Conflict |
| longbench_conversational_converter.py | 4处 | T4-Buried-* |
| narrativeqa_conversational_converter.py | 2处 | T4-Convo-Cross, T4-Detail |
| tracie_conversational_converter.py | 6处 | T1-Duration |
| udst_durationqa_conversational_converter.py | 3处 | T1-Duration |
| piqa_conversational_converter.py | 1处 | T5-ChoiceInversion |

**总计**: 34处截断修复

### 2.2 T4 Multi-hop构造

- 来源: T1-Multihop (500条)
- 目标: T4-MultiHop (500条)
- 对话长度: 平均1,113字，全部>1000字
- 方法: 扩展短对话 + 添加噪声对话轮

---

## 3. T4 对话长度分析

| 子维度 | 符合标准>1000字 | 需要扩展 | 截断问题 |
|--------|---------------|----------|----------|
| T4-Buried-Info | 100% | - | 是 |
| T4-Section-Nav | 100% | - | 无 |
| T4-T4-Detail | 99.8% | - | 是 |
| T4-Convo-Dialog | 52% | +468字 | 是 |
| T4-Convo-Recall | 25% | +138字 | 是 |
| T4-Noise-Retrieval | 4% | +247字 | 无 |
| T4-Noisy-Retrieval | 0% | +658字 | 无 |
| T4-Multi-hop(新) | 100% | - | 无 |

---

## 4. 删除的子维度

以下子维度因数据量极少或质量问题被删除：

| 子维度 | 原始数量 | 删除原因 |
|--------|---------|----------|
| T2-T2-Branch | 224 | 数据不足 |
| T2-T2-Rollback | 176 | 数据不足 |
| T2-T2-Commonsense | 498 | 与其他维度重复 |
| T3-Convo-Location | 122 | 数据不足 |
| T3-Duration-Conflict | 17 | 数据极少 |

---

## 5. 文件结构

```
dataset_final/
├── T1/
│   ├── T1-Duration.jsonl (1,070条)
│   ├── T1-Ordering.jsonl (975条)
│   ├── T1-Counting.jsonl (3,026条)
│   └── T1-TimeBoundary.jsonl (494条)
├── T2/
│   ├── T2-Location.jsonl (1,548条)
│   ├── T2-Status.jsonl (2,055条)
│   └── T2-Consequence.jsonl (1,845条)
├── T3/
│   ├── T3-SpaceConflict.jsonl (513条)
│   └── T3-ResourceConflict.jsonl (841条)
├── T4/
│   ├── T4-NoiseRetrieval.jsonl (4,095条)
│   └── T4-MultiHop.jsonl (599条)
├── T5/
│   └── T5-RuleReversal.jsonl (3,466条)
└── merge_report.json
```

---

## 6. 后续建议

### 6.1 需要重新生成的数据

由于转换器已修复，以下数据集可以通过重新运行转换器获得更完整的数据：
- T4-Convo-Dialog (截断问题)
- T4-Convo-Recall (截断问题)
- T4-Convo-Cross (截断问题)
- T5-Emotion (截断问题)

### 6.2 数据增强建议

以下子维度数据量较少，建议数据增强：
- T3-SpaceConflict (513条) → 目标1000条
- T4-MultiHop (599条) → 目标1000条

### 6.3 质量验证

建议对以下数据集进行人工抽样验证：
- T5-ChoiceInversion (选项截断已修复，建议验证)
- T4-Multi-hop (新构造数据，建议验证)

---

## 7. 统计摘要

| 指标 | 数值 |
|------|------|
| 原始数据 | 2,006,561条 |
| 去重后 | 1,738,287条 |
| 维度合并后 | 20,527条 |
| 去重率 | 86.6% |
| 维度数 | 5个主维度 |
| 子维度数 | 11个 |

**数据分布**:
- T1 (时间计算): 27.1%
- T2 (状态追踪): 26.5%
- T3 (并发冲突): 6.6%
- T4 (长期记忆): 22.9%
- T5 (规则反转): 16.9%