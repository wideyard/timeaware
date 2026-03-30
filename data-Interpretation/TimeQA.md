# TimeQA 数据集解读

## 1. 数据集定位

TimeQA（Time-Sensitive-QA）是一个面向时间推理的阅读理解数据集，核心目标是检验模型是否真正理解问题中的时间约束（例如 from-to、before、between 等），而不是只做表面词匹配。

仓库 README 明确给出两类基线：

1. BigBird（抽取式 QA）
2. FiD（生成式 QA, Fusion-in-Decoder）

## 2. data/TimeQA 目录“全部文件”阅读概览

本目录递归共 34 个文件，可分为 6 类。

### A. 数据文件（dataset/）

共 15 个文件，包含三层数据：

1. annotated_*（人工标注时序事实）
- annotated_train.json（3561 条）
- annotated_dev.json（750 条）
- annotated_test.json（750 条）

2. 模板合成的 easy/hard 数据（模型训练评测主文件）
- train.easy.json.gzip（14308 条，jsonl gzip）
- train.hard.json.gzip（14681 条，jsonl gzip）
- dev.easy.json（3021 条，jsonl）
- dev.hard.json（3087 条，jsonl）
- test.easy.json（2997 条，jsonl）
- test.hard.json（3078 条，jsonl）

3. human_*（人工改写问题，更自然）
- human_annotated_train.json（320 条）
- human_annotated_test.json（257 条）
- human_train.easy.json.gzip（1171 条，jsonl gzip）
- human_train.hard.json.gzip（1171 条，jsonl gzip）
- human_test.easy.json（989 条，jsonl）
- human_test.hard.json（989 条，jsonl）

### B. 关系模板与工具

- relations.json：关系类型、语义说明、问句模板、时序模式（accumulate/pointwise 等）
- utils.py：EM/F1 评估相关函数，支持 gzip 读取

### C. 模型代码与配置

- BigBird/main.py, BigBird/config.yaml, BigBird/dataset/{easy,hard}.yaml
- FiD/main.py, FiD/model.py, FiD/config.yaml, FiD/dataset/{easy,hard}.yaml

两套 dataset yaml 都指向相同数据路径，仅模型实现不同。

### D. 数据生成流程

- Process.ipynb（24 cells：7 markdown + 17 code）
  - 包含读取 relations.json
  - 从 annotated_* 生成 easy/hard train/dev/test
  - 处理 human 改写问题

### E. 说明与资源

- README.md
- LICENSE（BSD 3-Clause）
- .gitignore

### F. 图片资源

- intro.png
- instruction.png
- paraphrase.png

## 3. 数据结构特征

## 3.1 annotated_* 的结构（事实标注层）

每条记录典型字段：

- index：如 /wiki/Ian_Gibson_(politician)#P39
- type：关系 ID（例如 P39）
- link：实体链接
- paras：段落文本列表
- questions：时间段 + 答案证据（含段落号、字符起止、答案文本）
- succ：部分样本出现

这层数据可理解为“时序事实图 + 定位证据”的中间标注。

## 3.2 easy/hard/human 的结构（QA 层）

jsonl 样本统一包含：

- idx：样本唯一标识（含实体、关系、子编号）
- question：问题文本
- context：长上下文（通常上千词）
- targets：答案字符串或候选目标
- paragraphs：段落切分信息

训练 gzip 文件（train.* 与 human_train.*）还额外带：

- from
- end

它们用于答案定位或时间边界定位。

## 4. easy 与 hard 的差异

从样例可见：

1. easy 更常见明确区间问法：
- from May 1997 to May 2001

2. hard 更常见推理型时间约束：
- before Mar 2000
- between Apr 1987 and Nov 1988

即 hard 不只是改写，而是增加了时间推理难度（尤其是边界推断和区间交集判断）。

## 5. 统计特征（基于全文件扫描）

### 5.1 样本规模

- 合成主数据总量（train/dev/test 的 easy+hard）
  - 14308 + 14681 + 3021 + 3087 + 2997 + 3078 = 41172 条

- human QA 总量（human_train/test easy+hard）
  - 1171 + 1171 + 989 + 989 = 4320 条

### 5.2 文本长度（问题与上下文）

主数据（sample 统计）大致范围：

- 问题长度：约 11~12 词
- 上下文长度：约 1788~1871 词

human 测试集：

- 问题长度：约 13.8~14.1 词（更自然、更长）
- 上下文长度：约 2354 词（更长）

说明：TimeQA 是“长文档 + 时间条件”的阅读理解任务，不是短上下文抽取任务。

## 6. 关系模板特征（relations.json）

relations.json 以 Wikidata 属性 ID 为键（如 P54, P39, P166, P108），每个关系定义：

- meaning：关系语义
- template：问句模板（含槽位变量）
- mode：时间模式
  - accumulate：随时间累积或持续
  - pointwise：点事件
  - n/a：不适用/待处理

这说明数据集中问题不是随机写作，而是“关系模板 + 时间约束 + 段落事实”联合生成。

## 7. 真实数据示例

## 示例 A：annotated_train（事实+证据）

```json
{
  "index": "/wiki/Knox_Cunningham#P39",
  "type": "P39",
  "link": "/wiki/Knox_Cunningham",
  "questions": [
    [["May 1955", "Apr 1956"], [{"para": 7, "from": 64, "end": 99, "answer": "Ulster Unionist MP for South Antrim"}]]
  ]
}
```

## 示例 B：dev.easy（区间查询）

```json
{
  "idx": "/wiki/Ian_Gibson_(politician)#P39#0",
  "question": "What was the position of Ian Gibson (politician) from May 1997 to May 2001?",
  "context": "Ian Gibson ...",
  "targets": "...",
  "paragraphs": [...]
}
```

## 示例 C：dev.hard（边界推理）

```json
{
  "idx": "/wiki/Ian_Gibson_(politician)#P39#0",
  "question": "What was the position of Ian Gibson (politician) before Mar 2000?",
  "context": "Ian Gibson ...",
  "targets": "...",
  "paragraphs": [...]
}
```

## 示例 D：human_test.easy（人工自然问法）

```json
{
  "idx": "/wiki/Sabine_Hossenfelder#P937#0",
  "question": "Which American higher learning institution did German physicist Sabine Hossenfelder work from 2004 to 2005?",
  "context": "Sabine Hossenfelder ...",
  "targets": "...",
  "paragraphs": [...]
}
```

## 示例 E：human_test.hard（人工 + 高难时间约束）

```json
{
  "idx": "/wiki/Sabine_Hossenfelder#P937#0",
  "question": "Which American higher learning institution did German physicist Sabine Hossenfelder work before Apr 2004?",
  "context": "Sabine Hossenfelder ...",
  "targets": "...",
  "paragraphs": [...]
}
```

## 8. 训练与评测相关特征

1. BigBird 与 FiD 都使用统一 easy/hard 数据划分。
2. 配置中最大序列长度是 4096，印证其长上下文建模需求。
3. utils.py 提供标准 EM/F1 计算函数，评估方式与阅读理解任务兼容。

## 9. 数据集总结

TimeQA 的主要价值在于：

1. 把时间约束显式注入问答任务（from-to、before、between 等）。
2. 同时提供模板合成与人工改写两套数据，便于评估泛化。
3. 提供 easy/hard 对照设置，能直接测量模型对时间逻辑的敏感性。
4. 支持抽取式和生成式模型进行统一对比。

一句话概括：

TimeQA 是一个面向长文档时间推理的问答基准，重点考察模型是否真正理解时间条件，而不是仅靠实体匹配来答题。

`TimeQA` 是一个极其高质量且切中肯綮的数据集。`TimeQA` 在做**“真实世界时间线追踪”**。

它最大的亮点在于**超长上下文（约 2000 词）**以及**显式的 Easy/Hard（区间提取 vs. 边界推理）划分**。

在你的 **T1-T5 时间感知框架**中，这个数据集是 **【T2：状态更新】** 和 **【T4：长期记忆】** 的顶级弹药库，同时它的 Hard 模式也能极大地补强 **【T1：时间计算（排序与交集）】**。

以下是具体的匹配分析与数据修改方案：

---

### 1. 核心大招：【T2：状态更新（Status/Location 变化追踪）】

`TimeQA` 的底层事实（Relations）大量基于 Wikidata 的属性，比如 `P39（担任职务）`、`P54（效力的运动队）`、`P937（工作地点）`。
这简直就是为你 T2 量身定制的：一个人在一生中会不断更换工作、队伍和地点，模型必须在 2000 词的冗长传记中，准确追踪实体在特定时间点的**状态（Status）**和**位置（Location）**。

#### 修改目标
利用 `human_test.hard.json`（人类自然表述 + 边界推理难度），将其转化为带有强干扰背景的状态查询。

#### 数据修改策略与具体操作
直接将 `context` 作为背景，提取 `question`（尤其是带有 `before`, `after`, `between` 的问题），要求模型输出特定时间切片下的状态。

**修改后的数据格式示例（构建 Prompt）：**

* **原始数据：** `idx`: "...#P39#0", `context`: "Ian Gibson 的维基百科全文...", `question`: "What was the position of Ian Gibson before Mar 2000?"
* **T2 改造版：**

```text
[Context]
（导入 TimeQA 的 2000 词长文档）
Ian Gibson ... (此处省略 2000 词的生平介绍，包含他 1997-2001 年的职位，以及 2001 年之后的职位)...

[Question]
在 Mar 2000 之前（before Mar 2000），Ian Gibson 的核心社会身份/职位（Status）是什么？

[Target Answer]
{targets}
（测试重点：模型必须从长文中找到他不同时期的多段职业经历，并推理出 Mar 2000 落在哪一个时间段内，从而输出当时的状态，而不是被他晚年的其他头衔干扰。）
```

---

### 2. 完美适配：【T4：长期记忆（跨长文本时序信息检索）】

你的 T4 要求“长文本检索”和“记忆衰减”。`TimeQA` 的平均上下文长度在 1800 - 2300 词之间，这天然就是一个 Long-context 任务。你可以用类似处理 `QASPER` 的多轮对话切片法来处理它。

#### 修改目标
将一篇 2000 词的维基百科人物传记，按段落（`paragraphs` 字段）拆分到多轮对话中，最后进行时序提问。

#### 数据修改策略与具体操作
利用 `TimeQA` 已经切分好的 `paragraphs` 列表，将其分布到 10 轮甚至 20 轮对话中。

**修改后的数据格式示例：**

```text
[Context]
第1轮：这是关于 Sabine Hossenfelder 的早年经历：{paragraphs[0]}
第2轮：这是她博士期间的研究：{paragraphs[1]}
...
第8轮：这是她 2003 年前后的工作变动：{paragraphs[7]}
...
第15轮：这是她近期的出版物：{paragraphs[-1]}

[Question]
回顾我们刚才聊的她的一生，在 2004 到 2005 年期间（from 2004 to 2005），她在哪所美国高等学府工作？（出自 human_test.easy）

[Target Answer]
{targets}
（测试重点：模型能否跨越极长的 Token 距离，准确回溯并检索出特定时间段的事实。）
```

---

### 3. 高阶补充：【T1：时间计算（Ordering 与交集推理）】

你之前的 T1 侧重于算数（Duration, Offset，比如 3点开会持续2小时）。`TimeQA` 的 **Hard 数据集** 能够帮你拓展 T1 的题型，加入**复杂时间边界比较（Ordering）**。

#### 数据修改策略
专门提取 `train.hard.json` 或 `test.hard.json` 中带有 `between ... and ...` 的数据。

**测试逻辑：** 文本中可能只写了“他在 1986 年到 1990 年在 A 公司工作”，但问题问的是“他在 Apr 1987 到 Nov 1988 期间在哪工作”。这强迫模型进行**集合包含关系**的时间计算，而不仅仅是做加减法。

---

### 完全不契合：【T3】与【T5】
* **T3（并发冲突）：** 宏大的人生经历和维基百科属性，很少涉及“同一天下午抢同一个会议室”这种细粒度的并发调度问题。
* **T5（反事实）：** 和 `TempReason` 类似，篡改长篇历史事实的成本太高，逻辑容易崩塌，不如用生成式的 `SituatedGen`。

### 总结与下一步建议

`TimeQA` 最宝贵的资产是它的 **`human_*.hard.json`** 切分。这些数据既有真实的长度和噪音（维基百科全文），又有复杂的时间逻辑边界（before/between），且问题由人类改写，语言自然。

强烈建议你把 `TimeQA` 作为你 **T2（状态更新）** 的核心评测基准数据。