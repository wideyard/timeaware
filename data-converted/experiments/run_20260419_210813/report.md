# Benchmark Experiment Report (Single vs Random Multi)

- run_dir: D:/workspace/timeaware/data-converted/experiments/run_20260419_210813
- total_predictions: 2124
- styles: ['single', 'multi'] (multi randomly picks from ['multi_v1', 'multi_v2', 'multi_v3'])
- models: doubao-seed-1-8-251228, doubao-seed-2-0-pro-260215, gpt-4o-mini

## 1. Overall Performance

| model | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |
|---|---:|---:|---:|---:|---:|---:|
| doubao-seed-1-8-251228 | 708 | 0.7373 | 0.7763 | 0.7839 | 0.7722 | 0.0085 |
| doubao-seed-2-0-pro-260215 | 708 | 0.7486 | 0.7869 | 0.7960 | 0.7841 | 0.0000 |
| gpt-4o-mini | 708 | 0.7062 | 0.7534 | 0.7808 | 0.7605 | 0.0000 |

## 2. Style Comparison: Single vs Multi

| model | style | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |
|---|---|---:|---:|---:|---:|---:|---:|
| doubao-seed-1-8-251228 | single | 354 | 0.7373 | 0.7727 | 0.7843 | 0.7726 | 0.0113 |
| doubao-seed-1-8-251228 | multi | 354 | 0.7373 | 0.7798 | 0.7834 | 0.7719 | 0.0056 |
| doubao-seed-2-0-pro-260215 | single | 354 | 0.7542 | 0.7818 | 0.8012 | 0.7895 | 0.0000 |
| doubao-seed-2-0-pro-260215 | multi | 354 | 0.7429 | 0.7920 | 0.7909 | 0.7787 | 0.0000 |
| gpt-4o-mini | single | 354 | 0.7655 | 0.8121 | 0.8136 | 0.8013 | 0.0000 |
| gpt-4o-mini | multi | 354 | 0.6469 | 0.6942 | 0.7480 | 0.7197 | 0.0000 |

## 3. Performance by Task Tier

| tier | n | exact_match | single_choice_acc | f1 | jaccard |
|---|---:|---:|---:|---:|---:|
| T1 | 600 | 0.7133 | 0.8438 | 0.8183 | 0.7918 |
| T2 | 480 | 0.7979 | 0.8412 | 0.8614 | 0.8450 |
| T3 | 684 | 0.7295 | 0.7295 | 0.7635 | 0.7539 |
| T4 | 360 | 0.6722 | 0.6722 | 0.6796 | 0.6778 |

## 4. Model x Tier x Style Breakdown

| model | tier | style | n | exact_match | single_choice_acc | f1 | jaccard |
|---|---|---|---:|---:|---:|---:|---:|
| doubao-seed-1-8-251228 | T1 | single | 100 | 0.7400 | 0.8750 | 0.8480 | 0.8217 |
| doubao-seed-1-8-251228 | T1 | multi | 100 | 0.7600 | 0.8750 | 0.8413 | 0.8217 |
| doubao-seed-1-8-251228 | T2 | single | 80 | 0.8250 | 0.8421 | 0.8833 | 0.8688 |
| doubao-seed-1-8-251228 | T2 | multi | 80 | 0.8000 | 0.8767 | 0.8608 | 0.8448 |
| doubao-seed-1-8-251228 | T3 | single | 114 | 0.7456 | 0.7456 | 0.7558 | 0.7529 |
| doubao-seed-1-8-251228 | T3 | multi | 114 | 0.7544 | 0.7544 | 0.7836 | 0.7763 |
| doubao-seed-1-8-251228 | T4 | single | 60 | 0.6000 | 0.6000 | 0.6000 | 0.6000 |
| doubao-seed-1-8-251228 | T4 | multi | 60 | 0.5833 | 0.5833 | 0.5833 | 0.5833 |
| doubao-seed-2-0-pro-260215 | T1 | single | 100 | 0.7500 | 0.8625 | 0.8447 | 0.8217 |
| doubao-seed-2-0-pro-260215 | T1 | multi | 100 | 0.7000 | 0.8250 | 0.7947 | 0.7717 |
| doubao-seed-2-0-pro-260215 | T2 | single | 80 | 0.8375 | 0.8421 | 0.8792 | 0.8688 |
| doubao-seed-2-0-pro-260215 | T2 | multi | 80 | 0.8500 | 0.9315 | 0.9104 | 0.8938 |
| doubao-seed-2-0-pro-260215 | T3 | single | 114 | 0.7368 | 0.7368 | 0.7529 | 0.7485 |
| doubao-seed-2-0-pro-260215 | T3 | multi | 114 | 0.7456 | 0.7456 | 0.7632 | 0.7588 |
| doubao-seed-2-0-pro-260215 | T4 | single | 60 | 0.6833 | 0.6833 | 0.7167 | 0.7083 |
| doubao-seed-2-0-pro-260215 | T4 | multi | 60 | 0.6667 | 0.6667 | 0.6778 | 0.6750 |
| gpt-4o-mini | T1 | single | 100 | 0.7000 | 0.8625 | 0.8117 | 0.7833 |
| gpt-4o-mini | T1 | multi | 100 | 0.6300 | 0.7625 | 0.7697 | 0.7308 |
| gpt-4o-mini | T2 | single | 80 | 0.8125 | 0.8289 | 0.8625 | 0.8500 |
| gpt-4o-mini | T2 | multi | 80 | 0.6625 | 0.7260 | 0.7721 | 0.7442 |
| gpt-4o-mini | T3 | single | 114 | 0.7632 | 0.7632 | 0.7792 | 0.7749 |
| gpt-4o-mini | T3 | multi | 114 | 0.6316 | 0.6316 | 0.7462 | 0.7120 |
| gpt-4o-mini | T4 | single | 60 | 0.8167 | 0.8167 | 0.8167 | 0.8167 |
| gpt-4o-mini | T4 | multi | 60 | 0.6833 | 0.6833 | 0.6833 | 0.6833 |

## 5. Style Degradation Analysis (multi vs single)

How much does multi-turn noise degrade performance compared to single-turn?

### doubao-seed-1-8-251228
- Single exact_match: 0.7373 (354 samples)
- Multi exact_match: 0.7373 (354 samples)
- Degradation: +0.0000 (+0.0% relative)

### doubao-seed-2-0-pro-260215
- Single exact_match: 0.7542 (354 samples)
- Multi exact_match: 0.7429 (354 samples)
- Degradation: +0.0113 (+1.5% relative)

### gpt-4o-mini
- Single exact_match: 0.7655 (354 samples)
- Multi exact_match: 0.6469 (354 samples)
- Degradation: +0.1186 (+15.5% relative)

## 6. Per-Dataset Results

| dataset | tier | style | n | exact_match | single_choice_acc | f1 | jaccard |
|---|---|---|---:|---:|---:|---:|---:|
