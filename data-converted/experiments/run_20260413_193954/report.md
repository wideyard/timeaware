# Batch Experiment Report

- run_dir: data-converted/experiments/run_20260413_193954
- datasets: 13
- max_per_dataset: 20
- styles: single, multi_v1, multi_v2, multi_v3
- models: gpt-4o-mini, doubao-seed-1-8-251228, doubao-seed-2-0-pro-260215

## Overall by Model and Style

| model | style | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| doubao-seed-1-8-251228 | single | 268 | 0.7276 | 0.7787 | 0.7629 | 0.7544 | 0.1194 |
| doubao-seed-1-8-251228 | multi_v1 | 267 | 0.7079 | 0.7695 | 0.7453 | 0.7360 | 0.1348 |
| doubao-seed-1-8-251228 | multi_v2 | 266 | 0.7180 | 0.7769 | 0.7687 | 0.7563 | 0.1128 |
| doubao-seed-1-8-251228 | multi_v3 | 267 | 0.7416 | 0.7942 | 0.7815 | 0.7715 | 0.0861 |
| doubao-seed-2-0-pro-260215 | single | 267 | 0.6779 | 0.7284 | 0.7029 | 0.6966 | 0.2247 |
| doubao-seed-2-0-pro-260215 | multi_v1 | 266 | 0.6729 | 0.7355 | 0.6980 | 0.6917 | 0.2368 |
| doubao-seed-2-0-pro-260215 | multi_v2 | 266 | 0.6955 | 0.7603 | 0.7281 | 0.7199 | 0.1917 |
| doubao-seed-2-0-pro-260215 | multi_v3 | 266 | 0.6692 | 0.7314 | 0.6892 | 0.6842 | 0.2519 |
| gpt-4o-mini | single | 268 | 0.7388 | 0.7992 | 0.7985 | 0.7836 | 0.0224 |
| gpt-4o-mini | multi_v1 | 268 | 0.5448 | 0.5861 | 0.7330 | 0.6796 | 0.0112 |
| gpt-4o-mini | multi_v2 | 267 | 0.7303 | 0.7901 | 0.7964 | 0.7796 | 0.0225 |
| gpt-4o-mini | multi_v3 | 267 | 0.6105 | 0.6626 | 0.7544 | 0.7141 | 0.0112 |

## Dataset Breakdown (model_style_dataset)

| model | style | dataset | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |
|---|---|---|---:|---:|---:|---:|---:|---:|
| doubao-seed-1-8-251228 | single | CosmosQA | 28 | 0.6429 | 0.6429 | 0.6429 | 0.6429 | 0.0357 |
| doubao-seed-1-8-251228 | single | DROP | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.2000 |
| doubao-seed-1-8-251228 | single | HellaSwag | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.0500 |
| doubao-seed-1-8-251228 | single | PIQA | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |
| doubao-seed-1-8-251228 | single | SI-Bench | 20 | 0.3500 | 0.3500 | 0.3833 | 0.3750 | 0.2500 |
| doubao-seed-1-8-251228 | single | SocialIQA | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1500 |
| doubao-seed-1-8-251228 | single | TempReason | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | single | TimeDial | 20 | 0.2000 | 0.0000 | 0.5400 | 0.4583 | 0.3000 |
| doubao-seed-1-8-251228 | single | TimeQA | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | single | narrative-qa | 20 | 0.6500 | 0.6500 | 0.6500 | 0.6500 | 0.2000 |
| doubao-seed-1-8-251228 | single | pasta | 20 | 0.7000 | 0.8125 | 0.8000 | 0.7750 | 0.1000 |
| doubao-seed-1-8-251228 | single | qasper | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.1500 |
| doubao-seed-1-8-251228 | single | tracie | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.1500 |
| doubao-seed-1-8-251228 | multi_v1 | CosmosQA | 27 | 0.5926 | 0.5926 | 0.5926 | 0.5926 | 0.1111 |
| doubao-seed-1-8-251228 | multi_v1 | DROP | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.1000 |
| doubao-seed-1-8-251228 | multi_v1 | HellaSwag | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1500 |
| doubao-seed-1-8-251228 | multi_v1 | PIQA | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| doubao-seed-1-8-251228 | multi_v1 | SI-Bench | 20 | 0.3500 | 0.3500 | 0.3833 | 0.3750 | 0.1500 |
| doubao-seed-1-8-251228 | multi_v1 | SocialIQA | 20 | 0.6500 | 0.6500 | 0.6500 | 0.6500 | 0.3000 |
| doubao-seed-1-8-251228 | multi_v1 | TempReason | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | multi_v1 | TimeDial | 20 | 0.0500 | 0.0000 | 0.4167 | 0.3250 | 0.4000 |
| doubao-seed-1-8-251228 | multi_v1 | TimeQA | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | multi_v1 | narrative-qa | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1000 |
| doubao-seed-1-8-251228 | multi_v1 | pasta | 20 | 0.6500 | 0.7500 | 0.7500 | 0.7250 | 0.2000 |
| doubao-seed-1-8-251228 | multi_v1 | qasper | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1000 |
| doubao-seed-1-8-251228 | multi_v1 | tracie | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.1000 |
| doubao-seed-1-8-251228 | multi_v2 | CosmosQA | 26 | 0.5769 | 0.5769 | 0.5769 | 0.5769 | 0.1154 |
| doubao-seed-1-8-251228 | multi_v2 | DROP | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.2000 |
| doubao-seed-1-8-251228 | multi_v2 | HellaSwag | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1500 |
| doubao-seed-1-8-251228 | multi_v2 | PIQA | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| doubao-seed-1-8-251228 | multi_v2 | SI-Bench | 20 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.0500 |
| doubao-seed-1-8-251228 | multi_v2 | SocialIQA | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.2000 |
| doubao-seed-1-8-251228 | multi_v2 | TempReason | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | multi_v2 | TimeDial | 20 | 0.1000 | 0.0000 | 0.5067 | 0.4083 | 0.3000 |
| doubao-seed-1-8-251228 | multi_v2 | TimeQA | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | multi_v2 | narrative-qa | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1000 |
| doubao-seed-1-8-251228 | multi_v2 | pasta | 20 | 0.6000 | 0.6875 | 0.8333 | 0.7750 | 0.0500 |
| doubao-seed-1-8-251228 | multi_v2 | qasper | 20 | 0.8000 | 0.8000 | 0.8333 | 0.8250 | 0.1000 |
| doubao-seed-1-8-251228 | multi_v2 | tracie | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.1500 |
| doubao-seed-1-8-251228 | multi_v3 | CosmosQA | 27 | 0.6667 | 0.6667 | 0.6667 | 0.6667 | 0.0370 |
| doubao-seed-1-8-251228 | multi_v3 | DROP | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.1000 |
| doubao-seed-1-8-251228 | multi_v3 | HellaSwag | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1000 |
| doubao-seed-1-8-251228 | multi_v3 | PIQA | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.0500 |
| doubao-seed-1-8-251228 | multi_v3 | SI-Bench | 20 | 0.3500 | 0.3500 | 0.3500 | 0.3500 | 0.1500 |
| doubao-seed-1-8-251228 | multi_v3 | SocialIQA | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1000 |
| doubao-seed-1-8-251228 | multi_v3 | TempReason | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | multi_v3 | TimeDial | 20 | 0.2000 | 0.0000 | 0.5667 | 0.4750 | 0.2500 |
| doubao-seed-1-8-251228 | multi_v3 | TimeQA | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-1-8-251228 | multi_v3 | narrative-qa | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.1000 |
| doubao-seed-1-8-251228 | multi_v3 | pasta | 20 | 0.6500 | 0.7500 | 0.8167 | 0.7750 | 0.1000 |
| doubao-seed-1-8-251228 | multi_v3 | qasper | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.0500 |
| doubao-seed-1-8-251228 | multi_v3 | tracie | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.1000 |
| doubao-seed-2-0-pro-260215 | single | CosmosQA | 27 | 0.4815 | 0.4815 | 0.4815 | 0.4815 | 0.2222 |
| doubao-seed-2-0-pro-260215 | single | DROP | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.2000 |
| doubao-seed-2-0-pro-260215 | single | HellaSwag | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1500 |
| doubao-seed-2-0-pro-260215 | single | PIQA | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| doubao-seed-2-0-pro-260215 | single | SI-Bench | 20 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.7000 |
| doubao-seed-2-0-pro-260215 | single | SocialIQA | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.2500 |
| doubao-seed-2-0-pro-260215 | single | TempReason | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | single | TimeDial | 20 | 0.1000 | 0.0000 | 0.3667 | 0.3000 | 0.5000 |
| doubao-seed-2-0-pro-260215 | single | TimeQA | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | single | narrative-qa | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.1500 |
| doubao-seed-2-0-pro-260215 | single | pasta | 20 | 0.7000 | 0.7500 | 0.7667 | 0.7500 | 0.2000 |
| doubao-seed-2-0-pro-260215 | single | qasper | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.3000 |
| doubao-seed-2-0-pro-260215 | single | tracie | 20 | 0.6500 | 0.6500 | 0.6500 | 0.6500 | 0.2000 |
| doubao-seed-2-0-pro-260215 | multi_v1 | CosmosQA | 26 | 0.4615 | 0.4615 | 0.4615 | 0.4615 | 0.3462 |
| doubao-seed-2-0-pro-260215 | multi_v1 | DROP | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.1500 |
| doubao-seed-2-0-pro-260215 | multi_v1 | HellaSwag | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.2000 |
| doubao-seed-2-0-pro-260215 | multi_v1 | PIQA | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0500 |
| doubao-seed-2-0-pro-260215 | multi_v1 | SI-Bench | 20 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.7000 |
| doubao-seed-2-0-pro-260215 | multi_v1 | SocialIQA | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.2000 |
| doubao-seed-2-0-pro-260215 | multi_v1 | TempReason | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | multi_v1 | TimeDial | 20 | 0.0000 | 0.0000 | 0.3000 | 0.2250 | 0.5500 |
| doubao-seed-2-0-pro-260215 | multi_v1 | TimeQA | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | multi_v1 | narrative-qa | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1000 |
| doubao-seed-2-0-pro-260215 | multi_v1 | pasta | 20 | 0.6500 | 0.7500 | 0.6833 | 0.6750 | 0.3000 |
| doubao-seed-2-0-pro-260215 | multi_v1 | qasper | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.2500 |
| doubao-seed-2-0-pro-260215 | multi_v1 | tracie | 20 | 0.6500 | 0.6500 | 0.6500 | 0.6500 | 0.2000 |
| doubao-seed-2-0-pro-260215 | multi_v2 | CosmosQA | 26 | 0.5769 | 0.5769 | 0.5769 | 0.5769 | 0.2308 |
| doubao-seed-2-0-pro-260215 | multi_v2 | DROP | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.2000 |
| doubao-seed-2-0-pro-260215 | multi_v2 | HellaSwag | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1500 |
| doubao-seed-2-0-pro-260215 | multi_v2 | PIQA | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.1000 |
| doubao-seed-2-0-pro-260215 | multi_v2 | SI-Bench | 20 | 0.3500 | 0.3500 | 0.3500 | 0.3500 | 0.4000 |
| doubao-seed-2-0-pro-260215 | multi_v2 | SocialIQA | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.2500 |
| doubao-seed-2-0-pro-260215 | multi_v2 | TempReason | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | multi_v2 | TimeDial | 20 | 0.0000 | 0.0000 | 0.3667 | 0.2750 | 0.4500 |
| doubao-seed-2-0-pro-260215 | multi_v2 | TimeQA | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | multi_v2 | narrative-qa | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.1000 |
| doubao-seed-2-0-pro-260215 | multi_v2 | pasta | 20 | 0.6500 | 0.7500 | 0.7167 | 0.7000 | 0.2500 |
| doubao-seed-2-0-pro-260215 | multi_v2 | qasper | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.2000 |
| doubao-seed-2-0-pro-260215 | multi_v2 | tracie | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.1500 |
| doubao-seed-2-0-pro-260215 | multi_v3 | CosmosQA | 26 | 0.5385 | 0.5385 | 0.5385 | 0.5385 | 0.2692 |
| doubao-seed-2-0-pro-260215 | multi_v3 | DROP | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.1500 |
| doubao-seed-2-0-pro-260215 | multi_v3 | HellaSwag | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.2000 |
| doubao-seed-2-0-pro-260215 | multi_v3 | PIQA | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.1000 |
| doubao-seed-2-0-pro-260215 | multi_v3 | SI-Bench | 20 | 0.0500 | 0.0500 | 0.0500 | 0.0500 | 0.9000 |
| doubao-seed-2-0-pro-260215 | multi_v3 | SocialIQA | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.2000 |
| doubao-seed-2-0-pro-260215 | multi_v3 | TempReason | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | multi_v3 | TimeDial | 20 | 0.0000 | 0.0000 | 0.2000 | 0.1500 | 0.7000 |
| doubao-seed-2-0-pro-260215 | multi_v3 | TimeQA | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| doubao-seed-2-0-pro-260215 | multi_v3 | narrative-qa | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.2000 |
| doubao-seed-2-0-pro-260215 | multi_v3 | pasta | 20 | 0.6500 | 0.7500 | 0.7167 | 0.7000 | 0.2500 |
| doubao-seed-2-0-pro-260215 | multi_v3 | qasper | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1500 |
| doubao-seed-2-0-pro-260215 | multi_v3 | tracie | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.1500 |
| gpt-4o-mini | single | CosmosQA | 28 | 0.7857 | 0.7857 | 0.8095 | 0.8036 | 0.0000 |
| gpt-4o-mini | single | DROP | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.0500 |
| gpt-4o-mini | single | HellaSwag | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.0000 |
| gpt-4o-mini | single | PIQA | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.1000 |
| gpt-4o-mini | single | SI-Bench | 20 | 0.5500 | 0.5500 | 0.5500 | 0.5500 | 0.0000 |
| gpt-4o-mini | single | SocialIQA | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.0500 |
| gpt-4o-mini | single | TempReason | 20 | 0.9500 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |
| gpt-4o-mini | single | TimeDial | 20 | 0.0500 | 0.0000 | 0.5833 | 0.4500 | 0.0000 |
| gpt-4o-mini | single | TimeQA | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| gpt-4o-mini | single | narrative-qa | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.0500 |
| gpt-4o-mini | single | pasta | 20 | 0.7000 | 0.7500 | 0.9000 | 0.8500 | 0.0000 |
| gpt-4o-mini | single | qasper | 20 | 0.9000 | 0.9000 | 0.9333 | 0.9250 | 0.0500 |
| gpt-4o-mini | single | tracie | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.0000 |
| gpt-4o-mini | multi_v1 | CosmosQA | 28 | 0.5714 | 0.5714 | 0.7786 | 0.7202 | 0.0000 |
| gpt-4o-mini | multi_v1 | DROP | 20 | 0.2500 | 0.2500 | 0.5767 | 0.4750 | 0.0000 |
| gpt-4o-mini | multi_v1 | HellaSwag | 20 | 0.7000 | 0.7000 | 0.8333 | 0.8000 | 0.0000 |
| gpt-4o-mini | multi_v1 | PIQA | 20 | 0.6500 | 0.6500 | 0.7500 | 0.7250 | 0.1000 |
| gpt-4o-mini | multi_v1 | SI-Bench | 20 | 0.2500 | 0.2500 | 0.3750 | 0.3417 | 0.0000 |
| gpt-4o-mini | multi_v1 | SocialIQA | 20 | 0.4000 | 0.4000 | 0.6667 | 0.5833 | 0.0000 |
| gpt-4o-mini | multi_v1 | TempReason | 20 | 0.4500 | 0.4500 | 0.6700 | 0.5875 | 0.0000 |
| gpt-4o-mini | multi_v1 | TimeDial | 20 | 0.1500 | 0.0000 | 0.7033 | 0.5667 | 0.0000 |
| gpt-4o-mini | multi_v1 | TimeQA | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| gpt-4o-mini | multi_v1 | narrative-qa | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.0000 |
| gpt-4o-mini | multi_v1 | pasta | 20 | 0.3000 | 0.3750 | 0.7202 | 0.6067 | 0.0000 |
| gpt-4o-mini | multi_v1 | qasper | 20 | 0.9000 | 0.9000 | 0.9200 | 0.9125 | 0.0000 |
| gpt-4o-mini | multi_v1 | tracie | 20 | 0.6500 | 0.6500 | 0.7167 | 0.7000 | 0.0500 |
| gpt-4o-mini | multi_v2 | CosmosQA | 27 | 0.8148 | 0.8148 | 0.8148 | 0.8148 | 0.0000 |
| gpt-4o-mini | multi_v2 | DROP | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.0000 |
| gpt-4o-mini | multi_v2 | HellaSwag | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.0000 |
| gpt-4o-mini | multi_v2 | PIQA | 20 | 0.8000 | 0.8000 | 0.8000 | 0.8000 | 0.1500 |
| gpt-4o-mini | multi_v2 | SI-Bench | 20 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.0000 |
| gpt-4o-mini | multi_v2 | SocialIQA | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.0500 |
| gpt-4o-mini | multi_v2 | TempReason | 20 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 0.0500 |
| gpt-4o-mini | multi_v2 | TimeDial | 20 | 0.0500 | 0.0000 | 0.5817 | 0.4500 | 0.0000 |
| gpt-4o-mini | multi_v2 | TimeQA | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| gpt-4o-mini | multi_v2 | narrative-qa | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.0500 |
| gpt-4o-mini | multi_v2 | pasta | 20 | 0.5000 | 0.5000 | 0.8167 | 0.7333 | 0.0000 |
| gpt-4o-mini | multi_v2 | qasper | 20 | 0.9000 | 0.9000 | 0.9333 | 0.9250 | 0.0000 |
| gpt-4o-mini | multi_v2 | tracie | 20 | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.0000 |
| gpt-4o-mini | multi_v3 | CosmosQA | 27 | 0.6296 | 0.6296 | 0.7160 | 0.6914 | 0.0000 |
| gpt-4o-mini | multi_v3 | DROP | 20 | 0.7500 | 0.7500 | 0.8433 | 0.8125 | 0.0000 |
| gpt-4o-mini | multi_v3 | HellaSwag | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.0000 |
| gpt-4o-mini | multi_v3 | PIQA | 20 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.1000 |
| gpt-4o-mini | multi_v3 | SI-Bench | 20 | 0.1000 | 0.1000 | 0.4417 | 0.3500 | 0.0000 |
| gpt-4o-mini | multi_v3 | SocialIQA | 20 | 0.5500 | 0.5500 | 0.7000 | 0.6500 | 0.0000 |
| gpt-4o-mini | multi_v3 | TempReason | 20 | 0.6500 | 0.6500 | 0.7900 | 0.7375 | 0.0000 |
| gpt-4o-mini | multi_v3 | TimeDial | 20 | 0.0000 | 0.0000 | 0.5667 | 0.4167 | 0.0500 |
| gpt-4o-mini | multi_v3 | TimeQA | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| gpt-4o-mini | multi_v3 | narrative-qa | 20 | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.0000 |
| gpt-4o-mini | multi_v3 | pasta | 20 | 0.2500 | 0.1875 | 0.7300 | 0.6083 | 0.0000 |
| gpt-4o-mini | multi_v3 | qasper | 20 | 0.9500 | 0.9500 | 0.9833 | 0.9750 | 0.0000 |
| gpt-4o-mini | multi_v3 | tracie | 20 | 0.6500 | 0.6500 | 0.6500 | 0.6500 | 0.0000 |

## Source-Level Cross-Style Comparison Tables

- doubao-seed-1-8-251228: data-converted/experiments/run_20260413_193954/predictions/source_style_comparison_doubao-seed-1-8-251228.csv
- doubao-seed-2-0-pro-260215: data-converted/experiments/run_20260413_193954/predictions/source_style_comparison_doubao-seed-2-0-pro-260215.csv
- gpt-4o-mini: data-converted/experiments/run_20260413_193954/predictions/source_style_comparison_gpt-4o-mini.csv
