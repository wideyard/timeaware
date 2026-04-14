# Paired Conflict Multi-Turn Experiment Report

- run_dir: data-converted/experiments/run_paired_conflict_1200
- paired_samples: 100
- expected_calls: 1200
- actual_calls: 1200
- styles: single, multi_v1, multi_v2, multi_v3
- models: gpt-4o-mini, doubao-seed-1-8-251228, doubao-seed-2-0-pro-260215
- strict_pairing: same dataset + same source_id forced across 4 styles
- multi_turn_design: task-conflict (misleading prior hypothesis / conflicting instruction), not casual chit-chat

## Model Overall

| model | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |
|---|---:|---:|---:|---:|---:|---:|
| doubao-seed-1-8-251228 | 400 | 0.4475 | 0.5156 | 0.5045 | 0.4904 | 0.3750 |
| doubao-seed-2-0-pro-260215 | 400 | 0.3275 | 0.3906 | 0.3658 | 0.3563 | 0.5475 |
| gpt-4o-mini | 400 | 0.6100 | 0.7031 | 0.7272 | 0.6983 | 0.0325 |

## Paired Degradation (ALL datasets)

| model | style | n_pairs | em_single | em_style | delta_em | f1_single | f1_style | delta_f1 | worse_rate | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| doubao-seed-1-8-251228 | multi_v1 | 100 | 0.4900 | 0.4100 | -0.0800 | 0.5567 | 0.4633 | -0.0933 | 0.1300 | harder_than_single |
| doubao-seed-1-8-251228 | multi_v2 | 100 | 0.4900 | 0.4500 | -0.0400 | 0.5567 | 0.5047 | -0.0520 | 0.1100 | harder_than_single |
| doubao-seed-1-8-251228 | multi_v3 | 100 | 0.4900 | 0.4400 | -0.0500 | 0.5567 | 0.4933 | -0.0633 | 0.0700 | harder_than_single |
| doubao-seed-2-0-pro-260215 | multi_v1 | 100 | 0.3900 | 0.2500 | -0.1400 | 0.4500 | 0.2700 | -0.1800 | 0.1600 | harder_than_single |
| doubao-seed-2-0-pro-260215 | multi_v2 | 100 | 0.3900 | 0.3000 | -0.0900 | 0.4500 | 0.3333 | -0.1167 | 0.1000 | harder_than_single |
| doubao-seed-2-0-pro-260215 | multi_v3 | 100 | 0.3900 | 0.3700 | -0.0200 | 0.4500 | 0.4100 | -0.0400 | 0.0300 | harder_than_single |
| gpt-4o-mini | multi_v1 | 100 | 0.6100 | 0.6400 | 0.0300 | 0.7233 | 0.7927 | 0.0693 | 0.0800 | easier_than_single |
| gpt-4o-mini | multi_v2 | 100 | 0.6100 | 0.5600 | -0.0500 | 0.7233 | 0.6760 | -0.0473 | 0.1300 | harder_than_single |
| gpt-4o-mini | multi_v3 | 100 | 0.6100 | 0.6300 | 0.0200 | 0.7233 | 0.7167 | -0.0067 | 0.0700 | easier_than_single |

## Answer: Is multi-turn really harder?

- rollup_count: 9 (3 models x 3 multi styles)
- harder_cases(delta_em<0): 7
- easier_cases(delta_em>0): 2
- neutral_cases(delta_em=0): 0
- conclusion: In this strict paired setup, task-conflict multi-turn is overall harder than single.
