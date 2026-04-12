# Dataset-to-Task Mapping (full)

## Converted
- CosmosQA: T4, sample_size=25262, files=data-converted/CosmosQA/full/CosmosQA_single.jsonl, data-converted/CosmosQA/full/CosmosQA_multi_v1.jsonl, data-converted/CosmosQA/full/CosmosQA_multi_v2.jsonl, data-converted/CosmosQA/full/CosmosQA_multi_v3.jsonl
- DROP: T4, sample_size=86935, files=data-converted/DROP/full/DROP_single.jsonl, data-converted/DROP/full/DROP_multi_v1.jsonl, data-converted/DROP/full/DROP_multi_v2.jsonl, data-converted/DROP/full/DROP_multi_v3.jsonl
- HellaSwag: T2, sample_size=39905, files=data-converted/HellaSwag/full/HellaSwag_single.jsonl, data-converted/HellaSwag/full/HellaSwag_multi_v1.jsonl, data-converted/HellaSwag/full/HellaSwag_multi_v2.jsonl, data-converted/HellaSwag/full/HellaSwag_multi_v3.jsonl
- MCTACO: T1, sample_size=3783, files=data-converted/MCTACO/full/MCTACO_single.jsonl, data-converted/MCTACO/full/MCTACO_multi_v1.jsonl, data-converted/MCTACO/full/MCTACO_multi_v2.jsonl, data-converted/MCTACO/full/MCTACO_multi_v3.jsonl
- narrative-qa: T4, sample_size=39447, files=data-converted/narrative-qa/full/narrative-qa_single.jsonl, data-converted/narrative-qa/full/narrative-qa_multi_v1.jsonl, data-converted/narrative-qa/full/narrative-qa_multi_v2.jsonl, data-converted/narrative-qa/full/narrative-qa_multi_v3.jsonl
- pasta: T2, sample_size=8476, files=data-converted/pasta/full/pasta_single.jsonl, data-converted/pasta/full/pasta_multi_v1.jsonl, data-converted/pasta/full/pasta_multi_v2.jsonl, data-converted/pasta/full/pasta_multi_v3.jsonl
- PIQA: T2, sample_size=16113, files=data-converted/PIQA/full/PIQA_single.jsonl, data-converted/PIQA/full/PIQA_multi_v1.jsonl, data-converted/PIQA/full/PIQA_multi_v2.jsonl, data-converted/PIQA/full/PIQA_multi_v3.jsonl
- qasper: T4, sample_size=615, files=data-converted/qasper/full/qasper_single.jsonl, data-converted/qasper/full/qasper_multi_v1.jsonl, data-converted/qasper/full/qasper_multi_v2.jsonl, data-converted/qasper/full/qasper_multi_v3.jsonl
- SI-Bench: T4, sample_size=2221, files=data-converted/SI-Bench/full/SI-Bench_single.jsonl, data-converted/SI-Bench/full/SI-Bench_multi_v1.jsonl, data-converted/SI-Bench/full/SI-Bench_multi_v2.jsonl, data-converted/SI-Bench/full/SI-Bench_multi_v3.jsonl
- SocialIQA: T4, sample_size=33410, files=data-converted/SocialIQA/full/SocialIQA_single.jsonl, data-converted/SocialIQA/full/SocialIQA_multi_v1.jsonl, data-converted/SocialIQA/full/SocialIQA_multi_v2.jsonl, data-converted/SocialIQA/full/SocialIQA_multi_v3.jsonl
- TempReason: T1, sample_size=400000, files=data-converted/TempReason/full/TempReason_single.jsonl, data-converted/TempReason/full/TempReason_multi_v1.jsonl, data-converted/TempReason/full/TempReason_multi_v2.jsonl, data-converted/TempReason/full/TempReason_multi_v3.jsonl
- TimeDial: T1, sample_size=1446, files=data-converted/TimeDial/full/TimeDial_single.jsonl, data-converted/TimeDial/full/TimeDial_multi_v1.jsonl, data-converted/TimeDial/full/TimeDial_multi_v2.jsonl, data-converted/TimeDial/full/TimeDial_multi_v3.jsonl
- TimeQA: T1, sample_size=2674, files=data-converted/TimeQA/full/TimeQA_single.jsonl, data-converted/TimeQA/full/TimeQA_multi_v1.jsonl, data-converted/TimeQA/full/TimeQA_multi_v2.jsonl, data-converted/TimeQA/full/TimeQA_multi_v3.jsonl
- tracie: T3, sample_size=1174, files=data-converted/tracie/full/tracie_single.jsonl, data-converted/tracie/full/tracie_multi_v1.jsonl, data-converted/tracie/full/tracie_multi_v2.jsonl, data-converted/tracie/full/tracie_multi_v3.jsonl
- UDST-DurationQA: T1, sample_size=40102, files=data-converted/UDST-DurationQA/full/UDST-DurationQA_single.jsonl, data-converted/UDST-DurationQA/full/UDST-DurationQA_multi_v1.jsonl, data-converted/UDST-DurationQA/full/UDST-DurationQA_multi_v2.jsonl, data-converted/UDST-DurationQA/full/UDST-DurationQA_multi_v3.jsonl

## Skipped with Reasons
- ATOMIC: 根据你的要求，ATOMIC 不进行改造。
- choice-75: 主标注文件结构不统一且关键标签定义不稳定（含 archived/中间产物），试运行阶段跳过。
- LongBench: 多子任务异构且多数非统一问答标签，单脚本高质量改造风险高，试运行阶段跳过。
- OpenPI2.0: 以过程状态结构化标注为主，缺少统一问答金标字段，试运行阶段跳过。
- ProPara: 原始任务需复杂过程状态对齐与多文件联动，试运行阶段跳过。
- situated_gen: 当前主文件缺少明确答案标签字段，无法保证“全部有正确答案”，跳过。
- TRaVelER: 目录主要为模型结果文件而非原始标注集，避免二次污染，跳过。
- TRIP: 当前可见数据以后处理样例为主，缺少稳定可扩展金标训练集，跳过。
- UDS_T_v1.0: 语义标注表非直接QA样式，改造成对话选择题需要额外任务定义，试运行阶段跳过。
- winogrande: 当前目录无主数据文件，仅README，跳过。