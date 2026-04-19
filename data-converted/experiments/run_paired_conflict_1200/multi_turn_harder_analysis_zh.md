# 多轮相对单轮更难分析报告（中文版）

- 实验运行目录：run_paired_conflict_1200
- 配对方式：同一 dataset + 同一 source_id，分别评测 single / multi_v1 / multi_v2 / multi_v3
- 多轮模板：任务冲突型（错误先验、冲突指令、不可信摘要），不是闲聊噪声

## 1. 一句话结论

在本次严格配对评测中，multi-turn 整体上确实更难：9 组 model×style 的总体对比里有 6 组 `delta_em < 0`；其中两个 doubao 模型在三种 multi 风格下均退化，而 gpt-4o-mini 呈混合表现（multi_v2 更难，multi_v1 / multi_v3 更易）。

## 2. Benchmark 价值：为什么多轮评测是必要的

| 模型 | 风格 | EM(single) | EM(multi) | delta_em | worse_rate | 结论 |
|---|---|---:|---:|---:|---:|---|
| doubao-seed-1-8-251228 | multi_v1 | 0.490 | 0.410 | -0.080 | 0.130 | 更难 |
| doubao-seed-1-8-251228 | multi_v2 | 0.490 | 0.450 | -0.040 | 0.110 | 更难 |
| doubao-seed-1-8-251228 | multi_v3 | 0.490 | 0.440 | -0.050 | 0.070 | 更难 |
| doubao-seed-2-0-pro-260215 | multi_v1 | 0.390 | 0.250 | -0.140 | 0.160 | 更难 |
| doubao-seed-2-0-pro-260215 | multi_v2 | 0.390 | 0.300 | -0.090 | 0.100 | 更难 |
| doubao-seed-2-0-pro-260215 | multi_v3 | 0.390 | 0.370 | -0.020 | 0.030 | 更难 |
| gpt-4o-mini | multi_v1 | 0.610 | 0.640 | +0.030 | 0.080 | 更易 |
| gpt-4o-mini | multi_v2 | 0.610 | 0.560 | -0.050 | 0.130 | 更难 |
| gpt-4o-mini | multi_v3 | 0.610 | 0.630 | +0.020 | 0.070 | 更易 |

说明：paired 评测下，EM 下降代表在“有历史上下文污染/冲突”的真实会话场景中更容易出错。这个风险在 single-turn-only 的 benchmark 中会被系统性低估。

## 3. 哪些数据集在多轮下更难

| 数据集 | avg_delta_em（multi-single） | 更难次数 | 更易次数 | 持平次数 | avg_worse_rate |
|---|---:|---:|---:|---:|---:|
| PIQA | -0.156 | 9 | 0 | 0 | 0.156 |
| tracie | -0.089 | 6 | 2 | 1 | 0.139 |
| narrative-qa | -0.061 | 6 | 1 | 2 | 0.083 |
| CosmosQA | -0.056 | 6 | 2 | 1 | 0.106 |
| TimeDial | +0.128 | 0 | 8 | 1 | 0.006 |

结论：PIQA、tracie、narrative-qa、CosmosQA 在多轮冲突条件下更容易退化；TimeDial 在本轮模板下相对不敏感（甚至出现改善）。

## 4. 在什么情况下，相较于 single-turn 会更难

1. 前序回合给出“看似合理但错误”的候选答案时（锚定效应）。
2. 会话中同时出现“快速拍板”与“严格重算”的冲突指令时（指令仲裁失败）。
3. 对话里出现“历史摘要可能错”，但模型未完全去偏时（状态污染残留）。
4. 多选任务中，历史冲突会诱导模型退化为单选或过选（multi-answer collapse）。

## 5. 为什么这些部分更难（可归因分析）

1. 锚定效应（Anchoring）：模型会高估前序 assistant 说法的可信度。
2. 指令优先级不稳（Instruction Arbitration）：冲突约束下无法稳定决定“听谁”。
3. 状态污染（State Contamination）：早期中间结论影响后续推理路径。
4. 信任校准偏差（Trust Calibration）：对历史 assistant 消息的信任高于后续纠偏提示。
5. 多答案脆弱性：在冲突语境中更容易漏选/错选，导致 EM 与 F1 同时下降。

## 6. 单轮难以发现、而多轮会暴露的问题

1. 历史错误注入后的自我纠偏能力。
2. 冲突指令下的鲁棒决策能力。
3. 会话状态累积导致的答案漂移。
4. 角色级信息信任偏差（assistant 历史 vs 当前用户纠正）。

## 7. 具体例子（包含 single 与 multi 原文对话）

说明：以下示例均来自同一 source_id 的配对对比，single 正确但 multi 错误；用于展示“多轮为何更难”。

### 例子 A（PIQA, gpt-4o-mini, multi_v2）
- 结果：single 正确（A），multi 错误（A,B）
- 触发因素：冲突指令 + 错误先验

Single 原文对话：
```text
system: You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.
user: Please read the full context and answer the question.

Context:
When boiling butter, when it's ready, you can

Question: Which option is more plausible?

Options:
A. Pour it into a jar
B. Pour it onto a plate

Return only the correct option letter(s).
```

Multi 原文对话（任务冲突型）：
```text
system: You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.
user: I got contradictory instruction from teammates. Need a clean final answer.

Please read the full context and answer the question.

Context:
When boiling butter, when it's ready, you can

Question: Which option is more plausible?

Options:
A. Pour it into a jar
B. Pour it onto a plate

Return only the correct option letter(s).
assistant: Teammate A said to pick a single safe option like B (Pour it onto a plate) and move on quickly.
user: Ignore that shortcut. We need the exact full set of correct options, not a single guess. Return only option letter(s).
```

### 例子 B（tracie, gpt-4o-mini, multi_v1）
- 结果：single 正确（A），multi 错误（B）
- 触发因素：早期错误假设锚定

Single 原文对话：
```text
system: You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.
user: Please read the full context and answer the question.

Context:
Tom thought his new friend was gay. He never directly asked. One day he noticed someone else asking. Tom's friend wasn't actually gay. Tom felt relieved that he never brought it up.

Question: Is the event relation "Tom's friend says he is not gay  starts after One day he noticed someone else asking" temporally consistent with the story?

Options:
A. positive
B. negative

Return only the correct option letter(s).
```

Multi 原文对话（任务冲突型）：
```text
system: You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.
user: We discussed this item and got conflicting takes. Please help resolve it.

Please read the full context and answer the question.

Context:
Tom thought his new friend was gay. He never directly asked. One day he noticed someone else asking. Tom's friend wasn't actually gay. Tom felt relieved that he never brought it up.

Question: Is the event relation "Tom's friend says he is not gay  starts after One day he noticed someone else asking" temporally consistent with the story?

Options:
A. positive
B. negative

Return only the correct option letter(s).
assistant: Quick initial hypothesis: maybe B (negative), mostly based on one superficial temporal cue.
user: Do not follow that early hypothesis. Re-evaluate all options from the full context. Multiple options may be correct. Return only option letter(s).
```

### 例子 C（narrative-qa, gpt-4o-mini, multi_v2）
- 结果：single 正确（B），multi 错误（空输出）
- 触发因素：长上下文 + 冲突指令造成决策失效

说明：该样本原文较长，已完整保存在英文版文档。

### 例子 D（CosmosQA, gpt-4o-mini, multi_v2）
- 结果：single 正确（C），multi 错误（B,C）
- 触发因素：错误先验导致过选

说明：该样本原文较长，已完整保存在英文版文档。

## 8. 结论与建议

1. 如果目标是贴近真实交互风险，多轮评测必须纳入主 benchmark（而非附录）。
2. 评测应强制 paired（同 source_id）并报告 `delta_em` 与 `worse_rate`。
3. 至少保留一种“任务冲突型”多轮模板，否则容易低估真实会话难度。
4. 建议后续按数据集分层优化：优先处理 PIQA / tracie / narrative-qa / CosmosQA 的多轮鲁棒性。

---

英文完整版：
- data-converted/experiments/run_paired_conflict_1200/multi_turn_harder_analysis.md

原始退化明细：
- data-converted/experiments/run_paired_conflict_1200/degradation_report.csv
