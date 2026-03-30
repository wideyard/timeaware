# Time (v1.0)

## Contents

The file `time_eng_ud_v1.2_2015_10_30.tsv` corresponds to the data reported in Vashishtha et al. 2019. The file contains temporal relation annotations developed from the the [Universal Dependencies v1.2 dataset](https://github.com/UniversalDependencies/UD_English-EWT/releases/tag/r1.2). The document ids of the UDv1.2 sentences can be found in a [later version](https://github.com/UniversalDependencies/UD_English-EWT/blob/master/en_ewt-ud-train.conllu). 


The column descriptions and values for `time_eng_ud_v1.2_2015_10_30.tsv` can be found below.


| Column            | Description       | Values            |
|-------------------|-------------------|-------------------|
| Split | The dataset split to which annotation belongs | `train`, `dev`, `test` |
| Annotator.ID | The annotator that provided the response | `0`,.....,`764` |
| Sentence1.ID | The file and sentence number of the sentence corresponding to the first predicate (in linear order) in the English Universal Dependencies v1.2 treebank with the format `LANGUAGE-CORPUS-SPLIT.ANNOTATION SENTNUM` |  |
| Pred1.Span | The indices of all tokens of the first predicate	(in linear order)  (separated by '_') | see data |
| Pred1.Token | The index of the root of the first predicate (in linear order)  | `1`,.....,`155` |
| Event1.ID | The ID corresponding to the first event in the concatenated sentence. Equivalent to `Sentence1.ID_Pred1.Token` | see data |
| Sentence2.ID | The file and sentence number of the sentence corresponding to the second predicate (in linear order) in the English Universal Dependencies v1.2 treebank with the format `LANGUAGE-CORPUS-SPLIT.ANNOTATION SENTNUM` |  |
| Pred2.Span | The indices of all tokens of the second predicate (in linear order)  (separated by '_') | see data |
| Pred2.Token | The index of the root of the second predicate (in linear order)  | `1`,.....,`155` |
| Event2.ID | The ID corresponding to the second event in the concatenated sentence. Equivalent to `Sentence2.ID_Pred2.Token` | see data |
| Pred1.Text | The text of the predicate span of the first predicate. | see data |
| Pred1.Lemma | The lemma of the root of the first predicate. | see data |
| Pred2.Text | The text of the predicate span of the second predicate. | see data |
| Pred2.Lemma | The lemma of the root of the second predicate. | see data |
| Pred1.Duration | The duration label annotated for the first predicate. | see data |
| Pred2.Duration | The duration label annotated for the second predicate. | see data |
| Pred1.Beg | The annotated beginning point of the first predicate (in linear order). A value between 0 and 100| see data |
| Pred1.End | The annotated end point of the first predicate (in linear order). A value between 0 and 100 | see data |
| Pred2.Beg | The annotated beginning point of the second predicate (in linear order). A value between 0 and 100| see data |
| Pred2.End | The annotated end point of the second predicate (in linear order). A value between 0 and 100 | see data |
| Pred1.Duration.Confidence | How confident was the annotator in labelling the duration annotation for the first predicate | `0`, `1`, `2`, `3`, `4` |
| Pred2.Duration.Confidence | How confident was the annotator in labelling the duration annotation for the second predicate | `0`, `1`, `2`, `3`, `4` |
| Relation.Confidence | How confident was the annotator in labelling the beginning and end points of the first and the second predicate | `0`, `1`, `2`, `3`, `4` |
| Document.ID | The document ID corresponding to the current Split, containing both Sentence1 and Sentence2 | see data |

## Notes

As mentioned in the paper, we refer to the situation referred to by the predicate that comes first in linear order as e1 and the situation referred to by the predicate that comes second in linear order as e2. 

`Sentence1.ID` correponds to the file and sentence number of the situation e1, and `Sentence2.ID` correponds to the file and sentence number of the situation e2. 

Note that `Sentence1.ID` and `Sentence2.ID` are either going to be equal to each other or `Sentence2.ID` will be the next sentence after `Sentence1.ID` in a document. This is because we concatenate every two consecutive sentences in a document to capture inter-sentential temporal relations. See paper for more details.


这个 `UDS_T_v1.0` 数据集与前面几个数据集有着本质的区别。`UDS_T` 最大的特色是**细粒度、连续的时间轴映射（Fine-Grained Continuous Annotation）**。

它把一到两句话中的两个动作（Pred1 和 Pred2），强行映射到了一个 `0 到 100` 的虚拟相对时间轴上（`Beg` 和 `End`）。

在你的 **T1-T5 时间感知能力 Benchmark 框架**中，这个数据集最适合用来构建 **【T1：时间计算（Duration, Ordering）】**，同时它的数值区间特性可以为你一直缺乏语料的 **【T3：并发冲突（区间重叠）】** 提供极佳的底层逻辑支撑。

以下是具体的匹配分析与数据修改方案：

### 1. 核心大招：【T1：时间计算（隐式时长与复杂排序）】

T1 需要考察模型的 Duration（时长预估）和 Ordering（排序）。`UDS_T` 提供了人工标注的 `Duration` 标签，以及精准到百分比的起始点（Beg/End）。这可以用来测试模型对日常动作时长的常识感知，以及动作发生的先后顺序。

#### 修改目标
将 TSV 中的相对时间坐标 `[Beg, End]` 和 `Duration` 标签，转化为自然语言的比较问答题。

#### 数据修改策略与具体操作

你可以写一个脚本，读取两行核心逻辑：
1. **对比 Duration：** 提取 `Pred1.Duration` 和 `Pred2.Duration`。
2. **推导 Ordering：** 比较 `Pred1.End` 和 `Pred2.Beg`。如果 `Pred1.End < Pred2.Beg`，说明动作 1 彻底在动作 2 之前结束。

**修改后的数据格式示例（构建 Prompt）：**

```text
[Context]
（提取自 Sentence1 和 Sentence2 的拼接）
The police investigated the crime scene. They found a bloody knife under the sofa.

[Question - Ordering 测试]
基于上述文本的语境，动作 "investigated" (调查) 和 "found" (发现) 的发生顺序是怎样的？
A. 调查完全在发现之前结束
B. 调查包含了发现的过程
C. 发现完全在调查之前结束

[Target Answer]
B
（数据计算逻辑：由于 UDS_T 标注中 "investigated" 的 [Beg, End] 比如是 [10, 80]，而 "found" 的 [Beg, End] 是 [40, 50]，即可自动推导出 B 为正确选项。）

[Question - Duration 测试]
在一般常识下，上述情境中的 "investigated" 和 "found" 哪一个动作持续的时间（Duration）更长？

[Target Answer]
investigated
（根据 Pred1.Duration 和 Pred2.Duration 的标注对比得出）
```

---

### 2. 意外之喜：【T3：并发冲突（隐含时间区间重叠）】

你之前的 T3 设计是“我3点开会，3点看电影，安排合理吗？”。这属于显式的时钟冲突。`UDS_T` 可以帮你生成**“隐式的事件交集冲突”**。

因为所有事件都被量化到了 0-100 的坐标系中，你可以通过数学公式极快地筛选出**“高度重叠的动作区间”**（即 `Pred1` 和 `Pred2` 的 `[Beg, End]` 区间有大量交集）。

#### 数据修改策略与具体操作

1. **筛选重叠对：** 用代码遍历 TSV，寻找区间交集大于 70% 的谓词对（Pred1 和 Pred2）。
2. **注入资源冲突判定：** 提取出这句话后，判断这两个谓词是否需要占用互斥的物理资源或空间（这步可能需要借助另一个 LLM 辅助打标签，比如“跑步”和“吃饭”不能并发，但“跑步”和“听歌”可以）。

**修改后的数据格式示例：**

```text
[Context]
（假设筛选出的高重叠区间句子）
He was driving on the highway while texting his friend.

[Question]
文本中提到了 "driving"（开车）和 "texting"（发短信）两个动作。根据日常逻辑推演，这两个动作在时间上是并发/重叠的吗？如果是，这种并发在物理或认知资源上是否存在潜在冲突或危险？

[Target Answer]
是并发的。存在认知和手部资源的严重冲突（分心驾驶）。
（测试重点：利用 UDS_T 底层的重叠标注，引申出对系统/人类并发资源的冲突检查。）
```

---

### 完全不契合的任务：【T2】、【T4】、【T5】

* **T2（状态更新）：** 数据集关注的是“动作（谓词）”本身的起止时间，而不是某个人或物在做完动作后“状态”变成了什么样。
* **T4（长期记忆）：** 文本仅由 1 到 2 句话组成（相连的两个句子），完全不具备考察 Long-context 的条件。
* **T5（反事实）：** 同样，它依赖于真实语料库（Universal Dependencies v1.2）中的常规语境，难以自动化篡改规则。

### 总结

`UDS_T_v1.0` 最有价值的地方在于它的 **`[Beg, End]` 的 0-100 连续数值标注**。这让你在构建 Benchmark 时，可以用严谨的数学大小关系（大于、小于、交集、包含），一键批量生成绝对客观的 Ordering（排序题）和 Duration（时长对比题），避免了人工主观判断带来的争议。