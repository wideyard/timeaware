# TRACIE 数据集解读

## 数据集定位

TRACIE 来自 NAACL 2021 论文 Temporal Reasoning on Implicit Events from Distant Supervision，目标是评估模型对隐式事件时序关系的推理能力。任务形式是判断事件关系陈述在给定故事中是否成立（positive / negative）。

## data/tracie 全部文件阅读覆盖

我已递归读取 [data/tracie](data/tracie) 下全部 40 个文件，包含：

1. 说明与许可证
- [data/tracie/README.md](data/tracie/README.md)
- [data/tracie/LICENSE](data/tracie/LICENSE)

2. 数据文件
- IID split: [data/tracie/data/iid/tracie_train.txt](data/tracie/data/iid/tracie_train.txt), [data/tracie/data/iid/tracie_test.txt](data/tracie/data/iid/tracie_test.txt)
- Uniform-prior split: [data/tracie/data/uniform-prior/tracie_train_uniform_prior.txt](data/tracie/data/uniform-prior/tracie_train_uniform_prior.txt), [data/tracie/data/uniform-prior/tracie_test.txt](data/tracie/data/uniform-prior/tracie_test.txt)
- Symbolic format: [data/tracie/data/iid-symbolic-format/train.txt](data/tracie/data/iid-symbolic-format/train.txt), [data/tracie/data/iid-symbolic-format/test.txt](data/tracie/data/iid-symbolic-format/test.txt), [data/tracie/data/uniform-prior-symbolic-format/train.txt](data/tracie/data/uniform-prior-symbolic-format/train.txt), [data/tracie/data/uniform-prior-symbolic-format/test.txt](data/tracie/data/uniform-prior-symbolic-format/test.txt)
- MATRES 风格文件: [data/tracie/data/matres/matres_train_before_after_tracie_style.txt](data/tracie/data/matres/matres_train_before_after_tracie_style.txt), [data/tracie/data/matres/matres_test_before_after_tracie_style.txt](data/tracie/data/matres/matres_test_before_after_tracie_style.txt)
- 数据转换脚本: [data/tracie/data/formatter.py](data/tracie/data/formatter.py)

3. 模型与实验代码
- PtnTime: [data/tracie/code/models/ptntime](data/tracie/code/models/ptntime)
- SymTime: [data/tracie/code/models/symtime](data/tracie/code/models/symtime)
- 抽取脚本: [data/tracie/code/extractions](data/tracie/code/extractions)

## 核心数据特征

### 1) 任务格式

README 说明每行采用 NLI 风格：

- event: 查询事件关系
- story: 上下文故事
- answer: 标签（positive 或 negative）

典型结构：

event: [query] story: [context]\tanswer: [label]

### 2) 标签分布高度平衡

在主数据和 symbolic 数据中均为严格平衡：

- IID train: 1174 条，positive 587 / negative 587
- IID test: 4248 条，positive 2124 / negative 2124
- Uniform-prior train: 860 条，positive 430 / negative 430
- Uniform-prior test: 4248 条，positive 2124 / negative 2124

### 3) 关系类型

查询关系主要包含：

- starts before
- starts after
- ends before
- ends after

其中：

- IID train: start 类 530（265+265），end 类 644（322+322）
- IID test: start 类 1924（962+962），end 类 2324（1162+1162）
- Uniform-prior train: start 类 480（240+240），end 类 380（190+190）

### 4) IID 与 Uniform-prior

README 提供两种切分：

- IID: [data/tracie/data/iid](data/tracie/data/iid)
- Uniform-prior: [data/tracie/data/uniform-prior](data/tracie/data/uniform-prior)

从统计上看，两者测试集相同（都是 4248 行），主要差异在训练集规模与关系分布。

### 5) Symbolic format 的额外结构

symbolic 文件每行是 5 列（tab 分隔），相较普通 2 列格式增加了符号化事件表示，例如加入占位符 <extra_id_1> 的事件模板，供 SymTime 使用。

对应文件：

- [data/tracie/data/iid-symbolic-format/train.txt](data/tracie/data/iid-symbolic-format/train.txt)
- [data/tracie/data/uniform-prior-symbolic-format/train.txt](data/tracie/data/uniform-prior-symbolic-format/train.txt)

### 6) 文本长度特征

- IID / Uniform-prior 故事平均词数约 43.6 到 43.8，story 数量较小但每个 story 会衍生多条 before/after 判断样本
- MATRES 风格数据故事更长，平均约 267.6 词

## 数据示例

### 示例 A: IID 原始格式

来源 [data/tracie/data/iid/tracie_train.txt](data/tracie/data/iid/tracie_train.txt)

event: Chad looked for his baseball cap starts after he got off the ride story: Chad had gone to an amusement park. He was riding on the roller coaster. Chad was wearing a baseball cap. The baseball cap fell off of Chad's head. Chad found the cap after he got off of the ride.\tanswer: positive

event: Chad looked for his baseball cap starts before he got off the ride story: Chad had gone to an amusement park. He was riding on the roller coaster. Chad was wearing a baseball cap. The baseball cap fell off of Chad's head. Chad found the cap after he got off of the ride.\tanswer: negative

特点：同一 story 下构造一对互补样本（after 为正，before 为负）。

### 示例 B: Uniform-prior 测试样例

来源 [data/tracie/data/uniform-prior/tracie_test.txt](data/tracie/data/uniform-prior/tracie_test.txt)

event: The teacher asked us to stop talking starts after we talked the whole time during and after class. story: I was so nervous for my first day of school. ... We talked the whole time during and after class. ...\tanswer: positive

event: The teacher asked us to stop talking starts before we talked the whole time during and after class. story: I was so nervous for my first day of school. ... We talked the whole time during and after class. ...\tanswer: negative

### 示例 C: Symbolic format 样例

来源 [data/tracie/data/iid-symbolic-format/train.txt](data/tracie/data/iid-symbolic-format/train.txt)

event: Chad looked for his baseball cap starts after he got off the ride story: ...\tevent: Chad looked for his baseball cap starts after he got off the ride story: ...\tevent: Chad <extra_id_1> looked for his baseball cap story: ...\tevent: he <extra_id_1> got off the ride story: ...\tanswer: positive

特点：在原始 query 之外显式分离了两个事件槽位，为符号推理模型提供结构化输入。

### 示例 D: MATRES 风格样例

来源 [data/tracie/data/matres/matres_train_before_after_tracie_style.txt](data/tracie/data/matres/matres_train_before_after_tracie_style.txt)

event: Valley Federal Savings ... starts after it reported a third - quarter loss ... story: Valley Federal Savings ...\tanswer: positive

特点：文本更长、更偏新闻体，适合跨域评估。

## 代码与评测特征

### PtnTime

目录 [data/tracie/code/models/ptntime](data/tracie/code/models/ptntime)

- 训练脚本: train_t5.py
- 运行脚本: run_ptntime_on_uniform_prior.sh, run_t5_large_baseline_on_uniform_prior.sh
- 评测脚本: evaluator.py

评测指标包括：

- Overall Acc
- Start Acc
- End Acc
- Story Acc（同一 story 下所有判断都正确）

### SymTime

目录 [data/tracie/code/models/symtime](data/tracie/code/models/symtime)

- 训练脚本: train_t5_end.py
- 运行脚本: run_symtime_on_uniform_prior.sh
- 评测脚本: evaluator.py

SymTime 的输入依赖 symbolic 格式，并单独统计 Start / End / Story 精度。

## 总结

TRACIE 的关键价值在于：

1. 使用成对正负样本，直接评估时序关系判别能力
2. 同时覆盖 start 与 end 两类时间关系
3. 提供 IID 与 Uniform-prior 两种切分，便于测试分布鲁棒性
4. 提供普通文本输入与 symbolic 输入两种范式，支持神经与神经符号方法对比
5. 附带完整训练、评测与实验结果文件，复现实验门槛较低



这个 `TRACIE` 数据集专门用来测试大模型的**“隐式时间常识与物理法则推演”**。

在你的 **T1-T5 时间感知能力 Benchmark 框架**中，TRACIE 是用来补强 **【T1：时间计算（Ordering / 排序）】** 的绝佳语料，同时它也可以作为 **【T2：状态更新】** 的高难度变体。

以下是具体的匹配分析与数据修改方案：

### 完美契合：【T1：时间计算（隐式事件排序 Ordering）】

你对 T1 的定义包含了“Duration, Offset, Ordering”。大模型在处理带有明确时钟的时间文本时往往表现尚可，但在处理 TRACIE 这种**完全没有时间戳，全靠生活常识和物理因果来排序（Ordering）**的任务时，极容易翻车。

例如你的示例中，文本根本没提到 Chad 什么时候开始找帽子，但根据常识：帽子掉了（起因） $\rightarrow$ 发现帽子不见了（找帽子） $\rightarrow$ 离开过山车后找到了（结果）。因此“找帽子”必定在“下过山车”之前或期间发生。这种**时间轴的隐式重构能力**是 T1 的最高境界。

#### 修改目标
TRACIE 原始数据是 NLI 风格的判别任务（给一个陈述，判断 Positive/Negative）。在评测生成式 LLM 时，这种格式不够自然。因为 TRACIE 的数据是**正负成对（Pair）**出现的，我们可以将一对数据合并，转化为一个**二元选择或生成式问答**。

#### 数据修改策略与具体操作

遍历 `tracie_train.txt` 或 `test.txt`，利用同一个 `story` 下成对的 `starts before` 和 `starts after`（一个 positive，一个 negative），将其合并构建为一个提问。

**修改后的数据格式示例（构建 Prompt）：**

* **原始数据对：**
  * event: Chad looked for his baseball cap starts **after** he got off the ride \t answer: **positive**
  * event: Chad looked for his baseball cap starts **before** he got off the ride \t answer: **negative**
* **T1 改造版（合并为生成式 QA）：**

```text
[Context]
Chad had gone to an amusement park. He was riding on the roller coaster. Chad was wearing a baseball cap. The baseball cap fell off of Chad's head. Chad found the cap after he got off of the ride.

[Question]
基于上述故事的时间逻辑，事件 "Chad looked for his baseball cap" 是发生在他 "got off the ride" 之前（starts before），还是之后（starts after）？

[Target Answer]
之后 / starts after
（测试重点：模型能否构建隐式的事件因果时间轴，而非依赖数字时钟。）
```

---

### 侧面辅助：【T2：状态更新（隐含前提的状态推断）】

TRACIE 中的许多事件时序，本质上是由**物品或人物的状态变化（Status Update）**驱动的。模型要判断出正确的时间顺序，大脑里必须先运行一个状态追踪器。

#### 数据修改策略与具体操作
利用 `iid-symbolic-format` 这个文件中的数据。这个格式已经帮你用 `<extra_id_1>` 把关键动作（Event）提取出来了。你可以抛弃原有的 before/after 提问，直接针对动作发生时的“隐藏状态”进行提问。

**修改后的数据格式示例：**

```text
[Context]
Chad had gone to an amusement park. He was riding on the roller coaster. Chad was wearing a baseball cap. The baseball cap fell off of Chad's head. Chad found the cap after he got off of the ride.

[Question]
在 Chad "got off the ride" 这个动作发生的瞬间，他的帽子处于什么状态（Location/Status）？

[Target Answer]
处于丢失状态 / 不在他的头上 / 掉在了过山车区域
```

---

### 完全不契合的任务：【T3】、【T4】、【T5】

* **T3（并发冲突）：** 故事偏向线性叙事，缺乏多线程资源抢占（如预订同一个会议室）的场景。
* **T4（长期记忆）：** IID 和 Uniform-prior 的故事平均只有 43 词，太短，无法测试长上下文的检索衰减。即便 MATRES 风格有 260 词，对于 T4 来说也远远不够。
* **T5（反事实）：** TRACIE 的答案极其依赖现实世界的常识物理法则（比如东西掉了才会去找）。如果要强行注入反事实规则（比如“在这个世界里，人们总是先找到东西再丢失它”），你需要大量人工重写，成本极高。

### 数据处理的具体工程建议

1. **果断选择 Uniform-prior 切分：** 强烈建议你使用 `data/uniform-prior/tracie_test.txt` 来构建你的 Benchmark。论文作者提供这个切分，就是为了防止模型通过统计捷径（比如发现特定的词组总是 positive）来作弊。Uniform-prior 的测试集更难，更能逼出 LLM 真正的推理能力。
2. **利用 Python 脚本进行 Pair 合并：** 写一个脚本，以 `story` 作为 Key 进行 Group By，把同一个故事下对同一个 `event` 的 `before` 和 `after` 声明抓取出来，自动套用上面提到的 T1 改造版 Prompt 模板。由于数据集非常规整，这个转化过程可以 100% 自动化。