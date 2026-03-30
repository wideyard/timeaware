# QASPER 数据集解读

## 1. 目录文件全览（data/qasper）

本目录下共有 8 个文件：

- qasper-train-v0.3.json
- qasper-dev-v0.3.json
- qasper-test-v0.3.json
- qasper-train-dev-v0.3.tgz
- qasper-test-and-evaluator-v0.3.tgz
- qasper_evaluator.py
- README.md
- README-test.md

其中：

- 3 个 .json 是可直接使用的数据主文件。
- 2 个 .tgz 是打包分发文件。
- qasper_evaluator.py 是官方评测脚本。
- 两个 README 说明了字段定义、版本差异和评测方式。

## 2. 数据集任务与定位

QASPER（v0.3）是“面向科研论文的信息寻求式问答”数据集：

- 样本以论文为单位组织（key 为 arXiv id）。
- 每篇论文包含标题、摘要、全文结构、图表信息与 QA 标注。
- 问答不局限于抽取式，包含抽取式、自由生成、是非判断和不可回答。
- 答案配有证据段落/图表（evidence），适合联合评估“答案正确性 + 证据定位”。

## 3. 主文件规模统计

基于三个 JSON 全量统计：

- train: 888 篇论文，2593 个问题，2675 条答案标注
- dev: 281 篇论文，1005 个问题，1764 条答案标注
- test: 416 篇论文，1451 个问题，3554 条答案标注

按论文平均结构（约）：

- 每篇 section 数：13.5 ~ 14.0
- 每篇段落数：48 ~ 54
- 每篇图表（caption 条目）数：约 6.9 ~ 7.4

说明：这是一个“长文档 + 多证据”问答场景，不是短上下文 QA。

## 4. 字段结构特征

每篇论文对象（按 README 与样本）核心字段包括：

- title
- abstract
- full_text（章节与段落）
- figures_and_tables（图表文件名与caption）
- qas

每个问题（qas 内）常见字段：

- question_id
- question
- nlp_background（提问者 NLP 背景）
- topic_background（提问者对主题熟悉度）
- paper_read（是否阅读过论文）
- search_query（可为空）
- answers（多标注者答案）

每条答案（answers[*].answer）包含：

- unanswerable
- extractive_spans
- free_form_answer
- yes_no
- evidence
- highlighted_evidence

设计约束：可回答答案中，extractive_spans / free_form_answer / yes_no 三者应是单一类型。

## 5. 答案类型分布（按标注条数）

train：

- extractive: 1363
- abstractive: 622
- boolean: 409
- unanswerable: 281

dev：

- extractive: 962
- abstractive: 431
- boolean: 208
- unanswerable: 163

test：

- extractive: 1817
- abstractive: 878
- boolean: 493
- unanswerable: 366

结论：抽取式最多，但生成式、是非与不可答占比也不低，属于“混合答案类型”评测。

## 6. 证据标注特征

README 明确区分两类证据：

- evidence：段落级证据（以及图表证据）
- highlighted_evidence：更细粒度句子证据

当证据来自图或表时，evidence 文本会以 `FLOAT SELECTED` 开头并附带对应 caption。

这对“文本证据-only”与“文本+图表证据”的实验设置很关键。

## 7. 官方评测脚本特征（qasper_evaluator.py）

脚本输出两大主指标：

- Answer F1（含按类型分组）
- Evidence F1

关键评测逻辑：

- 对每个问题，预测与该问题所有参考答案逐一比对，取最大匹配分数。
- 答案分数基于 token-level F1（SQuAD 风格归一化）。
- 证据分数基于预测证据集合与金标集合的集合 F1。
- 支持 `--text_evidence_only`，忽略 `FLOAT SELECTED` 的图表证据。

## 8. 数据示例（真实样本）

## 示例 A：论文级结构

```json
{
  "paper_id": "1909.00694",
  "title": "Minimally Supervised Learning of Affective Events Using Discourse Relations",
  "abstract": "Recognizing affective events that trigger positive or negative sentiment ...",
  "full_text[0].section_name": "Introduction",
  "full_text[0].paragraphs[0]": "Affective events ...",
  "figures_and_tables[0]": {
    "file": "2-Figure1-1.png",
    "caption": "Figure 1: An overview of our method ..."
  }
}
```

## 示例 B：抽取式答案（extractive）

```json
{
  "question_id": "753990d0b621d390ed58f20c4d9e4f065f0dc672",
  "question": "What is the seed lexicon?",
  "answer": {
    "unanswerable": false,
    "extractive_spans": ["seed lexicon consists of positive and negative predicates"],
    "free_form_answer": "",
    "yes_no": null,
    "evidence": ["The seed lexicon consists of positive and negative predicates ..."]
  }
}
```

## 示例 C：生成式答案（abstractive）

```json
{
  "question": "What is the seed lexicon?",
  "answer": {
    "unanswerable": false,
    "extractive_spans": [],
    "free_form_answer": "a vocabulary of positive and negative predicates that helps determine the polarity score of an event",
    "yes_no": null,
    "evidence": ["The seed lexicon consists of positive and negative predicates ..."]
  }
}
```

## 示例 D：是非答案（boolean）+ 图表证据

```json
{
  "question": "Does the paper report macro F1?",
  "answer": {
    "unanswerable": false,
    "yes_no": true,
    "extractive_spans": [],
    "free_form_answer": "",
    "evidence": ["FLOAT SELECTED: Table 7: Recall and precision scores ..."]
  }
}
```

## 示例 E：不可回答（unanswerable）

```json
{
  "question": "Do they report results only on English data?",
  "answer": {
    "unanswerable": true,
    "extractive_spans": [],
    "free_form_answer": "",
    "yes_no": null,
    "evidence": []
  }
}
```

## 9. 文件完整性与可用性说明

- qasper-test-and-evaluator-v0.3.tgz：可正常读取，包含
  - qasper-test-v0.3.json
  - qasper_evaluator.py
  - README-test.md
- qasper-train-dev-v0.3.tgz：当前本地文件读取时报 EOFError（压缩流提前结束），看起来是损坏或下载不完整。

但由于 train/dev 的 JSON 主文件已在目录中可直接读取，因此不影响常规训练与分析。

## 10. 总结

QASPER 是一个面向科研论文长文档理解的多类型问答数据集，核心特点是：

1. 论文级长上下文（多章节、多段落、多图表）。
2. 问答类型混合（抽取/生成/是非/不可答）。
3. 强证据监督（文本段落与图表证据并存）。
4. 官方评测同时考察答案正确性与证据定位质量。

对于建模而言，它更接近“真实学术阅读问答”而非短上下文抽取任务。


基于 QASPER 数据集的特性（长文档、学术论文、事实性信息），**它原生只高度契合你的【T4：长期记忆】任务**。对于 T1、T2、T3 和 T5，QASPER 原生的问答对并不适用，但它的超长文本可以作为**高质量的上下文干扰项（Noise Context）**。

以下是具体的适配分析和数据修改方案：

---

### 最完美契合：【T4：长期记忆（跨长文本信息检索）】

QASPER 是一篇平均 50 段的长文本，这天然就是 T4 测试“long-context retrieval”和“memory decay”的绝佳语料。我们可以把“阅读长论文”伪装成一段漫长的多轮对话。

#### 修改目标
将 QASPER 的单篇结构化论文，改造成**“首轮输入核心信息 + 中间多轮注水/闲聊 + 尾轮提问”**的对话格式。

#### 数据修改策略与具体操作
你需要提取 `full_text` 中的不同 section，将其分散到不同的对话轮次中，最后抽取 `qas` 中的问题进行提问。

**修改后的数据格式示例（构建 Prompt）：**

```text
[Context]
第1轮：我最近在读一篇论文，标题是《{title}》，它的摘要是：{abstract}
第2轮：（User分享论文第一部分）这是它的Introduction：{full_text[0].paragraphs[...]}
第3轮：（User分享论文第二部分）这是它的Method：{full_text[1].paragraphs[...]}
...
第8轮：（插入与论文无关的闲聊，测试 Memory Decay）对了，我今天下午要去喝咖啡。
第9轮：（User分享论文最后一部分）这是结论：{full_text[-1].paragraphs[...]}
第10轮：（插入闲聊）今天的咖啡真不错，我们刚刚说到哪了？

[Question]
关于我刚才分享的论文，{qas[0].question}？

[Target Answer]
{qas[0].answers[0].answer.extractive_spans / free_form_answer}
```

**代码处理逻辑（Python 伪代码思路）：**
1. 过滤掉 `qas` 中 `unanswerable: true` 的问题，只保留有明确答案（extractive 或 free_form）的样本，保证测试结果的确定性。
2. 遍历 `full_text`，按 `section_name` 将论文切分成 5-8 个 chunk。
3. 按照对话格式拼接，中间随机插入 2-3 轮预设的“日常闲聊文本”。
4. 将 `question` 作为最后的 Query，将 `evidence` 所属的原始段落位置作为“检索正确性”的辅助评测指标。

---

### 作为干扰项的间接契合：【T1, T2, T3, T5】

这四个任务考察的是时间计算、状态更新、逻辑冲突和反事实，这都是高度动态和日常化（episodic）的场景，而学术论文是静态事实。

因此，**不要用 QASPER 来生成这四个任务的 Question 和 Answer，而是用它来做 Context 的“压力测试背景板”（大海捞针）。**

#### 修改目标
将你的 T1/T2/T3/T5 的核心线索，**悄悄埋入** QASPER 枯燥冗长的学术论文文本中。以此测试 LLM 在面对海量、晦涩且无关的学术专业信息干扰时，能否依然准确捕捉时间、状态、冲突和规则。

#### 数据修改策略与具体操作（以 T2：状态更新 为例）

**修改后的数据格式示例（构建 Prompt）：**

```text
[Context]
第1轮：我3点开始开会。（植入状态A）
第2轮：你可以帮我看看这篇论文吗？{QASPER 论文 Section 1}
第3轮：论文写得挺复杂的。{QASPER 论文 Section 2}
第4轮：现在是4点了，我的会开完了，我正在看这篇论文的图表。（更新状态B：Location和Status发生变化）
第5轮：图表说明是：{QASPER 论文 figures_and_tables 文本}
第6轮：论文的结论是：{QASPER 论文 Section N}

[Question]
我现在在做什么？

[Target Answer]
看论文 / 看论文的图表（而不是回答“在开会”）
```

**同样的方法适用于 T1/T3/T5：**
* **T1（时间计算 + 静态干扰）：** 把日程安排插在两段论文摘要之间。看看复杂的学术名词会不会干扰模型对“下午3点持续2小时”的数学提取。
* **T3（并发冲突）：** 把“我3点到4点开会”写在 Prompt 开头，把 QASPER 一整篇近万字的全文塞进去，在最后加上一句“对了，我3点要去看电影，这个安排合理吗？”
* **T5（反事实）：** 在 QASPER 全文前加上“在这个世界中，水在50度沸腾”。用整篇深度学习论文“洗脑”模型后，再问水温60度会发生什么。

### 总结建议

如果你准备直接处理这份 JSON 文件写处理脚本：
1.  **对于你的 T4 任务**，QASPER 是现成的**主料**，你需要写脚本将 `full_text` 拆解并转化为多轮对话格式，提取 `extractive/abstractive` 答案作为金标准。