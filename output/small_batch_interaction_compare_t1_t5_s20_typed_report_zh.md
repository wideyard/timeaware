# LLM 交互风格比较报告（小批量，类型化评分）

## 1. 实验目标
本实验比较同一源样本在三种交互风格下的模型表现：
- single（单轮）
- multiturn_clean（多轮清洁）
- multiturn_noisy（多轮噪声）

核心目标是测量多轮上下文和噪声是否改变准确率，并减少因格式不匹配导致的假阴性。

## 2. 数据与设置
- 输入结果文件：[output/small_batch_interaction_compare_t1_t5_s20_typed_post_hellaswag_fix.json](output/small_batch_interaction_compare_t1_t5_s20_typed_post_hellaswag_fix.json)
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
| gpt-4o-mini | 300 | 134 | 11 | 44.67% | 48.33% |
| doubao-seed-1-8 | 300 | 118 | 12 | 39.33% | 43.33% |
| doubao-seed-2-0-pro | 300 | 121 | 11 | 40.33% | 44.00% |

关键解读：
- 所有模型的综合准确率仍高于严格准确率。
- 部分得分带来的提升缩小到约 3.7-4.0 个百分点，说明修复后近似正确样本减少。

## 5. 交互风格效应（综合准确率）
### gpt-4o-mini
- single: 48.00%
- multiturn_clean: 49.00%
- multiturn_noisy: 48.00%

### doubao-seed-1-8
- single: 40.00%
- multiturn_clean: 46.00%
- multiturn_noisy: 44.00%

### doubao-seed-2-0-pro
- single: 45.00%
- multiturn_clean: 43.00%
- multiturn_noisy: 44.00%

关键解读：
- 对两个模型而言，清洁多轮依然总体有帮助。
- 噪声多轮仍是混合效应，强依赖模型与子任务。
- doubao-seed-2-0-pro 在本轮中 single 基线更强，clean 略有回落。

## 6. 按答案类型分析（综合准确率）
### gpt-4o-mini
- yesno: 85.96% (n=57)
- mc: 67.78% (n=90)
- span: 34.48% (n=87)
- free_form: 7.58% (n=66)

### doubao-seed-1-8
- yesno: 54.39% (n=57)
- mc: 64.44% (n=90)
- free_form: 19.70% (n=66)
- span: 32.18% (n=87)

### doubao-seed-2-0-pro
- yesno: 50.88% (n=57)
- mc: 68.89% (n=90)
- span: 28.74% (n=87)
- free_form: 24.24% (n=66)

关键解读：
- MC 与 yes/no 明显强于 free-form 和 span。
- free-form 仍是主要错误来源，尤其在 gpt-4o-mini 上更突出。
- 总体错误仍主要来自开放式答案类型。

## 7. 子任务趋势（综合准确率）
### gpt-4o-mini
- T1-Counting: 35% -> 65% -> 70% (single -> clean -> noisy)
- T2-Status: 70% -> 60% -> 60%
- T3-SpaceConflict: 75% -> 90% -> 85%
- T4-NoiseRetrieval: 35% -> 20% -> 20%
- T5-RuleReversal: 25% -> 10% -> 5%

### doubao-seed-1-8
- T1-Counting: 45% -> 65% -> 60%
- T2-Status: 65% -> 65% -> 60%
- T3-SpaceConflict: 45% -> 60% -> 55%
- T4-NoiseRetrieval: 25% -> 25% -> 30%
- T5-RuleReversal: 25% -> 15% -> 15%

### doubao-seed-2-0-pro
- T1-Counting: 65% -> 65% -> 75%
- T2-Status: 60% -> 60% -> 60%
- T3-SpaceConflict: 45% -> 55% -> 55%
- T4-NoiseRetrieval: 30% -> 25% -> 25%
- T5-RuleReversal: 25% -> 10% -> 5%

关键解读：
- T1-Counting 对多数模型仍然受益于多轮上下文。
- T2-Status 不再是此前的"全平"模式，现已体现模型/风格差异。
- T5-RuleReversal 仍是最难任务，并在 noisy 下继续恶化。

## 8. 为什么之前的准确率看起来低，现在更好
与早期的字符串相等式评分相比，此类型化设置减少了假阴性：
- MC 和 yes/no 现在使用明确的提取器。
- Span/free-form 现在使用 token 级重叠和数字一致性。
- 部分得分捕捉"基本正确"的状态答案。

观察证据：
- 部分正确记录数：34
- 部分正确仍集中在 T2/T4 类案例，但数量较修复前明显下降。

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