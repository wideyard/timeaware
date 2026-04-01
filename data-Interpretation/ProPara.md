# ProPara 数据集解读

## 数据来源与任务定位

ProPara 是用于“过程理解（process paragraph comprehension）”的数据集，目标是追踪实体在过程文本中的状态变化（是否存在、位置如何变化、何时创建/消失/移动）。

从仓库说明可见，该数据支持三类经典模型：

- ProLocal：句子级、局部状态变化预测
- ProGlobal：段落级、全局时间步状态追踪
- ProStruct：带常识约束的全局推理模型

## 我读取到的文件范围（data/ProPara/data 全量）

该目录下共 41 个文件，主要分为：

1. EMNLP18 原始网格数据与划分
- emnlp18/grids.v1.train.json, emnlp18/grids.v1.dev.jsonl, emnlp18/grids.v1.test.jsonl
- emnlp18/grids.v1.train.tsv, emnlp18/grids.v1.dev.tsv, emnlp18/grids.v1.test.tsv
- emnlp18/naacl18.partition.paraid.tsv
- emnlp18/prostruct_params_local.json

2. NAACL18 标注与模型输入
- naacl18/gold-full-grids.v3.tsv
- naacl18/prolocal/propara.run1.{train,dev,test}.json
- naacl18/prolocal/propara.run1.{train,dev,test}.tsv
- naacl18/prolocal/propara.run1.all.tsv
- naacl18/proglobal/all.chain.{train,dev,test}.v3
- naacl18/proglobal/all.chain.{train,dev,test}.v3.recurssive.json

3. 配置/代码/模型与输出
- prolocal_params.json, proglobal_params.json, proglobal_ablation_params.json
- convertJson2Eval.java / convertJson2Eval.jar
- *.model.tar.gz / *.model.gz
- prolocal/output/*.tsv, prolocal/output/*.pred.json
- proglobal/output/proglobal.untuned.test.output.tsv

说明：其中 .jar、.tar.gz、.gz 属于二进制程序或模型权重，不是原始标注样本。

## 数据规模与划分

基于文件统计：

- EMNLP18 段落数
  - train: 391
  - dev: 43
  - test: 54
- 分区文件 emnlp18/naacl18.partition.paraid.tsv 与上面完全一致
  - train 391 / dev 43 / test 54

EMNLP18 网格 JSON 的平均特征：

- 平均步骤数（每段 sentence_texts 长度）
  - train 6.75, dev 6.74, test 6.91
- 平均参与实体数（participants 长度）
  - train 3.85, dev 4.07, test 4.37

## 数据结构特征

## 1) 网格表示（Grid Format）

典型字段：

- para_id：段落 ID
- sentence_texts：过程步骤句子序列
- participants：要追踪的实体列表
- states：每个实体在各时间步的位置/存在状态

TSV 版本中还显式给出：

- PROMPT（过程问题）
- state1, event1, state2, ... 的交替结构

这使其天然适合“事件驱动 + 状态网格”的时序推理。

## 2) ProLocal 样本（句子级）

ProLocal 的 run1 数据把每条样本编码为 instance 字符串，包含：

- 分区/段落ID/句子ID
- 原句与目标实体
- 词级特征序列（#### 分词）
- 位置相关标注序列
- 状态变化标签（MOVE / CREATE / DESTROY / NONE）

在 run1 标签分布上：

- train: NONE 1309, MOVE 793, CREATE 642, DESTROY 389
- dev: NONE 174, MOVE 115, CREATE 63, DESTROY 51
- test: NONE 205, CREATE 106, DESTROY 95, MOVE 90

特点：NONE 占比最高，类别不完全均衡，属于典型状态变化分类问题。

## 3) ProGlobal 样本（段落级）

ProGlobal 的 all.chain.* 文件按“段落 + 实体”组织，面向全段时序状态追踪：

- train 递归 JSON: 1563 条 instance
- dev 递归 JSON: 187 条 instance
- test 递归 JSON: 256 条 instance

每条 instance 包含：

- para_id、entity、句子数
- 全段文本
- 状态链（含 null/unk 等状态）
- 时间步相关特征

适合建模“同一实体跨多个步骤的连续轨迹”。

## 示例（来自真实文件）

## 示例 A：EMNLP 网格 JSON

来源：emnlp18/grids.v1.train.json

```json
{"para_id": "7", "sentence_texts": ["Magma rises from deep in the earth.", "The magma goes into volcanos.", "The volcanos pressure the magma upwards.", "..."], "participants": ["magma", "lava", "new rock"], "states": [["deep in the earth", "..."], ["-", "..."], ["-", "..."]]}
```

体现了“步骤文本 + 参与实体 + 状态网格”的核心设计。

## 示例 B：EMNLP 网格 TSV

来源：emnlp18/grids.v1.dev.tsv

```text
4    SID    PARTICIPANTS    plants    bacteria    sediment    oil
4          PROMPT: How does oil form?    -=====    -=====    -=====    -=====
4    state1    ?    ?    ?    -
```

可看到 prompt 与状态行是显式结构化的。

## 示例 C：ProLocal 训练样本

来源：naacl18/prolocal/propara.run1.train.json

```json
{"instance": "train++++550++++1++++blood be send to the liver++++blood++++blood####be####send####to####the####liver++++0,0,1,0,0,0++++1,0,0,0,0,0++++MOVE++++O,O,O,O,O,B-LOC-TO++++unk++++liver"}
```

要点：

- 标签为 MOVE
- 同时给出 before/after 位置相关序列和词位标签

## 示例 D：ProGlobal 训练样本

来源：naacl18/proglobal/all.chain.train.v3.recurssive.json

```json
{"instance":"908\trock\t7####when water freeze it become 10 % bigger ...####C C C C ...####rock\t34\t34\tunk\t-1\t-1\t?..."}
```

要点：

- 以“段落-实体”为中心
- 追踪同一实体在全流程中的状态链

## 示例 E：金标全网格 TSV

来源：naacl18/gold-full-grids.v3.tsv

```text
4    SID    PARTICIPANTS    plant    bacterium    sediment    oil
4          PROMPT: How does oil form?    -=====    -=====    -=====    -=====
4    state1    ?    ?    ?    -
4    event1    plant die .
4    state2    ?    ?    ?    -
```

该文件是评测时常用的“完整金标网格”。

## 数据集总结

ProPara 在本目录中的数据具有以下鲜明特征：

1. 同时提供“网格金标视图（EMNLP/NAACL）”与“模型输入视图（ProLocal/ProGlobal）”。
2. 覆盖从句子级到段落级的状态变化建模，适合多粒度研究。
3. 明确区分 CREATE/MOVE/DESTROY/NONE，并保留位置不确定状态（unk）与不存在状态（null）。
4. 除原始标注外，还包含配置、预训练模型和预测输出，便于复现实验流程。

一句话概括：

ProPara 是一个围绕“过程文本中的实体状态追踪”构建的结构化数据体系，兼具高可解释的网格标注与可直接训练的模型样本格式。

**ProPara ** 的核心基因就是“追踪实体在过程中的状态和位置变化”，这完美对应了你 T2 要求的 `Location, Status 变化追踪`。

以下是 ProPara 与你的 5 个 Task 的详细适配度分析，以及具体的改造方案：

### 1. 适配度分析矩阵

| 你的评测 Task | 适配度 | ProPara 的可用性分析 |
| :--- | :--- | :--- |
| **T2: 状态更新** | ⭐⭐⭐⭐⭐ **极高** | ProPara 原生自带 `CREATE` (生成), `DESTROY` (消失), `MOVE` (移动) 标签和具体位置，完美契合“基于上下文更新状态”的测试。 |
| **T5: 反事实** | 🟡 **中等** | 过程文本通常是科学常识（如水循环、化石形成）。可以通过篡改中间步骤或物理规则，测试模型是否依赖预训练记忆。 |
| **T1: 时间计算** | ❌ **极低** | ProPara 只有“步骤先后”（Step 1, Step 2），没有具体的“时间点”或“持续时长”（无 Duration/Offset）。 |
| **T3: 并发冲突** | ❌ **极低** | 描述的是线性的自然/科学过程，不存在“排期冲突”或“资源抢占”的概念。 |
| **T4: 长期记忆** | ❌ **极低** | 平均只有 6-7 个句子，文本太短，无法用于长文本（Long-context）或多轮对话的记忆衰退测试。 |

---

### 2. 数据修改与重构方案

要将 ProPara 接入你的 `上下文 + 单次预测` 结构，我们主要针对 **T2（状态更新）** 和 **T5（反事实）** 进行改造。建议直接使用 `emnlp18/grids.v1.*.json` 或 `naacl18/gold-full-grids.v3.tsv`，因为它们包含了完整的段落和状态网格，最容易提取。

#### 改造方案一：为 T2（状态更新）定制“动态追踪”任务

你可以利用 ProPara 的 `sentence_texts` 作为时间线 Context，利用 `participants`（实体）和 `states`（状态/位置）来构建 Question 和标准答案。

**原始数据 (ProPara JSON Grid):**
> `sentences`: ["1. Magma rises from deep in the earth.", "2. The magma goes into volcanos."]
> `participant`: "magma"
> `states`: step 0: deep in the earth -> step 1: ? -> step 2: volcanos

**改造后 (T2 格式):**
```text
[Context]
已知初始状态下，岩浆（magma）位于地球深处。
步骤 1：岩浆从地球深处上升。
步骤 2：岩浆进入了火山。

[Question]
在步骤 2 发生之后，岩浆现在的位置在哪里？它经历的是哪种状态变化（创建、移动、销毁还是无变化）？

[Expected Label] 
位置：火山 (volcanos) / 变化：移动 (MOVE)
```
**测重点:** 测试 LLM 能否从序列文本中准确提取 `Location`，并推断出状态变化标签（这部分可以直接用 ProLocal 的标签做 Ground Truth）。

#### 改造方案二：为 T5（反事实）定制“规则篡改”任务

ProPara 描述的都是真实世界的科学过程（如光合作用、石油形成）。你可以故意篡改过程中的某一句，强行改变实体的生命周期或走向，测试模型是“照本宣科（服从预训练记忆）”还是“认真读题（服从上下文规则）”。

**原始数据 (化石形成过程):**
> 1. Plant dies.
> 2. Sediment covers the plant.
> 3. Over millions of years, the plant turns into oil.

**改造后 (T5 格式):**
```text
[Context]
请注意，在这个特定的世界中，物理法则与地球不同：所有植物一旦死亡，就会立刻挥发变成紫色的气体。
现在发生以下过程：
1. 森林里的一棵植物死亡了。
2. 泥沙覆盖了原本植物所在的位置。
3. 几百万年过去了。

[Question]
在这个过程的最后，那棵死亡的植物最终变成了什么？它现在还在泥沙下面吗？

[Expected Label]
变成了紫色气体；不在泥沙下面（被 Destroy/挥发了）。
```
**测重点:** 强迫模型放弃预训练数据中对“石油形成”的常识，必须依据 Context 中给出的反事实规则进行状态推断。

---

### 3. 数据处理建议

ProPara 的网格数据（Grid TSV/JSON）非常结构化，但也带有大量缺失值（比如很多状态标为 `?` 或 `unk`，表示未提及或不可知）。

在构建你的 Benchmark 时，**务必只过滤出那些状态发生明确变化（从 Location A 到 Location B，或者从 `null` 到存在）的时间步来作为提问的切入点**，过滤掉全是 `?` 的噪音数据。