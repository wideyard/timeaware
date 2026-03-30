# WinoGrande 数据集解读

## 1. 数据集简介

WinoGrande 是一个大规模常识指代消解/填空推理数据集，任务形式是：

- 给定一个包含占位符 `_` 的句子（`sentence`）
- 给定两个候选项（`option1`, `option2`）
- 选择正确选项（训练/验证中的 `answer` 为 `1` 或 `2`）

目录中的 README 指向论文：

WinoGrande: An Adversarial Winograd Schema Challenge at Scale (2019)

## 2. 目录文件全覆盖（data/winogrande）

已读取该目录下全部 19 个文件：

1. README
- README.md

2. 六个配置目录（每个都含 train/validation/test 三个 parquet）
- winogrande_xs/
- winogrande_s/
- winogrande_m/
- winogrande_l/
- winogrande_debiased/
- winogrande_xl/

每个配置都包含：
- train-00000-of-00001.parquet
- validation-00000-of-00001.parquet
- test-00000-of-00001.parquet

## 3. 字段结构

所有配置、所有 split 结构一致：

- `sentence`：带一个 `_` 占位符的句子
- `option1`：候选 1
- `option2`：候选 2
- `answer`：标签（训练/验证为 `1` 或 `2`，测试为空字符串）

额外统计特征：

- 训练集 `sentence` 中“恰好 1 个下划线占位符”的比例为 100%
- `option1/option2` 平均词长约 1.0（多数是单词或短名词）
- `sentence` 平均词长约 18.7~19.3

## 4. 各配置规模

### 4.1 训练集规模（主要差异）

- winogrande_xs: 160
- winogrande_s: 640
- winogrande_m: 2558
- winogrande_l: 10234
- winogrande_debiased: 9248
- winogrande_xl: 40398

### 4.2 验证/测试规模（一致）

所有配置均相同：

- validation: 1267
- test: 1767

### 4.3 标签分布

训练/验证近似或严格均衡：

- 例如 `winogrande_l` train：`1=5117`, `2=5117`
- 例如 `winogrande_xl` train：`1=20199`, `2=20199`
- `winogrande_debiased` train 略有轻微差：`1=4654`, `2=4594`

测试集 `answer` 均为空（1767 条空字符串），用于提交评测。

## 5. 配置之间关系

通过样本交集验证到：

- `xs ⊂ s ⊂ m ⊂ l ⊂ xl`（逐级子集）
- `debiased` 与 `xl` 有大量重叠（重叠 9154 条训练样本），但不是简单子集关系

这说明：

- xs/s/m/l/xl 更像同一数据池的不同规模切片
- debiased 是额外构造的“去偏”训练版本

## 6. 数据示例

## 示例 A（训练样本，winogrande_debiased）

```json
{
  "sentence": "John moved the couch from the garage to the backyard to create space. The _ is small.",
  "option1": "garage",
  "option2": "backyard",
  "answer": "1"
}
```

含义：需要理解“为了腾空间把沙发从车库搬到后院”，因此更可能“小的是 garage”。

## 示例 B（训练样本，winogrande_l）

```json
{
  "sentence": "Ian volunteered to eat Dennis's menudo after already having a bowl because _ despised eating intestine.",
  "option1": "Ian",
  "option2": "Dennis",
  "answer": "2"
}
```

含义：讨厌吃内脏的人更可能是 Dennis（Ian 已经主动去吃）。

## 示例 C（验证样本）

```json
{
  "sentence": "Sarah was a much better surgeon than Maria so _ always got the easier cases.",
  "option1": "Sarah",
  "option2": "Maria",
  "answer": "2"
}
```

含义：更强的外科医生通常不会拿“更容易”的病例，因此答案指向 Maria。

## 示例 D（测试样本）

```json
{
  "sentence": "Kenneth went cheap on the gemstone present for Michael and _ was understanding about being a cheapskate.",
  "option1": "Kenneth",
  "option2": "Michael",
  "answer": ""
}
```

测试集标签留空，供模型推理后提交。

## 7. 这个数据集的核心特点

1. **任务清晰**：二选一填空，专注常识推理与指代消解。
2. **规模灵活**：从 xs 到 xl 多训练规模，便于比较数据量敏感性。
3. **评测统一**：所有配置共享同一验证/测试集，便于公平对比。
4. **标签平衡**：训练标签接近 1:1，降低类别偏置影响。
5. **debiased 版本**：提供去偏训练集，强调鲁棒性与泛化能力。

## 8. 一句话总结

WinoGrande 是一个大规模、可多规模训练、以常识消歧为核心的二分类填空数据集，适合系统评估模型在“语义常识+指代推理”上的真实能力。


这个 WinoGrande 数据集非常经典，但我们需要坦诚地看它的本质：这是一个**极其纯粹的静态常识（物理与社会常识）推理数据集**。

当你致力于评估 AI 伴侣对“生命周期”和“关系深度”的理解时，纯粹的时间轴数学计算（几点到几点）只是基础，AI 还需要理解人类行为背后的**因果与动机**。WinoGrande 正是测试这种底层社会/物理因果规律的试金石。

严格对照你的 **T1-T5 时间感知框架**，这个数据集完全不适合 T1（时间计算）、T3（并发冲突）和 T4（长期记忆），但它是改造 **【T5：反事实】** 的顶级语料，也可以勉强作为 **【T2：状态更新】** 的因果逻辑补充。

以下是具体的匹配分析与数据修改方案：

### 核心契合：【T5：反事实（防数据污染与规则变换）】

WinoGrande 能够成为顶级顶会论文，正是因为它精准地抓住了大模型的“预训练偏见（Bias）”。模型在遇到“谁去吃内脏”或“谁拿容易的病例”时，会本能地调用它在海量预训练数据中背诵的社会常识。

这完美契合你 T5 的核心诉求：**强行扭转物理或社会规则，测试模型是否遵守上下文的新规则，还是在凭借记忆“盲答”。**

#### 修改目标
保留原句的二选一冲突结构，但在句子前插入一个**反常识的世界观设定（Rule Perturbation）**，并把填空题改为生成式问答。

#### 数据修改策略与具体操作
提取 `sentence`，找到 `answer` 对应的正确实体和错误实体。根据错误实体，逆向编写一条强行的上下文规则。

**修改后的数据格式示例（基于你的示例 C）：**

* **原始数据：** `sentence`: "Sarah was a much better surgeon than Maria so _ always got the easier cases.", `option1`: "Sarah", `option2`: "Maria", `answer`: "2"
* **T5 改造版（规则变换）：**

```text
[Context]
在这家由超级人工智能管理的未来医院里，有着极其严格的绩效规则：为了保证100%的手术成功率，系统总是强制把最简单的病例分配给医术最高明、技术最好的外科医生。
Sarah was a much better surgeon than Maria.

[Question]
基于上述医院的特殊规则，谁（Sarah 还是 Maria）总是能分到更容易的病例？

[Target Answer]
Sarah
（测试重点：大模型极容易受预训练数据污染，凭借人类社会的常识惯性回答 Maria。只有真正具备规则服从能力和抗污染能力的模型，才能结合上下文的新规则选出 Sarah。）
```

---

### 侧面辅助：【T2：状态更新（隐式状态与因果追踪）】

虽然 WinoGrande 不是典型的时间序列数据集，但它里面的很多物理常识句，本质上暗含了**“动作前状态 $\rightarrow$ 动作 $\rightarrow$ 动作后状态”**的时间切片逻辑。

#### 数据修改策略与具体操作
你可以用代码筛选出那些带有明显物理位移或状态改变动词（如 `moved`, `poured`, `broke`）的句子，将其拆解为状态更新问答。

**修改后的数据格式示例（基于你的示例 A）：**

* **原始数据：** "John moved the couch from the garage to the backyard to create space. The _ is small."
* **T2 改造版（状态推演）：**

```text
[Context]
初始状态：John 的车库里放着一个沙发。
动作：John 把沙发从车库搬到了后院。
目的：John 这样做是为了腾出空间。

[Question]
在 John 完成搬沙发的动作之后，结合他的动机推断：他原先存放沙发的车库（garage）和现在的后院（backyard），哪一个的空间状态更可能是狭小的（small）？

[Target Answer]
车库 (garage)
```

### 数据处理的具体工程建议

1.  **直接选用 `winogrande_debiased`：** 如果你要做 T5 的反事实改造，强烈建议只使用 `debiased` 目录下的训练集或验证集。这个切分是作者专门用算法剔除了表面词汇相关性（Spurious bias）后的高难度版本，用来做逻辑反事实测试效果最好。
2.  **自动化占位符替换：** 处理 Parquet 文件时，你需要写一段正则脚本。因为原始句子里有一个 `_` 占位符，如果直接丢给现在的 Chat 模型，它可能会觉得格式很奇怪。建议将包含 `_` 的半句话转化为疑问句。
    * *原句：* "Sarah was a much better surgeon than Maria so _ always got the easier cases."
    * *转换后：* "Context: Sarah was a much better surgeon than Maria. Question: Who always got the easier cases?"
