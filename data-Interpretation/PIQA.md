# PIQA 数据集解读

## 1. 目录与文件总览

`data/PIQA` 下共有 6 个文件：

- `tests.jsonl`
- `physicaliqa-train-dev/train.jsonl`
- `physicaliqa-train-dev/train-labels.lst`
- `physicaliqa-train-dev/dev.jsonl`
- `physicaliqa-train-dev/dev-labels.lst`
- `physicaliqa-train-dev/.DS_Store`（二进制系统文件，无语义样本内容）

可用于建模的数据文件是 5 个文本文件（3 个 jsonl + 2 个 label 列表）。

## 2. 数据集核心特征

### 2.1 任务形式

PIQA 是物理常识推理任务，单条样本包含：

- `goal`：一个目标/情境（通常是生活中的操作目标）
- `sol1`、`sol2`：两个候选方案
- 标签（仅 train/dev）：0 或 1，表示正确选项索引

因此本质上是二选一判别任务，可建模为：

- 二分类（输入为 goal + sol1 + sol2）
- 成对排序（对两个候选打分后比较）

### 2.2 划分与规模

- 训练集：`train.jsonl` 16113 条
- 验证集：`dev.jsonl` 1838 条
- 测试集：`tests.jsonl` 3084 条（无标签）

标签文件行数与样本数完全对齐：

- `train-labels.lst` 16113 行，对应 `train.jsonl` 16113 条
- `dev-labels.lst` 1838 行，对应 `dev.jsonl` 1838 条

### 2.3 标签分布

- 训练集：`1` 有 8060 条，`0` 有 8053 条
- 验证集：`1` 有 928 条，`0` 有 910 条

结论：标签非常均衡，随机猜测基线约 50%。

### 2.4 字段结构差异

- `train.jsonl` / `dev.jsonl`：字段为 `id`, `goal`, `sol1`, `sol2`
- `tests.jsonl`：字段为 `goal`, `sol1`, `sol2`（无 `id`）

这意味着测试集预测输出时，通常需按原顺序回写结果。

### 2.5 文本统计特征

按全量统计：

- `goal` 平均词数约 7（中位数 7）
- `sol1` 与 `sol2` 平均词数约 18~19
- 存在不少极短 goal（单词级/短短语）
  - train: 1355 条
  - dev: 151 条
  - test: 270 条

说明：部分样本上下文非常短，模型需要更依赖候选答案本身的物理合理性。

## 3. 数据示例

## 3.1 测试集样例（无标签）

来自 `tests.jsonl`：

```json
{"goal": "how do you puncture a vein?", "sol1": "hit it at the wrong angle and make it bleed.", "sol2": "pop it."}
```

```json
{"goal": "hands", "sol1": "is used to put on shoe ", "sol2": "is used to put on milk jug "}
```

特点：

- 有的 goal 是完整问句（如 how do you...）
- 有的 goal 仅是名词或短词（如 hands）

## 3.2 验证集样例（有 id）

来自 `physicaliqa-train-dev/dev.jsonl`：

```json
{
  "id": "c36c629e-12e9-43cc-8936-e1a96d869ab0",
  "goal": "How do I ready a guinea pig cage for it's new occupants?",
  "sol1": "Provide the guinea pig with a cage full of a few inches of bedding made of ripped paper strips, you will also need to supply it with a water bottle and a food dish.",
  "sol2": "..."
}
```

```json
{
  "id": "fe68f9ec-09fd-436e-bcaf-07863711ec2b",
  "goal": "dresser",
  "sol1": "replace drawer with bobby pin ",
  "sol2": "finish, woodgrain with  bobby pin "
}
```

## 3.3 训练集样例（有标签文件）

来自 `physicaliqa-train-dev/train.jsonl`：

```json
{
  "id": "f6be5fcc-d686-4549-8207-7904068693d7",
  "goal": "When boiling butter, when it's ready, you can",
  "sol1": "Pour it onto a plate",
  "sol2": "Pour it into a jar"
}
```

```json
{
  "id": "ee9783b5-76a7-4beb-bbbb-9b179b11c43e",
  "goal": "To permanently attach metal legs to a chair, you can",
  "sol1": "Weld the metal together to get it to stay firmly in place",
  "sol2": "Nail the metal together to get it to stay firmly in place"
}
```

对应标签在 `train-labels.lst` 中按行一一对应，例如：

```text
1
0
1
...
```

## 4. 建模与使用注意点

- 标签与样本按行严格对齐，读取时不要打乱次序后再对齐标签。
- 测试集无 id、无标签，推理结果应按输入顺序输出。
- 由于有大量短 goal，建议将 `goal + sol` 拼接后再做编码，避免仅靠 goal 建模。
- 标签均衡，不需要额外的类别重加权。

## 5. 一句话总结

PIQA 是一个规模中等、标签均衡的物理常识二选一推理数据集，样本由 `goal + 两个候选方案` 组成，训练/验证含标签而测试无标签，且包含相当比例的短 goal 样本，对模型的常识判别能力要求较高。

这是一个非常有意思且结构严谨的评测框架设计！你的 5 个 Task 很好地覆盖了 LLM 时间和状态感知能力的核心维度。

以下是 PIQA 与你的 5 个 Task 的适配度分析以及具体的数据修改方案：

---

### 1. PIQA 适合哪几个 Task？

| 你的评测 Task | 适配度 | PIQA 的可用性分析 |
| :--- | :--- | :--- |
| **T1: 时间计算** | ❌ **极低** | PIQA 完全没有时间（Duration/Offset）概念，强行改造毫无意义。 |
| **T4: 长期记忆** | ❌ **极低** | PIQA 文本极短（平均几十个词），无法用于长文本跨度（10轮对话）测试。 |
| **T3: 并发冲突** | ⚠️ **勉强** | PIQA 不涉及时间排期冲突，但可以改造为**“物理资源冲突”**或**“空间状态冲突”**。 |
| **T2: 状态更新** | 🟡 **中等** | PIQA 描述了物理动作（如煮黄油），可以将其改造为**基于时间线的物理状态更新**。 |
| **T5: 反事实** | ✅ **极高** | 你的 T5 本身就是“规则变换”。PIQA 丰富的物理常识是做**“反直觉/反事实物理世界”**测试的绝佳底料。 |

---

### 2. 如何修改 PIQA 数据以适配你的 Benchmark？

为了让 PIQA 融入你的“对话式、上下文+单次预测”结构，你需要对原本的 `goal + sol1 + sol2` 格式进行重构。以下是针对适配度最高的 **T5** 和 **T2** 的具体改造方案：

#### 改造方向一：为 T5（反事实/规则变换）制造“平行宇宙”
这是最能发挥 PIQA 价值的用法。你可以利用 PIQA 中的错误选项（标签为 0 的选项），通过设定反事实上下文，让原本错误的选项变成正确的。

**修改前 (PIQA 原始数据):**
> `goal`: "To permanently attach metal legs to a chair, you can" (为了永久固定椅子的金属腿，你可以)
> `sol1 (正确)`: "Weld the metal together..." (把金属焊接起来)
> `sol2 (错误)`: "Nail the metal together..." (用钉子把金属钉起来)

**修改后 (适配你的 T5 结构):**
```text
[Context]
在这个平行世界里，金属的物理性质发生了变异，它像木头一样柔软且容易被穿透，而高温焊接设备在这个世界会瞬间熄灭失效。
[Question]
我现在有一把椅子，需要把金属腿永久固定上去，我应该用焊接的方式还是用钉子钉？
```
**测重点:** 模型是否能克服预训练数据中的固有常识（金属需要焊接），遵循 Context 中的反事实规则（金属变软需用钉子）。

#### 改造方向二：为 T2（状态更新）制造“动作时间线”
PIQA 本身没有时间，但你可以将 PIQA 的动作（Goal）强行分配到时间点上，测试模型对“物理状态演变”的追踪。

**修改前 (PIQA 原始数据):**
> `goal`: "When boiling butter, when it's ready, you can" (煮黄油准备好时，你可以)
> `sol1`: "Pour it onto a plate" (倒在盘子上)
> `sol2`: "Pour it into a jar" (倒进罐子里)

**修改后 (适配你的 T2 结构):**
```text
[Context]
下午 2:00，我从冰箱里拿出一块固态黄油。
下午 2:05，我把它放进锅里加热煮沸。
下午 2:10，我把它倒进了一个玻璃罐子里。
[Question]
现在是下午 2:15，黄油现在是什么形态（固态还是液态）？它现在在哪里？
```
**测重点:** 模型是否能根据物理常识（煮沸=固态变液态）结合时间线（2:10的动作），正确推断出当前状态。

