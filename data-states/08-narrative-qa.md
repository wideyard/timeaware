# 08. narrative-qa 数据集说明

## 1. 数据集定位
- 任务类型：叙事问答改写/切块数据
- 目录位置：data/narrative-qa
- README 来源：data/narrative-qa/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/narrative-qa/queries.jsonl: 39447
- data/narrative-qa/chunks.jsonl: 7807
- 已统计主文件合计（非去重）：47254

## 3. 数据样例
- 样例来源：data/narrative-qa/queries.jsonl

```text
{"og_query": "Who is Mark Hunter?", "query": "What role did Paige Woodward's actions play in the escalation of Mark Hunter's radio show's impact?", "chunk_id": "a782ad633c7aa8e20706eabdfbda2dcc_1", "answer": "He is a high school student in Phoenix."} {"og_quer ...
```

## 4. 数据构造方法
- 方法概述：将长篇叙事文档切分为 chunk，并为 query 关联 chunk_id 与答案。
- README/文件线索：dataset_info:；splits:；dataset_size: 5630946

## 5. 数据构造目的
- 目标：支持长叙事场景下的检索增强问答与问题重写研究。

## 6. 你在使用前需要注意
- 关键注意事项：本目录更像处理后的中间数据，不一定与官方 NarrativeQA 原始发布格式一致。
- README 摘要：--- dataset_info: - config_name: documents features: - name: chunk_id dtype: string - name: chunk dtype: string splits: - name: train num_bytes: 3968308 num_examples: 5502 - name: validation num_bytes: 399556 num_examples: 555 - name: test num_bytes: 1263082 num_examples: 1750 download_size: 3462955
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。