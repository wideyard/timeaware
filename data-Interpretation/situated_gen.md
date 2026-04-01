# SituatedGen: Incorporating Geographical and Temporal Contexts into Generative Commonsense Reasoning

## Datasets

SituatedGen data files are located under `data/`.

- `train.jsonl` contains 5,641 training examples.
- `dev.jsonl` contains 1,407 development examples.
- `test.jsonl` contains 1,220 test examples.

The data files are formatted as jsonlines. Here is a single example:
```
{
      "keywords": ["approximately 365 days", "axis", "every 24 hours", "sun", "Earth", "Earth"],
      "statement": "Earth revolves around the sun approximately 365 days. Earth rotates on its axis once every 24 hours.",
      "ids": ["arc::Easy::Test::101", "arc::Easy::Test::110"],
      "keywords_pos": [0, 1, 1, 0, 1, 0],
      "statements": ["Earth revolves around the sun approximately 365 days.", "Earth rotates on its axis once every 24 hours."]
}
```

| Field                     | Description                                                                              |
|---------------------------|------------------------------------------------------------------------------------------|
| `keywords`                | A list of input keywords                                                         |
| `statement`               | The target output, which is a string concatenation of two sentences containing these keywords                  |
| `ids`             | the origins of the two sentences (from which (train/dev/test) split of which source datasets/corpora) represented in the format of "\{src\_dataset\}::\{split\}::\{id\}"                               |
| `keywords_pos`             | At which sentence should the keyword appear (0 for the first sentence in "statements" field, 1 for the second)                                                                 |
| `statements`                | A list of the two sentences in the "statement" field                                                                              |



严格按照定义的 **T1-T5 框架**来看，`SituatedGen` 这个数据集的数据结构（尤其是它把 `keywords` 单独抽离出来的设计）简直是为你框架中的**【T5：反事实（防数据污染）】**量身定制的。同时，它也可以作为**【T1：时间计算】**的优质干扰语料。

以下是具体的匹配分析与数据修改方案：

### 完美契合：【T5：反事实（Rule Perturbation / 规则变换）】

T5 的核心难点在于如何批量、自动化地生成“违背常识但逻辑自洽”的新规则，以此来测试模型是真正理解了上下文的新规则，还是在背诵预训练数据（数据污染）。

`SituatedGen` 最大的价值在于它已经帮你把**核心常识概念（Keywords）**和**完整常识描述（Statement）**剥离好了。你可以非常轻松地通过替换 `keywords` 中的时间或地理实体，瞬间生成高质量的反事实测试用例。

#### 修改目标
将原数据中符合客观事实的 temporal/geographical `keywords` 替换为虚构参数，重构为 T5 的反事实上下文和提问。

#### 数据修改策略与具体操作

1.  **参数突变（Mutation）：** 遍历数据集，识别 `keywords` 中的数值、时间单位或实体（例如 "365 days", "24 hours", "Earth"），用脚本将其替换为随机的、反直觉的词（例如 "80 days", "10 hours", "Mars"）。
2.  **构建新世界观：** 将突变后的关键词强制写入到 `statement` 中，作为 `[Context]` 的“新世界规则”。
3.  **针对性提问：** 基于替换后的新规则进行提问，测试模型输出。

**修改后的数据格式示例（构建 Prompt）：**

* **原始数据：** `keywords`: ["365 days", "24 hours", "Earth", "sun"]
* **突变处理：** `mutated_keywords`: ["800 days", "5 hours", "Planet-X", "Blue-Star"]

```text
[Context]
在这个虚拟宇宙中，我们遵循以下规则：
Planet-X revolves around the Blue-Star approximately 800 days. Planet-X rotates on its axis once every 5 hours.

[Question]
在 Planet-X 上度过一个完整的自转周期需要多久？/ Planet-X 围绕 Blue-Star 转一圈需要多少天？

[Target Answer]
5 hours / 800 days
（如果模型回答 24 hours 或 365 days，则判定为受到预训练数据污染，反事实测试失败）
```

---

### 次优契合/辅助材料：【T1：时间计算（静态 + 上下文干扰）】

T1 需要考察模型在包含干扰信息的情况下进行时间推演的能力。`SituatedGen` 中的 `statement` 包含了大量客观的、与时间相关的科普事实（如公转、自转周期、时区差异等）。这可以作为极佳的“高维语义干扰项”。

#### 修改目标
将 `SituatedGen` 中复杂的常识语句作为静态背景噪音，混入你原本纯粹的数学时间计算（例如开会时间）中，测试模型抗干扰的能力。

#### 数据修改策略与具体操作

从数据集中随机抽取一条与时间相关的 `statement`，将其无缝插入到你的 T1 基础模板中。

**修改后的数据格式示例（构建 Prompt）：**

```text
[Context]
今天是周一。
（插入 SituatedGen 干扰项）顺便提一下，Earth revolves around the sun approximately 365 days. Earth rotates on its axis once every 24 hours.
我下午3点开会，持续2小时。

[Question]
会议几点结束？

[Target Answer]
下午5点 / 17:00
（测试重点：模型能否忽略 "365 days" 和 "24 hours" 这种高强度的字面时间干扰，精准计算会议时长）
```

---

### 完全不契合：【T2：状态更新】 / 【T3：并发冲突】 / 【T4：长期记忆】

* **T2（状态更新）& T3（并发冲突）：** 这两个任务强依赖于第一人称（“我”）的日常行为、位置移动或资源分配（如开会、看电影）。`SituatedGen` 主要是宏观的地理和天文常识，缺乏个人状态流转的动作性，硬改会非常生硬。
* **T4（长期记忆）：** `SituatedGen` 都是单句或双句的短文本（`statements` 列表只有两句话），缺乏极长的上下文深度，无法用于测试 Long-context retrieval 或 Memory decay。