# Tier-Style Hardest Dataset Experiment Report

- run_dir: data-converted/experiments/run_tierstyle_20260414_003923
- expected_calls: 1200
- actual_calls: 1200
- tiers: T1, T2, T3, T4, T5
- styles: single, multi_v1, multi_v2, multi_v3
- models: gpt-4o-mini, doubao-seed-1-8-251228, doubao-seed-2-0-pro-260215

## Tier-Style Dataset Mapping

| tier | style | dataset |
|---|---|---|
| T1 | multi_v1 | TimeDial |
| T1 | multi_v2 | TimeDial |
| T1 | multi_v3 | TimeDial |
| T1 | single | TimeDial |
| T2 | multi_v1 | CosmosQA |
| T2 | multi_v2 | pasta |
| T2 | multi_v3 | pasta |
| T2 | single | CosmosQA |
| T3 | multi_v1 | SocialIQA |
| T3 | multi_v2 | tracie |
| T3 | multi_v3 | tracie |
| T3 | single | tracie |
| T4 | multi_v1 | DROP |
| T4 | multi_v2 | DROP |
| T4 | multi_v3 | narrative-qa |
| T4 | single | narrative-qa |
| T5 | multi_v1 | TempReason |
| T5 | multi_v2 | PIQA |
| T5 | multi_v3 | PIQA |
| T5 | single | PIQA |

## Model x Tier x Style

| model | tier | style | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |
|---|---|---|---:|---:|---:|---:|---:|---:|
| doubao-seed-1-8-251228 | T1 | single | 20 | 0.3000 | 0.0000 | 0.7067 | 0.6083 | 0.0500 |
| doubao-seed-2-0-pro-260215 | T1 | single | 20 | 0.2000 | 0.0000 | 0.6667 | 0.5500 | 0.1000 |
| gpt-4o-mini | T1 | single | 20 | 0.0500 | 0.0000 | 0.5833 | 0.4500 | 0.0000 |
| doubao-seed-1-8-251228 | T1 | multi_v1 | 20 | 0.2500 | 0.0000 | 0.6167 | 0.5250 | 0.1500 |
| doubao-seed-2-0-pro-260215 | T1 | multi_v1 | 20 | 0.1500 | 0.0000 | 0.5567 | 0.4583 | 0.2500 |
| gpt-4o-mini | T1 | multi_v1 | 20 | 0.2000 | 0.0000 | 0.6717 | 0.5500 | 0.0000 |
| doubao-seed-1-8-251228 | T1 | multi_v2 | 20 | 0.2500 | 0.0000 | 0.7233 | 0.6083 | 0.0500 |
| doubao-seed-2-0-pro-260215 | T1 | multi_v2 | 20 | 0.2000 | 0.0000 | 0.6000 | 0.5000 | 0.2000 |
| gpt-4o-mini | T1 | multi_v2 | 20 | 0.0500 | 0.0000 | 0.5483 | 0.4250 | 0.0000 |
| doubao-seed-1-8-251228 | T1 | multi_v3 | 20 | 0.3000 | 0.0000 | 0.7067 | 0.6083 | 0.1000 |
| doubao-seed-2-0-pro-260215 | T1 | multi_v3 | 20 | 0.1500 | 0.0000 | 0.5500 | 0.4500 | 0.2000 |
| gpt-4o-mini | T1 | multi_v3 | 20 | 0.0000 | 0.0000 | 0.5917 | 0.4333 | 0.0000 |
| doubao-seed-1-8-251228 | T2 | single | 20 | 0.6000 | 0.6000 | 0.6000 | 0.6000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | T2 | single | 20 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.1000 |
| gpt-4o-mini | T2 | single | 20 | 0.7500 | 0.7500 | 0.7833 | 0.7750 | 0.0000 |
| doubao-seed-1-8-251228 | T2 | multi_v1 | 20 | 0.5500 | 0.5500 | 0.5500 | 0.5500 | 0.0000 |
| doubao-seed-2-0-pro-260215 | T2 | multi_v1 | 20 | 0.4500 | 0.4500 | 0.4500 | 0.4500 | 0.2000 |
| gpt-4o-mini | T2 | multi_v1 | 20 | 0.4000 | 0.4000 | 0.7783 | 0.6792 | 0.0000 |
| doubao-seed-1-8-251228 | T2 | multi_v2 | 20 | 0.6500 | 0.6875 | 0.8833 | 0.8250 | 0.0000 |
| doubao-seed-2-0-pro-260215 | T2 | multi_v2 | 20 | 0.7000 | 0.7500 | 0.8333 | 0.8000 | 0.1000 |
| gpt-4o-mini | T2 | multi_v2 | 20 | 0.6000 | 0.6250 | 0.8583 | 0.7917 | 0.0000 |
| doubao-seed-1-8-251228 | T2 | multi_v3 | 20 | 0.6000 | 0.6250 | 0.8333 | 0.7750 | 0.0500 |
| doubao-seed-2-0-pro-260215 | T2 | multi_v3 | 20 | 0.7500 | 0.8125 | 0.8833 | 0.8500 | 0.0500 |
| gpt-4o-mini | T2 | multi_v3 | 20 | 0.2500 | 0.1875 | 0.7186 | 0.5950 | 0.0000 |
| doubao-seed-1-8-251228 | T3 | single | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | T3 | single | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.1000 |
| gpt-4o-mini | T3 | single | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.0000 |
| doubao-seed-1-8-251228 | T3 | multi_v1 | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1000 |
| doubao-seed-2-0-pro-260215 | T3 | multi_v1 | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1000 |
| gpt-4o-mini | T3 | multi_v1 | 20 | 0.4000 | 0.4000 | 0.6667 | 0.5833 | 0.0000 |
| doubao-seed-1-8-251228 | T3 | multi_v2 | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.0500 |
| doubao-seed-2-0-pro-260215 | T3 | multi_v2 | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.0000 |
| gpt-4o-mini | T3 | multi_v2 | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.0000 |
| doubao-seed-1-8-251228 | T3 | multi_v3 | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | T3 | multi_v3 | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.0000 |
| gpt-4o-mini | T3 | multi_v3 | 20 | 0.6000 | 0.6000 | 0.6000 | 0.6000 | 0.0000 |
| doubao-seed-1-8-251228 | T4 | single | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.1000 |
| doubao-seed-2-0-pro-260215 | T4 | single | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.0500 |
| gpt-4o-mini | T4 | single | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.0000 |
| doubao-seed-1-8-251228 | T4 | multi_v1 | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.1000 |
| doubao-seed-2-0-pro-260215 | T4 | multi_v1 | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.1000 |
| gpt-4o-mini | T4 | multi_v1 | 20 | 0.3000 | 0.3000 | 0.6000 | 0.5000 | 0.0000 |
| doubao-seed-1-8-251228 | T4 | multi_v2 | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.1000 |
| doubao-seed-2-0-pro-260215 | T4 | multi_v2 | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.0500 |
| gpt-4o-mini | T4 | multi_v2 | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.0000 |
| doubao-seed-1-8-251228 | T4 | multi_v3 | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.0500 |
| doubao-seed-2-0-pro-260215 | T4 | multi_v3 | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1500 |
| gpt-4o-mini | T4 | multi_v3 | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.0000 |
| doubao-seed-1-8-251228 | T5 | single | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |
| doubao-seed-2-0-pro-260215 | T5 | single | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| gpt-4o-mini | T5 | single | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |
| doubao-seed-1-8-251228 | T5 | multi_v1 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | T5 | multi_v1 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| gpt-4o-mini | T5 | multi_v1 | 20 | 0.5000 | 0.5000 | 0.7000 | 0.6250 | 0.0000 |
| doubao-seed-1-8-251228 | T5 | multi_v2 | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |
| doubao-seed-2-0-pro-260215 | T5 | multi_v2 | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |
| gpt-4o-mini | T5 | multi_v2 | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |
| doubao-seed-1-8-251228 | T5 | multi_v3 | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |
| doubao-seed-2-0-pro-260215 | T5 | multi_v3 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| gpt-4o-mini | T5 | multi_v3 | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |

## Model Overall

| model | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |
|---|---:|---:|---:|---:|---:|---:|
| doubao-seed-1-8-251228 | 400 | 0.6925 | 0.8045 | 0.7985 | 0.7725 | 0.0450 |
| doubao-seed-2-0-pro-260215 | 400 | 0.6750 | 0.8077 | 0.7720 | 0.7479 | 0.0900 |
| gpt-4o-mini | 400 | 0.5300 | 0.6474 | 0.7300 | 0.6754 | 0.0000 |
