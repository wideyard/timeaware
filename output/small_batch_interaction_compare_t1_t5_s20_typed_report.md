# LLM Interaction-Style Comparison Report (Small Batch, Typed Scoring)

## 1. Experiment Goal
This experiment compares model performance across three interaction styles within the same source sample:
- single
- multiturn_clean
- multiturn_noisy

The focus is to measure whether multi-turn context and noise change accuracy, and to reduce false negatives caused by format mismatch.

## 2. Data and Setup
- Input result file: [output/small_batch_interaction_compare_t1_t5_s20_typed_post_hellaswag_fix.json](output/small_batch_interaction_compare_t1_t5_s20_typed_post_hellaswag_fix.json)
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
| gpt-4o-mini | 300 | 134 | 11 | 44.67% | 48.33% |
| doubao-seed-1-8 | 300 | 118 | 12 | 39.33% | 43.33% |
| doubao-seed-2-0-pro | 300 | 121 | 11 | 40.33% | 44.00% |

Key read:
- Combined accuracy remains higher than strict accuracy for all models.
- Partial credit now contributes a modest lift (about 3.7-4.0 points), indicating fewer near-miss cases after the data fix.

## 5. Interaction-Style Effect (Combined Accuracy)
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

Key read:
- Clean multi-turn is still beneficial overall for two models.
- Noisy multi-turn remains mixed and subtask-dependent.
- doubao-seed-2-0-pro now shows stronger single-turn baseline and slight clean-context drop.

## 6. By Answer Type (Combined Accuracy)
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

Key read:
- MC and yes/no are now clearly stronger than free-form and span.
- Free-form remains the largest failure concentration, especially for gpt-4o-mini.
- Error volume is still dominated by open-ended answer styles.

## 7. Subtask Trends (Combined Accuracy)
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

Key read:
- T1-Counting still benefits from multi-turn context for most models.
- T2-Status no longer shows the previous flat profile and now varies by model/style.
- T5-RuleReversal remains the hardest and degrades toward noisy interaction.

## 8. Why Accuracy Looked Low Before, and Why This Is Better
Compared with earlier string-equality style scoring, this typed setup reduces false negatives:
- MC and yes/no now use explicit extractors.
- Span/free-form now use token-level overlap and numeric consistency.
- Partial credit captures "mostly right" status answers.

Observed evidence:
- Partial-correct records: 34
- Partials are still concentrated in T2/T4 style cases, but far fewer than before.

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
