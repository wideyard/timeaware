# 23. UDS_T_v1.0 数据集说明

## 1. 数据集定位
- 任务类型：事件时间结构标注（Universal Decompositional Semantics - Time）
- 目录位置：data/UDS_T_v1.0
- README 来源：data/UDS_T_v1.0/LICENSE, data/UDS_T_v1.0/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/UDS_T_v1.0/time_eng_ud_v1.2_2015_10_30.tsv: 91919
- 已统计主文件合计（非去重）：91919

## 3. 数据样例
- 样例来源：data/UDS_T_v1.0/time_eng_ud_v1.2_2015_10_30.tsv

```text
Split	Annotator.ID	Sentence1.ID	Pred1.Span	Pred1.Token	Event1.ID	Sentence2.ID	Pred2.Span	Pred2.Token	Event2.ID	Pred1.Text	Pred1.Lemma	Pred2.Text	Pred2.Lemma	Pred1.Duration	Pred2.Duration	Pred1.Beg	Pred1.End	Pred2.Beg	Pred2.End	Pred1.Duration.Confidence	Pred2.D ...
```

## 4. 数据构造方法
- 方法概述：在 UD 语料上对事件持续时间、起止区间和事件间关系进行细粒度标注。
- README/文件线索：This archive contains data collected from the protocols described in the following paper.；If you make use of this dataset in a presentation or publication, we ask that you please cite this paper.；The file `time_eng_ud_v1.2_2015_10_30.tsv` corresponds to the data reported in Vashishtha et al. 2019. The file contains temporal relation annotations developed from the the [Universal Dependencies v1.2 dataset](https://github.com/UniversalDependencies/UD_English-EWT/releases/tag/r1.2). The document ids of the UDv1.2 sentences can be found in a [later version](https://github.com/UniversalDependencies/UD_English-EWT/blob/master/en_ewt-ud-train.conllu).

## 5. 数据构造目的
- 目标：支持时间语义解析、时序关系建模和可解释时间推理研究。

## 6. 你在使用前需要注意
- 关键注意事项：tsv 字段较多，建模前建议先做字段字典与取值清洗。
- README 摘要：This archive contains data collected from the protocols described in the following paper.
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。