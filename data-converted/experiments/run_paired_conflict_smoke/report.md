# Paired Conflict Multi-Turn Experiment Report

- run_dir: data-converted/experiments/run_paired_conflict_smoke
- paired_samples: 1
- expected_calls: 12
- actual_calls: 12
- styles: single, multi_v1, multi_v2, multi_v3
- models: gpt-4o-mini, doubao-seed-1-8-251228, doubao-seed-2-0-pro-260215
- strict_pairing: same dataset + same source_id forced across 4 styles
- multi_turn_design: task-conflict (misleading prior hypothesis / conflicting instruction), not casual chit-chat

## Model Overall

| model | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |
|---|---:|---:|---:|---:|---:|---:|
| doubao-seed-1-8-251228 | 4 | 0.0000 | 0.0000 | 0.1667 | 0.1250 | 0.7500 |
| doubao-seed-2-0-pro-260215 | 4 | 0.0000 | 0.0000 | 0.3333 | 0.2500 | 0.5000 |
| gpt-4o-mini | 4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Paired Degradation (ALL datasets)

| model | style | n_pairs | em_single | em_style | delta_em | f1_single | f1_style | delta_f1 | worse_rate | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| doubao-seed-1-8-251228 | multi_v1 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | no_clear_difference |
| doubao-seed-1-8-251228 | multi_v2 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | no_clear_difference |
| doubao-seed-1-8-251228 | multi_v3 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.6667 | 0.6667 | 0.0000 | no_clear_difference |
| doubao-seed-2-0-pro-260215 | multi_v1 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.6667 | 0.0000 | -0.6667 | 0.0000 | no_clear_difference |
| doubao-seed-2-0-pro-260215 | multi_v2 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.6667 | 0.0000 | -0.6667 | 0.0000 | no_clear_difference |
| doubao-seed-2-0-pro-260215 | multi_v3 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.6667 | 0.6667 | 0.0000 | 0.0000 | no_clear_difference |
| gpt-4o-mini | multi_v1 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | no_clear_difference |
| gpt-4o-mini | multi_v2 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | no_clear_difference |
| gpt-4o-mini | multi_v3 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | no_clear_difference |

## Answer: Is multi-turn really harder?

- rollup_count: 9 (3 models x 3 multi styles)
- harder_cases(delta_em<0): 0
- easier_cases(delta_em>0): 0
- neutral_cases(delta_em=0): 9
- conclusion: In this strict paired setup, no clear overall difficulty difference between task-conflict multi-turn and single.
