# Typed对比实验：修复前 vs 修复后 差异表

- before: output/small_batch_interaction_compare_t1_t5_s20_typed_pre_hellaswag_fix.json
- after: output/small_batch_interaction_compare_t1_t5_s20_typed_post_hellaswag_fix.json

## doubao-seed-1-8

| Overall | Before | After | Delta |
|---|---:|---:|---:|
| Strict Accuracy | 30.33% | 39.33% | +9.00% |
| Combined Accuracy | 40.33% | 44.00% | +3.67% |

| Subtask | Interaction | Before | After | Delta |
|---|---|---:|---:|---:|
| T1-Counting | single | 45.00% | 50.00% | +5.00% |
| T1-Counting | multiturn_clean | 60.00% | 70.00% | +10.00% |
| T1-Counting | multiturn_noisy | 60.00% | 55.00% | -5.00% |
| T2-Status | single | 45.00% | 65.00% | +20.00% |
| T2-Status | multiturn_clean | 45.00% | 65.00% | +20.00% |
| T2-Status | multiturn_noisy | 45.00% | 65.00% | +20.00% |
| T3-SpaceConflict | single | 55.00% | 50.00% | -5.00% |
| T3-SpaceConflict | multiturn_clean | 60.00% | 60.00% | +0.00% |
| T3-SpaceConflict | multiturn_noisy | 60.00% | 50.00% | -10.00% |
| T4-NoiseRetrieval | single | 25.00% | 20.00% | -5.00% |
| T4-NoiseRetrieval | multiturn_clean | 25.00% | 30.00% | +5.00% |
| T4-NoiseRetrieval | multiturn_noisy | 25.00% | 35.00% | +10.00% |
| T5-RuleReversal | single | 25.00% | 20.00% | -5.00% |
| T5-RuleReversal | multiturn_clean | 15.00% | 10.00% | -5.00% |
| T5-RuleReversal | multiturn_noisy | 15.00% | 15.00% | +0.00% |

## doubao-seed-2-0-pro

| Overall | Before | After | Delta |
|---|---:|---:|---:|
| Strict Accuracy | 30.00% | 38.00% | +8.00% |
| Combined Accuracy | 41.33% | 41.67% | +0.33% |

| Subtask | Interaction | Before | After | Delta |
|---|---|---:|---:|---:|
| T1-Counting | single | 55.00% | 45.00% | -10.00% |
| T1-Counting | multiturn_clean | 65.00% | 70.00% | +5.00% |
| T1-Counting | multiturn_noisy | 70.00% | 70.00% | +0.00% |
| T2-Status | single | 50.00% | 60.00% | +10.00% |
| T2-Status | multiturn_clean | 50.00% | 60.00% | +10.00% |
| T2-Status | multiturn_noisy | 50.00% | 60.00% | +10.00% |
| T3-SpaceConflict | single | 40.00% | 45.00% | +5.00% |
| T3-SpaceConflict | multiturn_clean | 65.00% | 50.00% | -15.00% |
| T3-SpaceConflict | multiturn_noisy | 55.00% | 50.00% | -5.00% |
| T4-NoiseRetrieval | single | 30.00% | 30.00% | +0.00% |
| T4-NoiseRetrieval | multiturn_clean | 30.00% | 20.00% | -10.00% |
| T4-NoiseRetrieval | multiturn_noisy | 20.00% | 25.00% | +5.00% |
| T5-RuleReversal | single | 25.00% | 20.00% | -5.00% |
| T5-RuleReversal | multiturn_clean | 10.00% | 10.00% | +0.00% |
| T5-RuleReversal | multiturn_noisy | 5.00% | 10.00% | +5.00% |

## gpt-4o-mini

| Overall | Before | After | Delta |
|---|---:|---:|---:|
| Strict Accuracy | 35.33% | 45.00% | +9.67% |
| Combined Accuracy | 46.00% | 48.67% | +2.67% |

| Subtask | Interaction | Before | After | Delta |
|---|---|---:|---:|---:|
| T1-Counting | single | 30.00% | 30.00% | +0.00% |
| T1-Counting | multiturn_clean | 65.00% | 65.00% | +0.00% |
| T1-Counting | multiturn_noisy | 70.00% | 75.00% | +5.00% |
| T2-Status | single | 50.00% | 70.00% | +20.00% |
| T2-Status | multiturn_clean | 50.00% | 65.00% | +15.00% |
| T2-Status | multiturn_noisy | 50.00% | 60.00% | +10.00% |
| T3-SpaceConflict | single | 85.00% | 75.00% | -10.00% |
| T3-SpaceConflict | multiturn_clean | 80.00% | 90.00% | +10.00% |
| T3-SpaceConflict | multiturn_noisy | 85.00% | 85.00% | +0.00% |
| T4-NoiseRetrieval | single | 35.00% | 35.00% | +0.00% |
| T4-NoiseRetrieval | multiturn_clean | 20.00% | 20.00% | +0.00% |
| T4-NoiseRetrieval | multiturn_noisy | 20.00% | 20.00% | +0.00% |
| T5-RuleReversal | single | 25.00% | 25.00% | +0.00% |
| T5-RuleReversal | multiturn_clean | 15.00% | 10.00% | -5.00% |
| T5-RuleReversal | multiturn_noisy | 10.00% | 5.00% | -5.00% |
