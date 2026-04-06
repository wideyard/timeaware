# 数据集清理报告

## 概述

本文档记录了 `converted_data_v3` 数据集的清理过程和结果。

## 目标

- **去重**: 基于 context + query 的哈希值移除重复项
- **质量控制**: 评估任务相关性（是否切题）
- **数据精简**: 每个子维度保留约500条高质量数据
- **输出结构**: 按能力维度（T1-T5）组织

## 处理流程

### Phase 1: 索引与去重

| 指标 | 数值 |
|------|------|
| 原始数据总量 | 2,006,561 条 |
| 去重后数据量 | 1,738,287 条 |
| 移除重复项 | 268,274 条 (13.4%) |

### Phase 2: 质量评分与选择

每个条目根据以下标准评分（满分100分）：

1. **上下文质量 (25分)**: 长度、相关性
2. **问题质量 (25分)**: 格式、类型、清晰度
3. **答案质量 (25分)**: 存在性、完整性
4. **Ground Truth (15分)**: 原始数据完整性
5. **对话深度 (10分)**: 多轮对话丰富度

选择策略：
- 优先保留高质量条目
- 确保来源多样性（每个来源按比例抽取）
- 每个子维度最多500条

## 最终结果

### 按能力维度分布

| 能力维度 | 原始数量 | 选择后数量 | 压缩比 |
|----------|----------|------------|--------|
| **T1: 时间计算** | 1,487,636 | 7,130 | 99.5% |
| **T2: 状态追踪** | 238,655 | 10,272 | 95.7% |
| **T3: 并发冲突** | 65,303 | 2,639 | 96.0% |
| **T4: 长期记忆** | 81,712 | 6,115 | 92.5% |
| **T5: 反事实推理** | 133,255 | 8,667 | 93.5% |
| **总计** | 2,006,561 | **34,823** | 98.3% |

### 关键发现

1. **T1数据严重冗余**: 三个噪声变体（HistNoise/ConfusionNoise/NumNoise）各占408,000条
2. **T2范围最广**: 覆盖17个子维度，最多的子维度
3. **部分子维度数据稀缺**: 如T3-Duration-Conflict仅17条

### 子维度分布

#### T1: 时间计算 (16个子维度)

| 子维度 | 原始 | 选择 | 来源数 |
|--------|------|------|--------|
| T1-TimeCalc-HistNoise | 408,000 | 500 | 3 |
| T1-TimeCalc-ConfusionNoise | 408,000 | 500 | 3 |
| T1-TimeCalc-NumNoise | 408,000 | 500 | 3 |
| T1-T1-Ordering | 185,964 | 500 | 5 |
| T1-T1-Duration | 31,843 | 500 | 11 |
| T1-T1-TimeBoundary | 11,840 | 500 | 4 |
| T1-T1-MultiChoice | 11,976 | 500 | 3 |
| T1-T1-Distractor | 8,503 | 500 | 2 |
| T1-Convo-CommonSense | 6,722 | 500 | 1 |
| T1-T1-Sequence | 2,585 | 500 | 2 |
| T1-T1-Addition | 2,091 | 500 | 1 |
| T1-TypicalTime | 882 | 500 | 2 |
| T1-T1-Multihop | 600 | 500 | 1 |
| T1-T1-Causal | 342 | 342 | 1 |
| T1-T1-Parallel | 224 | 224 | 1 |
| T1-DurationCompare | 64 | 64 | 2 |

#### T2: 状态追踪 (24个子维度)

| 子维度 | 原始 | 选择 | 来源数 |
|--------|------|------|--------|
| T2-T2-StateTrack | 90,352 | 500 | 14 |
| T2-T2-SocialState | 35,364 | 500 | 2 |
| T2-PositionTrack-Basic | 39,147 | 500 | 6 |
| T2-T2-Location | 8,199 | 500 | 7 |
| T2-T2-Progressive | 7,019 | 500 | 5 |
| T2-StateTransition | 8,939 | 500 | 2 |
| T2-T2-Tense | 4,271 | 500 | 2 |
| T2-PositionTrack-Timeline | 5,346 | 500 | 3 |
| T2-PositionTrack-MC | 5,346 | 500 | 3 |
| T2-PositionTrack-WithContext | 5,346 | 500 | 3 |
| T2-T2-Commonsense | 5,222 | 498 | 6 |
| T2-StateTransition-BeforeAfter | 4,319 | 500 | 3 |
| T2-T2-Evidence | 5,000 | 500 | 1 |
| T2-Convo-Sequence | 1,502 | 500 | 1 |
| T2-CounterfactualState | 739 | 500 | 2 |
| T2-T2-Ordering | 984 | 500 | 2 |
| T2-T2-Consequence | 1,370 | 500 | 1 |
| T2-StateTransition-MC | 4,319 | 498 | 3 |
| T2-StateTransition-WithContext | 4,319 | 498 | 3 |
| T2-T2-Stationarity | 378 | 378 | 2 |
| T2-T2-Branch | 224 | 224 | 1 |
| T2-T2-Rollback | 176 | 176 | 1 |

#### T3: 并发冲突 (7个子维度)

| 子维度 | 原始 | 选择 | 来源数 |
|--------|------|------|--------|
| T3-T3-Concurrent | 49,933 | 500 | 3 |
| T3-T3-Conflict | 6,871 | 500 | 3 |
| T3-T3-TimeConflict | 5,224 | 500 | 2 |
| T3-T3-TimeOverlap | 1,624 | 500 | 1 |
| T3-T3-Resource | 1,512 | 500 | 2 |
| T3-Convo-Location | 122 | 122 | 1 |
| T3-Duration-Conflict | 17 | 17 | 2 |

#### T4: 长期记忆 (15个子维度)

| 子维度 | 原始 | 选择 | 来源数 |
|--------|------|------|--------|
| T4-T4-Buried | 25,439 | 500 | 11 |
| T4-T4-Section | 18,664 | 500 | 8 |
| T4-T4-Noise | 13,171 | 500 | 6 |
| T4-Buried-Info | 7,179 | 500 | 3 |
| T4-Noise-Retrieval | 7,179 | 500 | 3 |
| T4-T4-Detail | 3,087 | 500 | 1 |
| T4-Buried-Time | 1,361 | 500 | 2 |
| T4-Noisy-Retrieval | 1,327 | 500 | 2 |
| T4-Section-Nav | 2,090 | 500 | 3 |
| T4-Convo-Dialog | 1,058 | 500 | 1 |
| T4-Process-Memory | 542 | 500 | 1 |
| T4-Convo-Recall | 315 | 315 | 1 |
| T4-T4-Distractor | 200 | 200 | 1 |
| T4-Convo-Cross | 100 | 100 | 1 |

#### T5: 反事实推理 (17个子维度)

| 子维度 | 原始 | 选择 | 来源数 |
|--------|------|------|--------|
| T5-T5-RulePerturbation | 77,523 | 500 | 6 |
| T5-T5-Counterfactual | 12,121 | 500 | 4 |
| T5-T5-SocialReverse | 10,738 | 500 | 2 |
| T5-T5-RuleChange | 7,855 | 500 | 7 |
| T5-T5-Rule | 3,567 | 500 | 1 |
| T5-T5-RuleReversal | 5,000 | 500 | 1 |
| T5-T5-WrongToRight | 5,000 | 500 | 1 |
| T5-T5-Confusion | 1,550 | 500 | 1 |
| T5-Convo-RuleReverse | 1,449 | 500 | 1 |
| T5-T5-ChoiceInversion | 1,441 | 500 | 1 |
| T5-Convo-Reversal | 1,535 | 500 | 1 |
| T5-Convo-Contrastive | 1,432 | 500 | 1 |
| T5-ExplicitReverse | 671 | 500 | 2 |
| T5-T5-Emotion | 839 | 500 | 1 |
| T5-T5-Twist | 919 | 500 | 1 |
| T5-T5-ProcessReverse | 948 | 500 | 1 |
| T5-T5-SocialReverse | 1,273 | 500 | 2 |

## 数据稀缺子维度

以下子维度数据量不足500条，已保留全部数据：

| 子维度 | 可用数据 | 差额 |
|--------|----------|------|
| T2-T2-Rollback | 176 | -324 |
| T3-Convo-Location | 122 | -378 |
| T3-Duration-Conflict | 17 | -483 |
| T4-Convo-Cross | 100 | -400 |
| T4-T4-Distractor | 200 | -300 |
| T5-Stationarity-Reverse | 79 | -421 |
| T1-T1-Parallel | 224 | -276 |

**建议**: 这些子维度可能需要额外的数据收集或数据增强。

## 输出文件结构

```
converted_data_v3_cleaned/
├── T1/                     # 时间计算(16个子维度)
│   ├── T1-TimeCalc-HistNoise.jsonl
│   ├── T1-TimeCalc-ConfusionNoise.jsonl
│   ├── T1-TimeCalc-NumNoise.jsonl
│   ├── T1-T1-Ordering.jsonl
│   └── ...
├── T2/                     # 状态追踪(24个子维度)
│   ├── T2-T2-StateTrack.jsonl
│   └── ...
├── T3/                     # 并发冲突(7个子维度)
│   └── ...
├── T4/                     # 长期记忆(15个子维度)
│   └── ...
├── T5/                     # 反事实推理(17个子维度)
│   └── ...
├── cleaning_report.json    # 详细统计报告
└── phase1_report.json      # Phase 1统计报告
```

## 后续工作建议

1. **LLM质量评估**: 当前使用规则评分，可以用LLM对抽样进行更精细的质量评估
2. **数据增强**: 对稀缺子维度进行数据增强
3. **验证集划分**: 考虑为每个子维度划分train/dev/test
4. **数据平衡**: 目前T1占比过高(20%)，可考虑进一步削减