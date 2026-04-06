# LLM Interaction-Style Comparison Report (Small Batch, Typed Scoring)

## 1. Experiment Goal
This experiment compares model performance across three interaction styles within the same source sample:
- single
- multiturn_clean
- multiturn_noisy

The focus is to measure whether multi-turn context and noise change accuracy, and to reduce false negatives caused by format mismatch.

## 2. Data and Setup
- Input result file: [output/small_batch_interaction_compare_t1_t5_s20_typed.json](output/small_batch_interaction_compare_t1_t5_s20_typed.json)
- Models:
  - gpt-4o-mini
  - doubao-seed-1-8
  - doubao-seed-2-0-pro
- Subtasks (5):
  - T1-Counting
  - T2-Status
  - T3-SpaceConflict
  - T4-NoiseRetrieval
  - T5-RuleReversal
- Matched sampling: 20 source_id triplets per subtask
- Total evaluated records: 900
  - 3 models x 5 subtasks x 20 samples x 3 interaction styles

## 3. Scoring Protocol
Typed scoring was applied before judging correctness:
- MC: A/B/C/D extraction + exact letter match
- Yes/No: yes/no extraction + exact match
- Span: string/number overlap + token F1 thresholds
- Free-form: semantic-leaning text overlap (token F1) + relaxed lexical match

Metrics:
- strict: fully correct by task-specific rule
- partial: near-correct (for example, status is correct but missing next-step detail)
- combined: strict + partial

## 4. Overall Results (Per Model)
| Model | Total | Strict Correct | Partial Correct | Strict Acc | Combined Acc |
|---|---:|---:|---:|---:|---:|
| gpt-4o-mini | 300 | 106 | 32 | 35.33% | 46.00% |
| doubao-seed-1-8 | 300 | 91 | 30 | 30.33% | 40.33% |
| doubao-seed-2-0-pro | 300 | 90 | 34 | 30.00% | 41.33% |

Key read:
- Combined accuracy is materially higher than strict accuracy for all models.
- Partial credit contributes a non-trivial lift (about 10-11 points), indicating many near-miss answers.

## 5. Interaction-Style Effect (Combined Accuracy)
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

Key read:
- Clean multi-turn generally helps or stays neutral.
- Noisy multi-turn is not uniformly harmful; effect is subtask/model dependent.
- doubao-seed-2-0-pro benefits from clean context but drops back under noisy context.

## 6. By Answer Type (Combined Accuracy)
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

Key read:
- The largest failure concentration is free-form and span, not yes/no.
- yes/no is easiest and most stable for gpt-4o-mini.
- Open-ended answer styles dominate total error volume.

## 7. Subtask Trends (Combined Accuracy)
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

Key read:
- T1-Counting consistently improves in multi-turn settings.
- T5-RuleReversal is hardest across all models, with clear degradation from single to noisy.
- T4-NoiseRetrieval remains weak and noise-sensitive.

## 8. Why Accuracy Looked Low Before, and Why This Is Better
Compared with earlier string-equality style scoring, this typed setup reduces false negatives:
- MC and yes/no now use explicit extractors.
- Span/free-form now use token-level overlap and numeric consistency.
- Partial credit captures "mostly right" status answers.

Observed evidence:
- Partial-correct records: 96
- Many partials are T2-Status cases where the model gets status right but omits next-step detail.

## 9. Qualitative Examples
Detailed example dump: [output/small_batch_interaction_examples.md](output/small_batch_interaction_examples.md)

### 9.1 Strictly Correct Example
- model=gpt-4o-mini, sub_task=T4-NoiseRetrieval, interaction=multiturn_clean
  - gold: 2:30 PM
  - prediction: 2:30 PM

Interpretation:
- The model can still retrieve the exact target under multi-turn context when the target is explicit and localized.

### 9.2 Partial-Correct Example
- model=gpt-4o-mini, sub_task=T2-Status, interaction=single
  - gold: Still in progress. The next logical step is: rubs his eye with his fingers.
  - prediction: It is still in progress.
  - partial_reason: status_only_without_next_step

Interpretation:
- The model identifies the status state correctly, but misses the required next-step detail.
- This is precisely the case where strict-only scoring underestimates useful reasoning.

### 9.3 Incorrect Example
- model=gpt-4o-mini, sub_task=T3-SpaceConflict, interaction=multiturn_clean
  - gold: Yes, there's a time overlap.
  - prediction: no

Interpretation:
- This is a true logical error (polarity flip), not a formatting mismatch.

## 10. Figures

### 10.1 Overall Accuracy by Model
![Overall Accuracy by Model](output/figures/overall_accuracy_by_model.png)

Takeaway:
- Combined accuracy is consistently above strict accuracy for all three models, confirming that partial-credit captures meaningful near-miss behavior.

### 10.2 Interaction Style Effect by Model
![Interaction Effect by Model](output/figures/interaction_effect_by_model.png)

Takeaway:
- Clean multi-turn generally helps.
- Noisy multi-turn is not uniformly harmful; model-level sensitivity differs.

### 10.3 Subtask Heatmap
![Subtask Heatmap](output/figures/subtask_heatmap.png)

Takeaway:
- T5-RuleReversal and T4-NoiseRetrieval remain the hardest regions.
- T1-Counting and T3-SpaceConflict are relatively stronger for some models.

### 10.4 Answer-Type Comparison
![Answer-Type Comparison](output/figures/answer_type_comparison.png)

Takeaway:
- yes/no is easiest, while free-form and span dominate residual errors.
- Error profile is more driven by answer type than by interaction style alone.

## 11. Practical Conclusions
- The "single vs clean vs noisy" story should be reported with combined accuracy, not strict-only.
- For robust model ranking, emphasize:
  - T5-RuleReversal and T4-NoiseRetrieval as hard stress tests
  - T1-Counting and T3-SpaceConflict as sensitivity-to-context probes
- Use typed scoring as default for this benchmark; strict-only can remain as a secondary metric.

## 12. Recommended Next Runs
1. Increase matched sample size to 50 per subtask for tighter confidence.
2. Add bootstrap confidence intervals per model and per interaction style.
3. Add per-subtask prompt specialization (especially for T5 and T4) to separate reasoning error from instruction-following error.
4. Export two scoreboards:
   - strict leaderboard
   - combined leaderboard
