# LLM 交互风格比较报告（小批量，类型化评分）

## 1. 实验目标
本实验比较同一源样本在三种交互风格下的模型表现：
- single（单轮）
- multiturn_clean（多轮清洁）
- multiturn_noisy（多轮噪声）

核心目标是测量多轮上下文和噪声是否改变准确率，并减少因格式不匹配导致的假阴性。

## 2. 数据与设置
- 输入结果文件：[output/small_batch_interaction_compare_t1_t5_typed.json](output/small_batch_interaction_compare_t1_t5_typed.json)
- 模型：
  - gpt-4o-mini
  - doubao-seed-1-8
  - doubao-seed-2-0-pro
- 子任务（5个）：
  - T1-Counting
  - T2-Status
  - T3-SpaceConflict
  - T4-NoiseRetrieval
  - T5-RuleReversal
- 匹配采样：每个子任务 20 个 source_id 三元组
- 总评估记录数：900
  - 3 个模型 × 5 个子任务 × 20 个样本 × 3 种交互风格

## 3. 评分协议
在判定正确性之前应用类型化评分：
- MC（选择题）：提取 A/B/C/D + 字母精确匹配
- Yes/No（是非题）：提取 yes/no + 精确匹配
- Span（片段）：字符串/数字重叠 + token F1 阈值
- Free-form（自由形式）：语义倾向的文本重叠（token F1）+ 宽松的词汇匹配

指标：
- strict（严格）：按任务特定规则完全正确
- partial（部分）：接近正确（例如状态正确但缺少下一步细节）
- combined（综合）：strict + partial

## 4. 整体结果（按模型）
| Model | Total | Strict Correct | Partial Correct | Strict Acc | Combined Acc |
|---|---:|---:|---:|---:|---:|
| gpt-4o-mini | 300 | 106 | 32 | 35.33% | 46.00% |
| doubao-seed-1-8 | 300 | 91 | 30 | 30.33% | 40.33% |
| doubao-seed-2-0-pro | 300 | 90 | 34 | 30.00% | 41.33% |

关键解读：
- 所有模型的综合准确率都显著高于严格准确率。
- 部分得分贡献了不可忽视的提升（约10-11个百分点），表明存在大量"差一点就答对"的情况。

## 5. 交互风格效应（综合准确率）
### gpt-4o-mini
- single: 45.00%
- multiturn_clean: 46.00%
- multiturn_noisy: 47.00%

### doubao-seed-1-8
- single: 39.00%
- multiturn_clean: 41.00%
- multiturn_noisy: 41.00%

### doubao-seed-2-0-pro
- single: 40.00%
- multiturn_clean: 44.00%
- multiturn_noisy: 40.00%

关键解读：
- 清洁多轮上下文通常有帮助或保持中性。
- 噪声多轮上下文并非一律有害；其影响因子任务和模型而异。
- doubao-seed-2-0-pro 从清洁上下文中受益，但在噪声上下文下回落。

## 6. 按答案类型分析（综合准确率）
### gpt-4o-mini
- yesno: 98.04% (n=51)
- mc: 51.67% (n=60)
- span: 35.71% (n=84)
- free_form: 25.71% (n=105)

### doubao-seed-1-8
- yesno: 66.67% (n=51)
- mc: 48.33% (n=60)
- free_form: 31.43% (n=105)
- span: 29.76% (n=84)

### doubao-seed-2-0-pro
- yesno: 58.82% (n=51)
- mc: 50.00% (n=60)
- span: 34.52% (n=84)
- free_form: 33.33% (n=105)

关键解读：
- 最大失败集中在 free-form 和 span 类型，而非 yes/no。
- yes/no 对 gpt-4o-mini 来说最容易且最稳定。
- 开放式答案类型主导了总错误量。

## 7. 子任务趋势（综合准确率）
### gpt-4o-mini
- T1-Counting: 30% -> 65% -> 70% (single -> clean -> noisy)
- T2-Status: 50% -> 50% -> 50%
- T3-SpaceConflict: 85% -> 80% -> 85%
- T4-NoiseRetrieval: 35% -> 20% -> 20%
- T5-RuleReversal: 25% -> 15% -> 10%

### doubao-seed-1-8
- T1-Counting: 45% -> 60% -> 60%
- T2-Status: 45% -> 45% -> 45%
- T3-SpaceConflict: 55% -> 60% -> 60%
- T4-NoiseRetrieval: 25% -> 25% -> 25%
- T5-RuleReversal: 25% -> 15% -> 15%

### doubao-seed-2-0-pro
- T1-Counting: 55% -> 65% -> 70%
- T2-Status: 50% -> 50% -> 50%
- T3-SpaceConflict: 40% -> 65% -> 55%
- T4-NoiseRetrieval: 30% -> 30% -> 20%
- T5-RuleReversal: 25% -> 10% -> 5%

关键解读：
- T1-Counting 在多轮设置下持续改善。
- T5-RuleReversal 对所有模型来说最难，从 single 到 noisy 明显下降。
- T4-NoiseRetrieval 持续表现较弱且对噪声敏感。

## 8. 为什么之前的准确率看起来低，现在更好
与早期的字符串相等式评分相比，此类型化设置减少了假阴性：
- MC 和 yes/no 现在使用明确的提取器。
- Span/free-form 现在使用 token 级重叠和数字一致性。
- 部分得分捕捉"基本正确"的状态答案。

观察证据：
- 部分正确记录数：96
- 许多部分正确案例是 T2-Status，模型状态判断正确但遗漏下一步细节。

## 9. 定性案例
详细案例输出：[output/small_batch_interaction_examples.md](output/small_batch_interaction_examples.md)

### 9.1 严格正确案例
- model=gpt-4o-mini, sub_task=T4-NoiseRetrieval, interaction=multiturn_clean
  - gold: 2:30 PM
  - prediction: 2:30 PM

解读：
- 当目标明确且局部化时，模型仍能在多轮上下文中精确检索。

### 9.2 部分正确案例
- model=gpt-4o-mini, sub_task=T2-Status, interaction=single
  - gold: Still in progress. The next logical step is: rubs his eye with his fingers.
  - prediction: It is still in progress.
  - partial_reason: status_only_without_next_step

解读：
- 模型正确识别了状态，但遗漏了要求的下一步细节。
- 这正是"仅用严格评分会低估有效推理"的典型案例。

### 9.3 错误案例
- model=gpt-4o-mini, sub_task=T3-SpaceConflict, interaction=multiturn_clean
  - gold: Yes, there's a time overlap.
  - prediction: no

解读：
- 这是真正的逻辑错误（极性翻转），而非格式不匹配。

## 10. 图表

### 10.1 各模型整体准确率
![Overall Accuracy by Model](output/figures/overall_accuracy_by_model.png)

要点：
- 三个模型的综合准确率始终高于严格准确率，确认部分得分捕捉了有意义的"差一点就答对"行为。

### 10.2 各模型交互风格效应
![Interaction Effect by Model](output/figures/interaction_effect_by_model.png)

要点：
- 清洁多轮通常有帮助。
- 噪声多轮并非一律有害；模型敏感度各不相同。

### 10.3 子任务热力图
![Subtask Heatmap](output/figures/subtask_heatmap.png)

要点：
- T5-RuleReversal 和 T4-NoiseRetrieval 保持最难区域。
- T1-Counting 和 T3-SpaceConflict 对某些模型相对较强。

### 10.4 答案类型比较
![Answer-Type Comparison](output/figures/answer_type_comparison.png)

要点：
- yes/no 最容易，而 free-form 和 span 主导剩余错误。
- 错误特征更多由答案类型驱动，而非仅由交互风格决定。

## 11. 实践结论
- "single vs clean vs noisy" 的比较应使用综合准确率报告，而非仅用严格准确率。
- 对于稳健的模型排名，应强调：
  - T5-RuleReversal 和 T4-NoiseRetrieval 作为高难度压力测试
  - T1-Counting 和 T3-SpaceConflict 作为上下文敏感度探测
- 将类型化评分作为此基准的默认评分方式；严格评分可作为次要指标保留。

## 12. 建议的后续运行
1. 将匹配样本量增加到每子任务 50 个，以获得更紧的置信区间。
2. 为每个模型和每种交互风格添加 bootstrap 置信区间。
3. 为每个子任务添加专门的提示（特别是 T5 和 T4），以区分推理错误和指令遵循错误。
4. 导出两个排行榜：
   - strict 排行榜
   - combined 排行榜