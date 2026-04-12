# 24. UDST-DurationQA 数据集说明

## 1. 数据集定位
- 任务类型：持续时间问答（二分类）
- 目录位置：data/UDST-DurationQA
- README 来源：data/UDST-DurationQA/LICENSE, data/UDST-DurationQA/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/UDST-DurationQA/data/train.tsv: 40102
- data/UDST-DurationQA/data/dev.tsv: 4924
- data/UDST-DurationQA/data/test.tsv: 4868
- 已统计主文件合计（非去重）：49894

## 3. 数据样例
- 样例来源：data/UDST-DurationQA/data/train.tsv

```text
I called the school most probably 10 times before I finally enrolled in a 20 hour package .	How long does it take for me to call the school?	52 minutes	yes I called the school most probably 10 times before I finally enrolled in a 20 hour package .	How long doe ...
```

## 4. 数据构造方法
- 方法概述：给定句子与“需要多长时间”问题，判断候选时长答案是否合理。
- README/文件线索：Dataset from the paper "Improving Event Duration Question Answering by Leveraging Existing Temporal Information Extraction Data"；### Overview of the dataset；We recast our data from the [UDS-T dataset](http://decomp.io/projects/time/).

## 5. 数据构造目的
- 目标：评估模型对事件持续时间常识的判别能力。

## 6. 你在使用前需要注意
- 关键注意事项：与 MCTACO 同属时间常识类，但任务格式更聚焦 duration。
- README 摘要：Dataset from the paper "Improving Event Duration Question Answering by Leveraging Existing Temporal Information Extraction Data" ------
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。