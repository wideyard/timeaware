# TimeAware 数据集分析报告

## 概览

`data` 目录包含17个时间推理相关数据集，总计约850MB，600,000+行数据。

| 数据集 | 文件大小 | 主要文件 | 数据量 | 映射任务 |
|--------|----------|----------|--------|---------|
| **时间推理 (T1)** ||||
| MCTACO | 2.8MB | dev/test.tsv | 13,225行 | T1 |
| UDST-DurationQA | 8.7MB | train/dev/test.tsv | 49,894行 | T1 |
| TimeQA | 4MB | annotated_*.json | 10,000+行 | T1 |
| DROP | 12MB | train/dev.parquet | 77,400行 | T1 |
| TimeDial | 1.6MB | test.json | 1,446对话 | T1 |
| **状态追踪 (T2)** ||||
| TRACIE | 54MB | train/test.txt | 10,870行 | T2 |
| situated_gen | 4.7MB | train/dev/test.jsonl | 8,268行 | T2 |
| bAbI | 255KB | qa*.txt | ~10,000行 | T2 |
| ProPara | 71MB | prolocal*.tsv | ~5,000行 | T2 |
| **并发冲突 (T3)** ||||
| SocialIQA | 8.3MB | train/dev/test.jsonl | 33,000+行 | T3 |
| CosmosQA | 25MB | train/dev/test.jsonl | 35,000+行 | T3 |
| ATOMIC | 9.6MB | 需下载 | - | T3 |
| **长期记忆 (T4)** ||||
| QASPer | 67MB | qasper-*-v0.3.json | 5,049问答 | T4 |
| LongBench | 350MB | 需要加载 | 多任务 | T4 |
| NarrativeQA | 22MB | 需下载 | - | T4 |
| **反事实 (T5)** ||||
| PIQA | 6.3MB | tests.jsonl | 30,000+行 | T5 |
| HellaSwag | 69MB | 需要下载 | - | T5 |
| Winogrande | 8MB | winogrande_*.parquet | 81,442样本 | T5 |

---

## 1. MCTACO

**来源**: EMNLP 2019 paper "Going on a vacation" takes longer than "Going for a walk": A Study of Temporal Commonsense Understanding

### 数据格式
TSV格式，5列：
1. 上下文句子
2. 问题
3. 答案
4. 标签 (yes/no)
5. 时间类别

时间类别包括：
- Stationarity (稳定性)
- Event Duration (事件持续时间)
- Event Ordering (事件顺序)
- Frequency (频率)

### 数据规模
- dev_3783.tsv: 3,783行
- test_9442.tsv: 9,442行

### 示例
```
Islam later emerged as the majority religion during the centuries of Ottoman rule, though a significant Christian minority remained.	Is Islam still the majority religion?	yes	yes	Stationarity
Islam later emerged as the majority religion during the centuries of Ottoman rule, though a significant Christian minority remained.	How long has a significant Christian minority remained?	hundreds of years	yes	Event Duration
```

### 任务类型
时间常识理解问答系统，需要模型理解：
- 事件是否仍在持续
- 事件的合理持续时间
- 事件发生的先后顺序
- 事件的频率

---

## 2. situated_gen

**来源**: NeurIPS 2023 "SituatedGen: Incorporating Geographical and Temporal Contexts into Generative Commonsense Reasoning"

### 数据格式
JSONL格式，每个样本包含：
- `keywords`: 输入关键词列表
- `statement`: 目标输出句子
- `ids`: 来源数据集ID
- `keywords_pos`: 关键词在句子中的位置标记
- `statements`: 拆分后的两个句子

### 数据规模
- train.jsonl: 5,641行
- dev.jsonl: 1,407行
- test.jsonl: 1,220行

### 示例
```json
{
  "keywords": ["March", "calendar", "English", "December", "September", "August", "October", "winter"],
  "statement": "Winter begins in December and ends in March. September comes after August, but before October in English calendar.",
  "ids": ["openbookqa::Additional/crowdsourced-facts.txt::5091", "creak::train::9297"],
  "keywords_pos": [0, 1, 1, 0, 1, 1, 1, 0],
  "statements": [
    "Winter begins in December and ends in March.",
    "September comes after August, but before October in English calendar."
  ]
}
```

### 任务类型
生成式常识推理，结合地理和时间上下文，根据关键词生成包含时间/空间信息的自然语句。

---

## 3. TempReason

**来源**: 时间推理问答数据集

### 数据格式
需从Hugging Face下载（数据集较大）
```bash
git lfs install
git clone https://huggingface.co/datasets/tonytan48/TempReason
```

### 数据规模
- 完整数据集存储在外部仓库

### 任务类型
时间推理问答

---

## 4. TimeDial

**来源**: ACL 2022 Findings "TimeDial: A Temporal Commonsense Reasoning Benchmark for Dialogue"

### 数据格式
JSON数组格式，每个元素包含：
- `conversation`: 对话列表
- `id`: 对话ID
- `correct1`, `correct2`: 正确答案
- `incorrect1`, `incorrect2`: 错误答案及规则
- `incorrect1_rule`, `incorrect2_rule`: 错误原因规则

### 数据规模
- test.json: 1个文件，包含多个对话样本

### 示例
```json
{
  "conversation": [
    "A:We need to take the accounts system offline to carry out the upgrade . But don't worry , it won't cause too much inconvenience . We're going to do it over the weekend .",
    "B: How long will the system be down for ?",
    "A: We'll be taking everything offline in about two hours ' time . It'll be down for a minimum of twelve hours . If everything goes according to plan , it should be up again by 6 pm on Saturday .",
    "B: That's fine . We've allowed <MASK> to be on the safe side ."
  ],
  "id": 1,
  "correct1": "forty-eight hours",
  "correct2": "50 hours",
  "incorrect1": "two hours",
  "incorrect1_rule": "Rule 1",
  "incorrect2": "12 days",
  "incorrect2_rule": "Rule 2"
}
```

### 任务类型
对话中的时间推理，需要根据对话上下文填充 `<MASK>` 位置的时间表达式。

---

## 5. TRACIE

**来源**: NAACL 2021 "Temporal Reasoning on Implicit Events from Distant Supervision"

### 数据格式
文本格式，每行包含：
- `event`: 事件描述 + 时间关系（starts after/before）
- `story`: 上下文故事
- `answer`: positive/negative（判断时间关系是否正确）

### 数据规模
- tracie_train.txt: 1,174行
- tracie_test.txt: 4,248行

另有多个变体格式：
- IID格式
- Uniform-Prior格式
- Symbolic格式
- MATRES格式

### 示例
```
event: Chad looked for his baseball cap starts after he got off the ride story: Chad had gone to an amusement park. He was riding on the roller coaster. Chad was wearing a baseball cap. The baseball cap fell off of Chad's head. Chad found the cap after he got off of the ride.	answer: positive
event: Chad looked for his baseball cap starts before he got off the ride story: Chad had gone to an amusement park. He was riding on the roller coaster. Chad was wearing a baseball cap. The baseball cap fell off of Chad's head. Chad found the cap after he got off of the ride.	answer: negative
```

### 任务类型
隐式事件的时间顺序推理，判断给定事件对之间的时间关系是否正确。

---

## 6. UDS_T_v1.0

**来源**: "Fine-Grained Temporal Relation Extraction" (Vashishtha et al., 2019)

### 数据格式
TSV格式，23列，包含丰富的时间标注信息：

| 列名 | 描述 | 值示例 |
|------|------|--------|
| Split | 数据集划分 | train, dev, test |
| Annotator.ID | 标注者ID | 0-764 |
| Sentence1.ID | 第一个句子ID | en-ud-train.conllu 418 |
| Pred1.Span | 第一个谓词跨度 | 17 |
| Event1.ID | 第一个事件ID | en-ud-train.conllu 418_17 |
| Sentence2.ID | 第二个句子ID | en-ud-train.conllu 418 |
| Pred2.Span | 第二个谓词跨度 | 18_19 |
| Event2.ID | 第二个事件ID | en-ud-train.conllu 418_19 |
| Pred1.Text | 第一个谓词文本 | think |
| Pred1.Lemma | 第一个谓词词元 | think |
| Pred2.Text | 第二个谓词文本 | is intentional |
| Pred2.Lemma | 第二个谓词词元 | intentional |
| Pred1.Duration | 第一个谓词持续时间标签 | 0-10 |
| Pred2.Duration | 第二个谓词持续时间标签 | 0-10 |
| Pred1.Beg | 第一个谓词开始点 | 0-100 |
| Pred1.End | 第一个谓词结束点 | 0-100 |
| Pred2.Beg | 第二个谓词开始点 | 0-100 |
| Pred2.End | 第二个谓词结束点 | 0-100 |
| Pred1.Duration.Confidence | 第一个谓词持续时间置信度 | 0-4 |
| Pred2.Duration.Confidence | 第二个谓词持续时间置信度 | 0-4 |
| Relation.Confidence | 关系标注置信度 | 0-4 |
| Document.ID | 文档ID | 10 |

### 数据规模
- time_eng_ud_v1.2_2015_10_30.tsv: 91,919行

### 示例
```
train	209	en-ud-train.conllu 418	17	17	en-ud-train.conllu 418_17	en-ud-train.conllu 418	18_19	19	en-ud-train.conllu 418_19	think	think	is intentional	intentional	2	0	35 	 41	64 	 65	4.0	4.0	4.0	10
```

### 任务类型
细粒度时间关系提取，包括：
- 事件持续时间分类
- 事件起止点标注
- 时间关系抽取

---

## 7. UDST-DurationQA

**来源**: LREC 2022 "Improving Event Duration Question Answering by Leveraging Existing Temporal Information Extraction Data"

### 数据格式
TSV格式，4列：
1. 句子（上下文）
2. 问题
3. 答案
4. 标签 (yes/no)

### 数据规模
- train.tsv: 40,102行
- dev.tsv: 4,924行
- test.tsv: 4,868行

### 示例
```
I called the school most probably 10 times before I finally enrolled in a 20 hour package .	How long does it take for me to call the school?	52 minutes	yes
I called the school most probably 10 times before I finally enrolled in a 20 hour package .	How long does it take for me to enroll in a 20 hour package?	45 minutes	yes
can i buy a laptop in u.k and then take it to rep. ireland and put a irish pay , go dongle in it ?	How long did it take for me to buy a laptop?	5 minutes	yes
can i buy a laptop in u.k and then take it to rep. ireland and put a irish pay , go dongle in it ?	How long did it take for me to buy a laptop?	several minutes	yes
```

### 任务类型
事件持续时间问答，从UDS-T数据重铸而来，用于改进McTACO任务。

---

## 任务类型总结

| 任务类型 | 数据集 |
|----------|--------|
| 时间常识问答 | MCTACO, UDST-DurationQA |
| 生成式时间推理 | situated_gen |
| 对话时间推理 | TimeDial |
| 隐式事件时间推理 | TRACIE |
| 细粒度时间关系提取 | UDS_T_v1.0 |
| 时间推理问答 | TempReason |

## 数据集关系

```
UDS_T_v1.0 (原始时间标注数据)
    ↓ 重铸
UDST-DurationQA (持续时间QA数据)
    ↓ 用于训练
MCTACO (时间常识理解) - 主要基准任务

TRACIE - 隐式事件时间推理
TimeDial - 对话中的时间推理
situated_gen - 生成式时间/地理常识推理
TempReason - 通用时间推理问答
QASPer - 科研论文问答（时间相关问题）
```

---

## 8. QASPer

**来源**: ACL 2021 "A Dataset of Information-Seeking Questions and Answers Anchored in Research Papers"

### 数据格式
JSON格式，字典结构，key为论文ID：

```json
{
  "paper_id": {
    "id": "paper_id",
    "title": "论文标题",
    "abstract": "摘要",
    "full_text": {
      "section_name": "...",
      "paragraphs": ["段落1", "段落2", ...]
    },
    "qas": [
      {
        "question": "问题",
        "question_id": "ID",
        "nlp_background": "...",
        "topic_background": "...",
        "answers": [
          {
            "answer": {
              "unanswerable": false,
              "extractive_spans": ["..."],
              "yes_no": null,
              "free_form_answer": "自由形式答案",
              "evidence": ["..."]
            }
          }
        ]
      }
    ]
  }
}
```

### 数据规模
| Split | 论文数 | 问答对数 |
|-------|--------|---------|
| train | 888 | 2,593 |
| dev | 281 | 1,005 |
| test | 416 | 1,451 |
| **Total** | **1,585** | **5,049** |

### 示例
```
论文: "Minimally Supervised Learning of Affective Events Using Discourse Relations"
问题: "What is the seed lexicon?"
答案: "a vocabulary of positive and negative predicates that helps determine the polarity score of an event"
```

### 时间相关特点
QASPer中的问题涉及：
- 论文中的时间线和事件顺序
- 方法/实验的时间跨度
- 时间表达式理解（"before", "after", "during", "until"等）

---

## 9. Winogrande

**来源**: ACL 2020 "WinoGrande: An Adversarial Winograd Schema Challenge at Scale"

### 数据格式
Parquet格式，每行包含：
- `sentence`: 句子（带有 `_` 占位符）
- `option1`: 选项1
- `option2`: 选项2
- `answer`: 答案 (1 或 2)

### 数据规模
| 子数据集 | Train | Test | Validation | Total |
|----------|-------|------|------------|-------|
| winogrande_xs | 160 | 1,767 | 1,267 | 3,194 |
| winogrande_s | 640 | 1,767 | 1,267 | 3,674 |
| winogrande_m | 2,558 | 1,767 | 1,267 | 5,592 |
| winogrande_l | 10,234 | 1,767 | 1,267 | 13,268 |
| winogrande_xl | 40,398 | 1,767 | 1,267 | 43,432 |
| winogrande_debiased | 9,248 | 1,767 | 1,267 | 12,282 |
| **Total** | **63,238** | **10,602** | **7,602** | **81,442** |

### 示例
```
sentence: "Ian volunteered to eat Dennis's menudo after already having a bowl because _ despised eating intestines."
option1: "Ian"
option2: "Dennis"
answer: "2"  (正确答案是Dennis)
```

### 特点
- WinoGrad Schema Challenge的规模化版本
- 涉及代词消解和常识推理
- 包含多个难度级别（xs, s, m, l, xl）
- debiased版本经过去偏处理

---

## 10. DROP

**来源**: ACL 2019 "DROP: A Reasoning Benchmark for Discrete Reasoning Over Paragraphs"

### 数据格式
Parquet格式，包含段落、问题和答案跨度。

```python
{
    "section_id": "nfl_2201",
    "passage": "To start the season, the Lions traveled south...",
    "question": "How many points did the buccaneers need to tie in the first?",
    "answers_spans": {"spans": ["3"], "types": ["number"]}
}
```

### 数据规模
- train: 77,400 行
- validation: 9,536 行

### 映射任务
→ T1 (时间计算/数字推理)

---

## 11. TimeQA

**来源**: EMNLP 2023 "TimeQA: A Large Scale Dataset for Temporal Question Answering"

### 数据格式
JSON格式，包含时间相关的问答。

```python
{
    "index": "/wiki/Knox_Cunningham#P39",
    "type": "P39",
    "questions": [[["May 1955", "Apr 1956"], [...]]],
    "paras": [...]
}
```

### 映射任务
→ T1 (时间推理问答)

---

## 12. bAbI

**来源**: Facebook AI Research "Towards AI Complete Question Answering"

### 数据格式
文本格式，包含故事和问答对。

```
John went to the kitchen.
What is John location?	kitchen
```

### 映射任务
→ T2 (状态追踪)

---

## 13. ProPara

**来源**: EMNLP 2018 "ProPara: A Large Dataset for Paragraph-level State Tracking"

### 数据格式
TSV格式，追踪实体状态变化。

```
4   1   blood    send    blood    liver
4   2   blood    use     liver   liver
```

### 映射任务
→ T2 (状态追踪/过程追踪)

---

## 14. SocialIQA

**来源**: ICLR 2020 "Social Interaction: Towards Text-based and Knowledge-based AI"

### 数据格式
JSONL格式，社会常识问答。

```json
{
    "context": "Tracy didn't go home that evening and resisted Riley's attacks.",
    "question": "What does Tracy need to do before this?",
    "answerA": "make a new plan",
    "answerB": "Go home and see Riley",
    "answerC": "Find somewhere to go"
}
```

### 数据规模
- train: ~33,000
- dev: ~1,954
- test: ~3,000

### 映射任务
→ T3 (并发冲突/社会推理)

---

## 15. CosmosQA

**来源**: EMNLP 2019 "Cosmos QA: Machine Reading Comprehension for Unstructured Text"

### 数据格式
JSONL格式，常识阅读理解。

```json
{
    "context": "HGH and steroid use is rampant in track...",
    "question": "...",
    "answer0": "...",
    "answer1": "...",
    "answer2": "...",
    "answer3": "..."
}
```

### 映射任务
→ T3 (常识推理)

---

## 16. PIQA

**来源**: NeurIPS 2019 "PIQA: Reasoning about Physical Commonsense in Targeted Domains"

### 数据格式
JSONL格式，物理常识问答。

```json
{
    "goal": "how do you puncture a vein?",
    "sol1": "hit it at the wrong angle and make it bleed.",
    "sol2": "pop it."
}
```

### 数据规模
- test: 3,084
- train/dev: ~16,000

### 映射任务
→ T5 (反事实/虚构规则)

---

## 17. LongBench

**来源**: NeurIPS 2023 "LongBench: A Multi-task Benchmark for Long Context Understanding"

### 数据格式
需要通过 `datasets` 库加载。

### 特点
- 多任务长文本理解基准
- 包含 6 个子任务
- 最长 32,000 tokens

### 映射任务
→ T4 (长期记忆)

---

## 统一架构适配

所有数据集已通过 `arch/` 中的适配器转换为统一格式。

### 适配器列表

| 文件 | 数据集 | 映射任务 |
|------|--------|---------|
| `dataset_adapter.py` | MCTACO, UDST-DurationQA, TimeDial, TRACIE, situated_gen, UDS_T | T1/T2 |
| `qasper_adapter.py` | QASPer | T4 |
| `winogrande_adapter.py` | Winogrande | T5 |
| `new_adapters.py` | DROP, TimeQA, bAbI, ProPara, SocialIQA, CosmosQA, PIQA, LongBench | T1-T5 |

### 转换统计

| 数据集 | 转换后样本数 | 映射任务类型 |
|--------|-------------|-------------|
| MCTACO | ~3,200 | T1 (时间计算) / T2 (状态更新) |
| UDST-DurationQA | ~16,000 | T1 (时间计算) |
| TimeDial | ~1,400 | T1 (时间计算) |
| TRACIE | ~1,200 | T2 (状态更新) |
| situated_gen | ~5,600 | T2 (状态更新) |
| UDS_T | ~59,000 | 知识库 |
| QASPer | ~4,300 | T4 (长期记忆) |
| Winogrande | ~81,000 | T5 (反事实) |
| DROP | ~77,000 | T1 (数字推理) |
| TimeQA | ~3,500 | T1 (时间推理) |
| SocialIQA | ~33,000 | T3 (社会推理) |
| PIQA | ~30,000 | T5 (物理推理) |

### 使用方法

```python
# 导入适配器
from arch import (
    DROPAdapter, TimeQAAdapter, SocialIQAAdapter,
    PIQAAdapter, WinograndeAdapter, QASPerAdapter
)

# 加载数据集
adapter = DROPAdapter('data')
samples = adapter.load('train')

# 或使用便捷函数
from arch.new_adapters import load_drop_data, load_timeqa_data
samples = load_drop_data('data', 'train')
```
