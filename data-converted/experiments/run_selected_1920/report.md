# Selected Datasets Paired Experiment Report

- run_dir: data-converted/experiments/run_selected_1920
- expected_calls: 1920
- actual_calls: 1920
- seed: 6
- samples_per_group: 20
- styles: single, multi_v1, multi_v2, multi_v3
- models: gpt-4o-mini, doubao-seed-1-8-251228, doubao-seed-2-0-pro-260215

## Group Setup

| group | dataset | folder | forced_task |
|---|---|---|---|
| TimeDial | TimeDial | full |  |
| SI-Bench | SI-Bench | full |  |
| DROP | DROP | full |  |
| pasta | pasta | full |  |
| SocialIQA | SocialIQA | full |  |
| CosmosQA | CosmosQA | full |  |
| TempReason_T1 | TempReason | full | T1 |
| TempReason_T5 | TempReason | sample_T5 | T5 |

## Model x Style

| model | style | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |
|---|---|---:|---:|---:|---:|---:|---:|
| doubao-seed-1-8-251228 | single | 160 | 0.5125 | 0.6279 | 0.5458 | 0.5375 | 0.3812 |
| doubao-seed-1-8-251228 | multi_v1 | 160 | 0.4938 | 0.6047 | 0.5337 | 0.5234 | 0.3812 |
| doubao-seed-1-8-251228 | multi_v2 | 160 | 0.5125 | 0.6357 | 0.5692 | 0.5547 | 0.3187 |
| doubao-seed-1-8-251228 | multi_v3 | 160 | 0.5125 | 0.6279 | 0.5567 | 0.5453 | 0.3312 |
| doubao-seed-2-0-pro-260215 | single | 160 | 0.4250 | 0.5271 | 0.4375 | 0.4344 | 0.5500 |
| doubao-seed-2-0-pro-260215 | multi_v1 | 160 | 0.4062 | 0.5039 | 0.4188 | 0.4156 | 0.5687 |
| doubao-seed-2-0-pro-260215 | multi_v2 | 160 | 0.4375 | 0.5426 | 0.4583 | 0.4531 | 0.5062 |
| doubao-seed-2-0-pro-260215 | multi_v3 | 160 | 0.3688 | 0.4574 | 0.3854 | 0.3812 | 0.6000 |
| gpt-4o-mini | single | 160 | 0.6875 | 0.7984 | 0.7859 | 0.7610 | 0.0250 |
| gpt-4o-mini | multi_v1 | 160 | 0.4938 | 0.5659 | 0.6935 | 0.6369 | 0.0187 |
| gpt-4o-mini | multi_v2 | 160 | 0.6625 | 0.7597 | 0.7508 | 0.7281 | 0.0375 |
| gpt-4o-mini | multi_v3 | 160 | 0.5437 | 0.6357 | 0.7183 | 0.6666 | 0.0250 |

## Model x Group x Style

| model | group | style | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |
|---|---|---|---:|---:|---:|---:|---:|---:|
| doubao-seed-1-8-251228 | TimeDial | single | 20 | 0.0500 | 0.0000 | 0.1833 | 0.1500 | 0.7500 |
| doubao-seed-1-8-251228 | TimeDial | multi_v1 | 20 | 0.0000 | 0.0000 | 0.1667 | 0.1250 | 0.7500 |
| doubao-seed-1-8-251228 | TimeDial | multi_v2 | 20 | 0.0000 | 0.0000 | 0.2000 | 0.1500 | 0.7000 |
| doubao-seed-1-8-251228 | TimeDial | multi_v3 | 20 | 0.0000 | 0.0000 | 0.1667 | 0.1250 | 0.7000 |
| doubao-seed-1-8-251228 | SI-Bench | single | 20 | 0.1500 | 0.1500 | 0.1500 | 0.1500 | 0.6500 |
| doubao-seed-1-8-251228 | SI-Bench | multi_v1 | 20 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.5000 |
| doubao-seed-1-8-251228 | SI-Bench | multi_v2 | 20 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.4000 |
| doubao-seed-1-8-251228 | SI-Bench | multi_v3 | 20 | 0.1500 | 0.1500 | 0.1500 | 0.1500 | 0.4500 |
| doubao-seed-1-8-251228 | DROP | single | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.3000 |
| doubao-seed-1-8-251228 | DROP | multi_v1 | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.3000 |
| doubao-seed-1-8-251228 | DROP | multi_v2 | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.2500 |
| doubao-seed-1-8-251228 | DROP | multi_v3 | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.2000 |
| doubao-seed-1-8-251228 | pasta | single | 20 | 0.2500 | 0.5556 | 0.3833 | 0.3500 | 0.5500 |
| doubao-seed-1-8-251228 | pasta | multi_v1 | 20 | 0.2500 | 0.4444 | 0.4033 | 0.3625 | 0.5000 |
| doubao-seed-1-8-251228 | pasta | multi_v2 | 20 | 0.2000 | 0.4444 | 0.4533 | 0.3875 | 0.4000 |
| doubao-seed-1-8-251228 | pasta | multi_v3 | 20 | 0.2500 | 0.4444 | 0.4367 | 0.3875 | 0.4500 |
| doubao-seed-1-8-251228 | SocialIQA | single | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.2500 |
| doubao-seed-1-8-251228 | SocialIQA | multi_v1 | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1500 |
| doubao-seed-1-8-251228 | SocialIQA | multi_v2 | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.1500 |
| doubao-seed-1-8-251228 | SocialIQA | multi_v3 | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.2000 |
| doubao-seed-1-8-251228 | CosmosQA | single | 20 | 0.4500 | 0.4500 | 0.4500 | 0.4500 | 0.3500 |
| doubao-seed-1-8-251228 | CosmosQA | multi_v1 | 20 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.6500 |
| doubao-seed-1-8-251228 | CosmosQA | multi_v2 | 20 | 0.3500 | 0.3500 | 0.3500 | 0.3500 | 0.4500 |
| doubao-seed-1-8-251228 | CosmosQA | multi_v3 | 20 | 0.3500 | 0.3500 | 0.3500 | 0.3500 | 0.4500 |
| doubao-seed-1-8-251228 | TempReason_T1 | single | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.2000 |
| doubao-seed-1-8-251228 | TempReason_T1 | multi_v1 | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.2000 |
| doubao-seed-1-8-251228 | TempReason_T1 | multi_v2 | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.2000 |
| doubao-seed-1-8-251228 | TempReason_T1 | multi_v3 | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.2000 |
| doubao-seed-1-8-251228 | TempReason_T5 | single | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | TempReason_T5 | multi_v1 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | TempReason_T5 | multi_v2 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | TempReason_T5 | multi_v3 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | TimeDial | single | 20 | 0.0000 | 0.0000 | 0.0667 | 0.0500 | 0.9000 |
| doubao-seed-2-0-pro-260215 | TimeDial | multi_v1 | 20 | 0.0000 | 0.0000 | 0.0667 | 0.0500 | 0.9000 |
| doubao-seed-2-0-pro-260215 | TimeDial | multi_v2 | 20 | 0.0000 | 0.0000 | 0.0667 | 0.0500 | 0.9000 |
| doubao-seed-2-0-pro-260215 | TimeDial | multi_v3 | 20 | 0.0000 | 0.0000 | 0.0667 | 0.0500 | 0.9000 |
| doubao-seed-2-0-pro-260215 | SI-Bench | single | 20 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| doubao-seed-2-0-pro-260215 | SI-Bench | multi_v1 | 20 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| doubao-seed-2-0-pro-260215 | SI-Bench | multi_v2 | 20 | 0.1500 | 0.1500 | 0.1500 | 0.1500 | 0.6500 |
| doubao-seed-2-0-pro-260215 | SI-Bench | multi_v3 | 20 | 0.0500 | 0.0500 | 0.0500 | 0.0500 | 0.9500 |
| doubao-seed-2-0-pro-260215 | DROP | single | 20 | 0.6500 | 0.6500 | 0.6500 | 0.6500 | 0.3500 |
| doubao-seed-2-0-pro-260215 | DROP | multi_v1 | 20 | 0.5500 | 0.5500 | 0.5500 | 0.5500 | 0.4500 |
| doubao-seed-2-0-pro-260215 | DROP | multi_v2 | 20 | 0.6000 | 0.6000 | 0.6000 | 0.6000 | 0.4000 |
| doubao-seed-2-0-pro-260215 | DROP | multi_v3 | 20 | 0.5500 | 0.5500 | 0.5500 | 0.5500 | 0.4500 |
| doubao-seed-2-0-pro-260215 | pasta | single | 20 | 0.2500 | 0.5556 | 0.2833 | 0.2750 | 0.7000 |
| doubao-seed-2-0-pro-260215 | pasta | multi_v1 | 20 | 0.1500 | 0.3333 | 0.1833 | 0.1750 | 0.8000 |
| doubao-seed-2-0-pro-260215 | pasta | multi_v2 | 20 | 0.2500 | 0.5556 | 0.3500 | 0.3250 | 0.6000 |
| doubao-seed-2-0-pro-260215 | pasta | multi_v3 | 20 | 0.1000 | 0.2222 | 0.1667 | 0.1500 | 0.8000 |
| doubao-seed-2-0-pro-260215 | SocialIQA | single | 20 | 0.6500 | 0.6500 | 0.6500 | 0.6500 | 0.3000 |
| doubao-seed-2-0-pro-260215 | SocialIQA | multi_v1 | 20 | 0.6500 | 0.6500 | 0.6500 | 0.6500 | 0.3000 |
| doubao-seed-2-0-pro-260215 | SocialIQA | multi_v2 | 20 | 0.6500 | 0.6500 | 0.6500 | 0.6500 | 0.3500 |
| doubao-seed-2-0-pro-260215 | SocialIQA | multi_v3 | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.2500 |
| doubao-seed-2-0-pro-260215 | CosmosQA | single | 20 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.7500 |
| doubao-seed-2-0-pro-260215 | CosmosQA | multi_v1 | 20 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.7500 |
| doubao-seed-2-0-pro-260215 | CosmosQA | multi_v2 | 20 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.7500 |
| doubao-seed-2-0-pro-260215 | CosmosQA | multi_v3 | 20 | 0.0500 | 0.0500 | 0.0500 | 0.0500 | 0.9500 |
| doubao-seed-2-0-pro-260215 | TempReason_T1 | single | 20 | 0.6500 | 0.6500 | 0.6500 | 0.6500 | 0.3500 |
| doubao-seed-2-0-pro-260215 | TempReason_T1 | multi_v1 | 20 | 0.6500 | 0.6500 | 0.6500 | 0.6500 | 0.3500 |
| doubao-seed-2-0-pro-260215 | TempReason_T1 | multi_v2 | 20 | 0.6500 | 0.6500 | 0.6500 | 0.6500 | 0.3500 |
| doubao-seed-2-0-pro-260215 | TempReason_T1 | multi_v3 | 20 | 0.5500 | 0.5500 | 0.5500 | 0.5500 | 0.4500 |
| doubao-seed-2-0-pro-260215 | TempReason_T5 | single | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| doubao-seed-2-0-pro-260215 | TempReason_T5 | multi_v1 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | TempReason_T5 | multi_v2 | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| doubao-seed-2-0-pro-260215 | TempReason_T5 | multi_v3 | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| gpt-4o-mini | TimeDial | single | 20 | 0.2500 | 0.0000 | 0.5833 | 0.5000 | 0.0500 |
| gpt-4o-mini | TimeDial | multi_v1 | 20 | 0.1000 | 0.0000 | 0.5667 | 0.4500 | 0.1000 |
| gpt-4o-mini | TimeDial | multi_v2 | 20 | 0.2000 | 0.0000 | 0.5333 | 0.4500 | 0.1000 |
| gpt-4o-mini | TimeDial | multi_v3 | 20 | 0.0500 | 0.0000 | 0.5150 | 0.3917 | 0.0500 |
| gpt-4o-mini | SI-Bench | single | 20 | 0.3000 | 0.3000 | 0.3333 | 0.3250 | 0.0500 |
| gpt-4o-mini | SI-Bench | multi_v1 | 20 | 0.3000 | 0.3000 | 0.3667 | 0.3500 | 0.0000 |
| gpt-4o-mini | SI-Bench | multi_v2 | 20 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.0500 |
| gpt-4o-mini | SI-Bench | multi_v3 | 20 | 0.2000 | 0.2000 | 0.3917 | 0.3417 | 0.0000 |
| gpt-4o-mini | DROP | single | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |
| gpt-4o-mini | DROP | multi_v1 | 20 | 0.4000 | 0.4000 | 0.6733 | 0.5875 | 0.0000 |
| gpt-4o-mini | DROP | multi_v2 | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.0000 |
| gpt-4o-mini | DROP | multi_v3 | 20 | 0.7000 | 0.7000 | 0.8333 | 0.7875 | 0.0000 |
| gpt-4o-mini | pasta | single | 20 | 0.3500 | 0.5556 | 0.7375 | 0.6383 | 0.0000 |
| gpt-4o-mini | pasta | multi_v1 | 20 | 0.3500 | 0.3333 | 0.6747 | 0.5908 | 0.0000 |
| gpt-4o-mini | pasta | multi_v2 | 20 | 0.4000 | 0.4444 | 0.7483 | 0.6583 | 0.0500 |
| gpt-4o-mini | pasta | multi_v3 | 20 | 0.4000 | 0.4444 | 0.6350 | 0.5658 | 0.0500 |
| gpt-4o-mini | SocialIQA | single | 20 | 0.8500 | 0.8500 | 0.8833 | 0.8750 | 0.0000 |
| gpt-4o-mini | SocialIQA | multi_v1 | 20 | 0.6000 | 0.6000 | 0.8000 | 0.7417 | 0.0000 |
| gpt-4o-mini | SocialIQA | multi_v2 | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.0000 |
| gpt-4o-mini | SocialIQA | multi_v3 | 20 | 0.6500 | 0.6500 | 0.8167 | 0.7667 | 0.0000 |
| gpt-4o-mini | CosmosQA | single | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.1000 |
| gpt-4o-mini | CosmosQA | multi_v1 | 20 | 0.6500 | 0.6500 | 0.7367 | 0.7125 | 0.0500 |
| gpt-4o-mini | CosmosQA | multi_v2 | 20 | 0.8000 | 0.8000 | 0.8250 | 0.8167 | 0.0500 |
| gpt-4o-mini | CosmosQA | multi_v3 | 20 | 0.9000 | 0.9000 | 0.9250 | 0.9167 | 0.0000 |
| gpt-4o-mini | TempReason_T1 | single | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |
| gpt-4o-mini | TempReason_T1 | multi_v1 | 20 | 0.5500 | 0.5500 | 0.7300 | 0.6625 | 0.0000 |
| gpt-4o-mini | TempReason_T1 | multi_v2 | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |
| gpt-4o-mini | TempReason_T1 | multi_v3 | 20 | 0.5500 | 0.5500 | 0.7300 | 0.6625 | 0.0000 |
| gpt-4o-mini | TempReason_T5 | single | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| gpt-4o-mini | TempReason_T5 | multi_v1 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| gpt-4o-mini | TempReason_T5 | multi_v2 | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| gpt-4o-mini | TempReason_T5 | multi_v3 | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.1000 |

## Covered Task Layers Comparison (T1-T5 in covered layers)

| model | task_type | style | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |
|---|---|---|---:|---:|---:|---:|---:|---:|
| doubao-seed-1-8-251228 | T1 | single | 40 | 0.4250 | 0.8000 | 0.4917 | 0.4750 | 0.4750 |
| doubao-seed-1-8-251228 | T1 | multi_v1 | 40 | 0.4000 | 0.8000 | 0.4833 | 0.4625 | 0.4750 |
| doubao-seed-1-8-251228 | T1 | multi_v2 | 40 | 0.4000 | 0.8000 | 0.5000 | 0.4750 | 0.4500 |
| doubao-seed-1-8-251228 | T1 | multi_v3 | 40 | 0.4000 | 0.8000 | 0.4833 | 0.4625 | 0.4500 |
| doubao-seed-1-8-251228 | T2 | single | 20 | 0.2500 | 0.5556 | 0.3833 | 0.3500 | 0.5500 |
| doubao-seed-1-8-251228 | T2 | multi_v1 | 20 | 0.2500 | 0.4444 | 0.4033 | 0.3625 | 0.5000 |
| doubao-seed-1-8-251228 | T2 | multi_v2 | 20 | 0.2000 | 0.4444 | 0.4533 | 0.3875 | 0.4000 |
| doubao-seed-1-8-251228 | T2 | multi_v3 | 20 | 0.2500 | 0.4444 | 0.4367 | 0.3875 | 0.4500 |
| doubao-seed-1-8-251228 | T4 | single | 80 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.3875 |
| doubao-seed-1-8-251228 | T4 | multi_v1 | 80 | 0.4750 | 0.4750 | 0.4750 | 0.4750 | 0.4000 |
| doubao-seed-1-8-251228 | T4 | multi_v2 | 80 | 0.5250 | 0.5250 | 0.5250 | 0.5250 | 0.3125 |
| doubao-seed-1-8-251228 | T4 | multi_v3 | 80 | 0.5125 | 0.5125 | 0.5125 | 0.5125 | 0.3250 |
| doubao-seed-1-8-251228 | T5 | single | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | T5 | multi_v1 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | T5 | multi_v2 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | T5 | multi_v3 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | T1 | single | 40 | 0.3250 | 0.6500 | 0.3583 | 0.3500 | 0.6250 |
| doubao-seed-2-0-pro-260215 | T1 | multi_v1 | 40 | 0.3250 | 0.6500 | 0.3583 | 0.3500 | 0.6250 |
| doubao-seed-2-0-pro-260215 | T1 | multi_v2 | 40 | 0.3250 | 0.6500 | 0.3583 | 0.3500 | 0.6250 |
| doubao-seed-2-0-pro-260215 | T1 | multi_v3 | 40 | 0.2750 | 0.5500 | 0.3083 | 0.3000 | 0.6750 |
| doubao-seed-2-0-pro-260215 | T2 | single | 20 | 0.2500 | 0.5556 | 0.2833 | 0.2750 | 0.7000 |
| doubao-seed-2-0-pro-260215 | T2 | multi_v1 | 20 | 0.1500 | 0.3333 | 0.1833 | 0.1750 | 0.8000 |
| doubao-seed-2-0-pro-260215 | T2 | multi_v2 | 20 | 0.2500 | 0.5556 | 0.3500 | 0.3250 | 0.6000 |
| doubao-seed-2-0-pro-260215 | T2 | multi_v3 | 20 | 0.1000 | 0.2222 | 0.1667 | 0.1500 | 0.8000 |
| doubao-seed-2-0-pro-260215 | T4 | single | 80 | 0.3875 | 0.3875 | 0.3875 | 0.3875 | 0.6000 |
| doubao-seed-2-0-pro-260215 | T4 | multi_v1 | 80 | 0.3625 | 0.3625 | 0.3625 | 0.3625 | 0.6250 |
| doubao-seed-2-0-pro-260215 | T4 | multi_v2 | 80 | 0.4125 | 0.4125 | 0.4125 | 0.4125 | 0.5375 |
| doubao-seed-2-0-pro-260215 | T4 | multi_v3 | 80 | 0.3375 | 0.3375 | 0.3375 | 0.3375 | 0.6500 |
| doubao-seed-2-0-pro-260215 | T5 | single | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| doubao-seed-2-0-pro-260215 | T5 | multi_v1 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | T5 | multi_v2 | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| doubao-seed-2-0-pro-260215 | T5 | multi_v3 | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| gpt-4o-mini | T1 | single | 40 | 0.6000 | 0.9500 | 0.7667 | 0.7250 | 0.0250 |
| gpt-4o-mini | T1 | multi_v1 | 40 | 0.3250 | 0.5500 | 0.6483 | 0.5563 | 0.0500 |
| gpt-4o-mini | T1 | multi_v2 | 40 | 0.5750 | 0.9500 | 0.7417 | 0.7000 | 0.0500 |
| gpt-4o-mini | T1 | multi_v3 | 40 | 0.3000 | 0.5500 | 0.6225 | 0.5271 | 0.0250 |
| gpt-4o-mini | T2 | single | 20 | 0.3500 | 0.5556 | 0.7375 | 0.6383 | 0.0000 |
| gpt-4o-mini | T2 | multi_v1 | 20 | 0.3500 | 0.3333 | 0.6747 | 0.5908 | 0.0000 |
| gpt-4o-mini | T2 | multi_v2 | 20 | 0.4000 | 0.4444 | 0.7483 | 0.6583 | 0.0500 |
| gpt-4o-mini | T2 | multi_v3 | 20 | 0.4000 | 0.4444 | 0.6350 | 0.5658 | 0.0500 |
| gpt-4o-mini | T4 | single | 80 | 0.7375 | 0.7375 | 0.7542 | 0.7500 | 0.0375 |
| gpt-4o-mini | T4 | multi_v1 | 80 | 0.4875 | 0.4875 | 0.6442 | 0.5979 | 0.0125 |
| gpt-4o-mini | T4 | multi_v2 | 80 | 0.7000 | 0.7000 | 0.7063 | 0.7042 | 0.0250 |
| gpt-4o-mini | T4 | multi_v3 | 80 | 0.6125 | 0.6125 | 0.7417 | 0.7031 | 0.0000 |
| gpt-4o-mini | T5 | single | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| gpt-4o-mini | T5 | multi_v1 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| gpt-4o-mini | T5 | multi_v2 | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| gpt-4o-mini | T5 | multi_v3 | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.1000 |

## Analysis Notes

- This report is regenerated from saved predictions with corrected gold mapping: answer_key is first mapped to options.key.
- This run enforces strict paired evaluation: the same source_id is compared across 4 interaction styles.
- TempReason is split into two groups: TempReason_T1(full) and TempReason_T5(sample_T5), each sampled independently.
- Use model_task_style table to compare model behavior over covered task layers (including T1 and T5).