# 04. DROP 数据集说明

## 1. 数据集定位
- 任务类型：离散推理阅读理解（数值、比较、计数）
- 目录位置：data/DROP
- README 来源：data/DROP/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/DROP/DROP.jsonl: 86935
- 已统计主文件合计（非去重）：86935

## 3. 数据样例
- 样例来源：data/DROP/DROP.jsonl

```text
{"section_id": "nfl_2201", "query_id": "f16c0ee7-f131-4a8b-a6ac-4d275ea68066", "passage": "To start the season, the Lions traveled south to Tampa, Florida to take on the Tampa Bay Buccaneers. The Lions scored first in the first quarter with a 23-yard field goa ...
```

## 4. 数据构造方法
- 方法概述：从段落中抽取可执行离散运算的问题，答案可涉及算术、集合比较与实体抽取。
- README/文件线索：DROP is a QA dataset which tests comprehensive understanding of paragraphs. In；this crowdsourced, adversarially-created, 96k question-answering benchmark, a；For adding novel benchmarks/datasets to the library:

## 5. 数据构造目的
- 目标：衡量模型在长段落中结合文本证据做符号化推理的能力，而非仅做 span 匹配。

## 6. 你在使用前需要注意
- 关键注意事项：当前仓库以 jsonl 保存实例化样本；注意与官方原始 json 结构可能存在转换差异。
- README 摘要：Title: `DROP: A Reading Comprehension Benchmark Requiring Discrete Reasoning Over Paragraphs`
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。