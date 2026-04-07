# LLM 交互风格评测精简报告（修复后）

## 1. 实验范围
- 数据文件：output/small_batch_interaction_compare_t1_t5_s20_typed_post_hellaswag_fix.json
- 模型：gpt-4o-mini、doubao-seed-1-8、doubao-seed-2-0-pro
- 子任务：T1-Counting、T2-Status、T3-SpaceConflict、T4-NoiseRetrieval、T5-RuleReversal
- 采样：每子任务 20 条 source_id 三元组（single / multiturn_clean / multiturn_noisy）
- 总记录数：900

## 2. 评分口径
- strict：严格正确
- partial：部分正确（例如状态判断正确但细节缺失）
- combined：strict + partial
- 采用类型化判分：mc、yesno、span、free_form

## 3. 总体结果（按模型）
| Model | Total | Strict Correct | Partial Correct | Strict Acc | Combined Acc |
|---|---:|---:|---:|---:|---:|
| gpt-4o-mini | 300 | 134 | 11 | 44.67% | 48.33% |
| doubao-seed-1-8 | 300 | 118 | 12 | 39.33% | 43.33% |
| doubao-seed-2-0-pro | 300 | 121 | 11 | 40.33% | 44.00% |

结论：
- 当前设置下，gpt-4o-mini 综合准确率最高。
- 三个模型的 combined 均高于 strict，说明部分正确在该任务中有稳定贡献。

## 4. 交互风格结论（combined）
- gpt-4o-mini：single 48.00%，clean 49.00%，noisy 48.00%
- doubao-seed-1-8：single 40.00%，clean 46.00%，noisy 44.00%
- doubao-seed-2-0-pro：single 45.00%，clean 43.00%，noisy 44.00%

结论：
- multiturn_clean 对多数模型更稳。
- multiturn_noisy 影响具有任务依赖性，不是单向增益或单向损伤。

## 5. 按答案类型表现（combined）
### gpt-4o-mini
- yesno: 85.96% (n=57)
- mc: 67.78% (n=90)
- span: 34.48% (n=87)
- free_form: 7.58% (n=66)

### doubao-seed-1-8
- yesno: 54.39% (n=57)
- mc: 64.44% (n=90)
- span: 32.18% (n=87)
- free_form: 19.70% (n=66)

### doubao-seed-2-0-pro
- yesno: 50.88% (n=57)
- mc: 68.89% (n=90)
- span: 28.74% (n=87)
- free_form: 24.24% (n=66)

结论：
- mc 与 yesno 明显优于 free_form 与 span。
- free_form 是当前主要误差来源。

## 6. 子任务观察（combined）
### gpt-4o-mini
- T1-Counting: 35% -> 65% -> 70%
- T2-Status: 70% -> 60% -> 60%
- T3-SpaceConflict: 75% -> 90% -> 85%
- T4-NoiseRetrieval: 35% -> 20% -> 20%
- T5-RuleReversal: 25% -> 10% -> 5%

### doubao-seed-1-8
- T1-Counting: 45% -> 65% -> 60%
- T2-Status: 65% -> 65% -> 60%
- T3-SpaceConflict: 45% -> 60% -> 55%
- T4-NoiseRetrieval: 25% -> 25% -> 30%
- T5-RuleReversal: 20% -> 15% -> 15%

### doubao-seed-2-0-pro
- T1-Counting: 65% -> 65% -> 75%
- T2-Status: 60% -> 60% -> 60%
- T3-SpaceConflict: 45% -> 55% -> 55%
- T4-NoiseRetrieval: 30% -> 25% -> 25%
- T5-RuleReversal: 25% -> 10% -> 5%

结论：
- T1 与 T3 在多轮上下文中更容易释放能力。
- T5-RuleReversal 是最难任务，noisy 条件下退化明显。
- T4-NoiseRetrieval 仍是短板。

## 7. 直接可用结论
- 主报告建议采用 combined 作为主指标，strict 作为辅指标。
- 若做模型横评，优先关注 T5 与 T4 的稳健性。
- 若做交互策略，优先采用 multiturn_clean，并按子任务控制噪声注入强度。

## 8. 相关产物
- 完整英文报告：output/small_batch_interaction_compare_t1_t5_s20_typed_report.md
- 完整中文报告：output/small_batch_interaction_compare_t1_t5_s20_typed_report_zh.md
- 差异表：output/hellaswag_fix_before_after_diff_table.md
