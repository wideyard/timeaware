# 13. qasper 数据集说明

## 1. 数据集定位
- 任务类型：学术论文问答（基于全文证据）
- 目录位置：data/qasper
- README 来源：data/qasper/README-test.md, data/qasper/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/qasper/qasper-train-v0.3.json: 888
- data/qasper/qasper-test-v0.3.json: 416
- data/qasper/qasper-dev-v0.3.json: 281
- 已统计主文件合计（非去重）：1585

## 3. 数据样例
- 样例来源：data/qasper/qasper-train-v0.3.json

```text
{'1909.00694': {'title': 'Minimally Supervised Learning of Affective Events Using Discourse Relations', 'abstract': 'Recognizing affective events that trigger positive or negative sentiment has a wide range of natural language processing applications but remai ...
```

## 4. 数据构造方法
- 方法概述：以论文为单位组织标题/摘要/全文片段和问题答案标注。
- README/文件线索：A Dataset of Information Seeking Questions and Answers Anchored in Research Papers；in the papers associated can be found here: https://qasper-dataset.s3.us-west-2.amazonaws.com/train_dev_figures_and_tables.tgz；Due to an issue in the annotation interface, a small number of annotations (about 0.6%) had multiple answer types (e.g.: unanswerable and boolean; see more information on answer types in the final section of this README) in v0.2. These were manually fixed to create v0.3. These fixes affected train, development, and test sets.

## 5. 数据构造目的
- 目标：评估模型在科研文档场景下的多跳证据检索与回答能力。

## 6. 你在使用前需要注意
- 关键注意事项：json 顶层通常为 paper_id 映射；训练/开发/测试按论文数切分。
- README 摘要：A Dataset of Information Seeking Questions and Answers Anchored in Research Papers ----------------------------------------------------------------------------------
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。