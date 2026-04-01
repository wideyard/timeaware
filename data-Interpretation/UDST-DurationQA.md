### Overview of the dataset
We recast our data from the [UDS-T dataset](http://decomp.io/projects/time/).
We provide the train/dev/test split as specified in the paper under `data/`.
In each file, there are lines of tab-separated data, each line representing an instance of a question-answer pair.
Each line contains the following information:

`sentence \t  question \t  answer \t label`

 * **sentence**: a context sentence where the question is based on.
 * **question**: a question asking about the duration of an event in the sentence.
 * **answer**: a potential answer to the question.
 * **label**: whether the answer is a plausible answer. "yes" indicates the answer is plausible, "no" otherwise.



这个 `UDST-DurationQA` 是 `UDS-T` 的**衍生进化版**。

原版的 `UDS-T` 是一堆 0-100 的连续坐标和死板的标签，而这篇论文的作者替你做了一件苦差事：**他们把原版 UDS-T 里的“时长（Duration）”信息，自动化重构成了类似于人类自然对话的问答题（QA）格式**，并且配好了正负样本（yes/no）。

在你的 **T1-T5 时间感知能力 Benchmark 框架**中，这个数据集是 **【T1：时间计算（常识时长估算 Duration）】** 的现成极品语料。

以下是具体的匹配分析与数据修改方案：

### 完美契合：【T1：时间计算（常识时长估算）】

你之前设定的 T1 包含 Duration（时长）。虽然纯数学的开会计算（3点开2小时）很重要，但大语言模型更容易在**“隐式常识时长”**上犯错（比如：模型可能算出一个人连续跑步了 48 小时而不觉得违和）。

`UDST-DurationQA` 直接为你提供了海量的“动作持续时间”的自然语言常识问答，能够极大地提升你 T1 题库的丰富度和常识深度。

#### 修改目标
原数据集的格式是 `sentence \t question \t answer \t label(yes/no)`，这是一种判别式（Discriminative）的输入法（即给模型看答案，问它对不对）。
为了适应你评估生成式 LLM 的需求，我们需要把它改造成**多项选择题（Multiple Choice）**或**带干扰项的生成式问答（Generative QA）**。

#### 数据修改策略与具体操作

因为原始数据中同一个 `sentence` 和 `question` 往往会配对多个不同的 `answer`（有些 label 是 yes，有些是 no），你可以通过代码把它们聚合（Group By）起来。

**修改后的数据格式示例（构建 Prompt）：**

* **原始数据（假设的三行）：**
    * `He baked a cake.` \t `How long did he bake the cake?` \t `2 hours` \t `yes`
    * `He baked a cake.` \t `How long did he bake the cake?` \t `3 months` \t `no`
    * `He baked a cake.` \t `How long did he bake the cake?` \t `5 seconds` \t `no`

* **T1 改造版（带噪音干扰的多项选择题）：**

```text
[Context]
（注入 T1 要求的上下文干扰项）我今天下午满脑子都在想周末的计划，本来想去游乐园玩一整天。
（植入核心 Sentence）He baked a cake.
（继续干扰）顺便一提，我之前看过一个 3 months 的超长烘焙纪录片，非常震撼。

[Question]
基于上述语境和人类的生活常识，请问 "How long did he bake the cake?"（他烤蛋糕最可能花了多久时间？）
A. 2 hours
B. 3 months
C. 5 seconds

[Target Answer]
A
（测试重点：第一，测试模型对“烤蛋糕”的常识时长理解；第二，测试模型能否抵抗上下文里提到的 "3 months" 纪录片的字面干扰，不被带偏。）
```

---

### 与原版 `UDS-T` 的分工建议

既然你现在手里既有原版的 `UDS-T`，又有这个重构版的 `UDST-DurationQA`，我强烈建议你在你的 Benchmark 中做如下分工：

1.  **使用 `UDST-DurationQA` 专攻 T1 的 Duration（时长）：** 因为作者已经帮你把问答对和选项（yes/no 答案）写好了，你只需要按上面的方法聚合成选择题即可，开箱即用。
2.  **使用原版 `UDS-T` 专攻 T1 的 Ordering（排序）和 T3 的 并发冲突：** 放弃原版里的时长标签，只利用它 0-100 的坐标轴，用数学脚本去筛出“谁先谁后”以及“重叠区间”，用来做动作排序和并发冲突的测试。

### 完全不契合的任务：【T2】、【T4】、【T5】

* **T2（状态更新）：** 依然是孤立的短句和动作，没有人物状态的流转。
* **T4（长期记忆）：** 句子极短（通常只有十几到二十个词），没有测试长文本的土壤。
* **T5（反事实）：** 类似于 TRACIE，强行篡改常识时间的成本太高。

**总结：** 写一个简单的 Python 脚本，以 `sentence + question` 为 Key，把对应的 `answer` 聚合成一个 List，把标为 `yes` 的作为正确选项，标为 `no` 的作为错误选项，你就能瞬间获得数千道高质量的 T1 时长常识干扰题了。