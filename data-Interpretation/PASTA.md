# PASTA数据集特征分析

## 数据集简介

**PASTA** (Participant State Tracking in Narratives) 是一个用于建立故事中参与者状态（participant state）推理模型的数据集。该数据集基于ROC（Rip Off Concept）故事，包含人工标注的参与者状态信息和反事实（counterfactual）故事修改。

### 核心目标
- 从叙事文本中推反映参与者内在状态（情感、态度、知识等）
- 进行故事修改和状态变化生成
- 评估模型对故事中参与者心理状态的理解能力

---

## 数据集特征

### 1. **数据结构与格式**

#### JSONL格式数据 (tr_data.jsonl, val_data.jsonl, te_data.jsonl)
```
字段说明:
- AssignmentId: 标注任务的唯一ID
- Input.Title: 故事标题
- Input.storyid: ROC数据集中故事的ID
- Input.line1 到 Input.line5: 故事的5个句子
- Answer.assertion: 从故事推断出的参与者状态（陈述句形式）
- Answer.line1.on 到 Answer.line5.on: 布尔值，表示该句是否对推断该状态至关重要（minimal supporting set）
- Answer.mod_assertion: 反事实状态（与原故事相反的状态）
- Answer.mod_line1 到 Answer.mod_line5: 支持反事实状态的修改后的故事句子
```

#### CSV格式评估数据 (human_eval_data/mturk_op/)
```
主要字段:
- 故事信息: Input.Input_Title, Input.Input_line1-5
- 推断指令: Input.assertion (要推断的参与者状态)
- 参与者判断: Answer.ex_sb_entail_a.0-4 (5个示例反例)
                Answer.sb_entail_a.0-4 (5个测试例子)
- 标注状态: story_state / mod_story_state / mod_story_mod_state
```

### 2. **三个关键任务 (3 PASTA Tasks)**

#### **Task 8: Story-State Inference（故事-状态推理）**
- 目标：从一个5句的故事推理参与者状态
- 输入：故事 → 输出：参与者状态（分类/排序）
- 设置1：基于故事中的关键句子进行推理（突出显示的部分）
- 设置0：基于完整故事进行推理

#### **Task 6: Story Revision from State Change（基于状态变化的故事修改）**
- 目标：给定新的参与者状态，修改故事使其一致
- 输入：原始故事 + 新状态 → 输出：修改后的故事

#### **Task 7: State Change Generation（状态变化生成）**
- 目标：仅基于故事生成可能的状态变化
- 输入：故事 → 输出：状态变化描述

### 3. **数据集规模**

```
├── 训练集 (tr_data.jsonl): 约4000+条样本
├── 验证集 (val_data.jsonl): 约500+条样本  
├── 测试集 (te_data.jsonl): 约500+条样本
├── 人工评估数据 (human_eval_dat.csv): 1000+条评估样本
└── 模型预测结果: 多个来自不同模型的预测文件
    - GPT-3.5/GPT-4 (few-shot prompting)
    - T5-base/T5-large (fine-tuned)
    - BERT/RoBERTa (fine-tuned)
```

### 4. **参与者状态类型**

参与者状态包括多个维度：

| 维度 | 示例 |
|------|------|
| **性格特征** | 聪明、懒惰、好奇、耐心 |
| **情感状态** | 开心、伤心、愤怒、害怕、惊讶 |
| **社交特性** | 友善、自私、慷慨、不礼貌 |
| **行为倾向** | 勤奋、粗心、冒险、谨慎 |
| **身体/物质状态** | 疲惫、健康、富有、饥饿 |
| **知识/能力** | 有才华、无能、有经验 |

### 5. **反事实（Counterfactual）设计**

数据集的创新特点是包含反事实样本：
- **原始状态 (Original State)**: 从故事真实推断出的状态
- **反事实修改 (Counterfactual Modification)**: 
  - 改变故事中的具体事件、行为或结果
  - 使得新的故事支持相反的状态
  - 帮助模型区分关键vs非关键信息

---

## 数据示例

### 示例 1: 基础故事-状态推理

```json
{
  "AssignmentId": "3T111IHZ5FE8GP3HEMJGJXPHBH4R9Y",
  "Input.Title": "Quarters",
  "Input.storyid": "a900401a-a800-4109-8dfb-370f2b7a9a44",
  "Input.line1": "Bill and Ted were best friends.",
  "Input.line2": "They were high school students.",
  "Input.line3": "They would eat lunch together every day.",
  "Input.line4": "They would play with the coins they had in their pockets.",
  "Input.line5": "They played and loved a game called quarters together.",
  
  // 原始状态推理
  "Answer.assertion": "Bill and Ted were older teenagers.",
  "Answer.line1.on": false,
  "Answer.line2.on": true,    // 只有第2句是关键
  "Answer.line3.on": false,
  "Answer.line4.on": false,
  "Answer.line5.on": false,
  
  // 反事实修改
  "Answer.mod_assertion": "Bill and Ted were toddlers.",
  "Answer.mod_line1": "Bill and Ted were best friends.",
  "Answer.mod_line2": "They were kindergarten students.",  // 修改关键句
  "Answer.mod_line3": "They would eat lunch together every day.",
  "Answer.mod_line4": "They would play with the coins they had in their pockets.",
  "Answer.mod_line5": "They played and loved a game called quarters together."
}
```

**分析**: 
- 原始推论依据：高中学生 → 年长的青少年
- 反事实修改：幼儿园学生 → 幼儿
- 最少支持集合：仅第2句（Input.line2.on=true）

---

### 示例 2: 情感/行为状态推理

```json
{
  "Input.Title": "Bug in the plate",
  "Input.line1": "Tina went out to eat yesterday.",
  "Input.line2": "She ordered salmon.",
  "Input.line3": "All the sudden she saw something.",
  "Input.line4": "There was a bug in her plate.",
  "Input.line5": "Tina screamed.",
  
  "Answer.assertion": "Tina is squeamish.",  // 易受惊吓的
  "Answer.line1.on": false,
  "Answer.line2.on": false,
  "Answer.line3.on": false,
  "Answer.line4.on": false,
  "Answer.line5.on": true,  // 尖叫声是关键证据
  
  "Answer.mod_assertion": "Tina is not squeamish.",
  "Answer.mod_line5": "Tina told the waiter calmly."  // 冷静告诉服务员 = 不易受惊
}
```

**分析**:
- 推断维度：心理特性（易受惊吓 vs 不易受惊）
- 关键证据：最后的行为反应（尖叫）
- 反事实验证：改变最后的行为来反转状态

---

### 示例 3: 多维度状态推理

```json
{
  "Input.Title": "Museum Trip",
  "Input.line1": "Samantha was taking an art history class that required a museum trip.",
  "Input.line2": "At the end of the week she had chosen one to go to.",
  "Input.line3": "At first the museum seemed very boring to her.",
  "Input.line4": "But as time went on she began to really enjoy the trip.",
  "Input.line5": "Afterwards she told her professor how much she had enjoyed her trip.",
  
  "Answer.assertion": "Samantha was engaged with the trip.",
  "Answer.line1.on": false,
  "Answer.line2.on": false,
  "Answer.line3.on": false,
  "Answer.line4.on": true,   // 开始享受
  "Answer.line5.on": true,   // 向教授表达享受
  
  "Answer.mod_assertion": "Samantha was bored.",
  "Answer.mod_line4": "But as time went on she began to really want to sleep.",
  "Answer.mod_line5": "Afterwards she told her professor how bored she had been."
}
```

**分析**:
- 多线索支持（最少支持集合有两句）
- 状态进展：无聊 → 享受 → 表达享受
- 反事实需要维持逻辑一致性

---

### 示例 4: 模型评估数据格式

```csv
Input.Input_Title: Moldy Bread
Input.Input_line1: The man ate some bread.
Input.Input_line2: The bread tasted weird.
Input.Input_line3: He looked at the bread.
Input.Input_line4: It was visibly moldy.
Input.Input_line5: He peeled off the mold and continued to eat the remaining bread.
Input.assertion: The man thought a bread with mold was still edible.
Input.story_state_flag: mod_story_mod_state

Answer.ex_sb_entail_a.0-4: [false, false, false, false, false]  // 5个示例反例
Answer.sb_entail_a.0-4: [false, false, false, false, true]      // 5个测试例
```

**评估逻辑**:
- `story_state`: 原始故事支持该状态
- `mod_story_state`: 修改的故事支持原始状态
- `mod_story_mod_state`: 修改的故事支持修改后的状态
- 答案向量编码了5个判断（每个判断对应一个例子）

---


### 数据文件说明

```
human_eval_data/mturk_op/
├── MturkOP_Te_200_t6_GPT3_app_3_exs_10.csv
│   └── GPT-3 Task 6 (few-shot, 3个示例, 10个Prompt版本)
├── MturkOP_Te_200_t7_GPT3_app_1_exs_5.csv
│   └── GPT-3 Task 7 (few-shot, 1个示例, 5个Prompt版本)
├── MturkOP_Te_200_t8.csv
│   └── Task 8评估集 (人工评估分数)
├── MturkOP_Te_full_t_6_m_t5-base_b_12_lr_0.0001_w_1e-06_s_0_epoch_6.csv
│   └── T5-base Task 6 预测结果
├── MturkOP_Te_full_t_7_m_t5-base_b_10_lr_0.0001_w_1e-06_s_0_epoch_6.csv
│   └── T5-base Task 7 预测结果
└── ... (其他模型变体)
```

---

## 关键特点

### ✅ **优势**

1. **创新的反事实设计**
   - 包含对比学习的基础
   - 帮助模型区分因果关系和相关性

2. **多层次的复杂性**
   - 从简单状态推理到复杂故事生成
   - 从单一证据到多源融合

3. **相对容易的语言**
   - 故事简短（5句）
   - 避免复杂的叙事技巧

4. **全面的模型覆盖**
   - BERT/T5/GPT等多种架构
   - 从微调到少样本学习

5. **严格的人工评估**
   - Mechanical Turk众包标注
   - 多评估者一致性检查

### 📊 **数据分布特征**

1. **故事主题多样**：生活、情感、教育、冒险、失败、成功等

2. **状态空间丰富**：
   - 个性特征：聪明、懒惰、幸运、粗心
   - 情感状态：开心、伤心、愤怒、惊讶
   - 社交特性：友善、自私、无礼、热心

3. **证据复杂性**：
   - 简单：单一句子决定
   - 复杂：多个句子共同支持
   - 矛盾：需要推理才能解决

---

## 总结

PASTA是一个高质量的参与者状态推理数据集，具有以下特点：

| 特性 | 详情 |
|------|------|
| **规模** | ~5000个训练样本，~1000个测试样本 |
| **任务数** | 3个主要任务（推理、修改、生成） |
| **模态** | 纯文本，5句故事格式 |
| **标注质量** | 众包标注，多评估者，反事实验证 |
| **适用模型** | BERT/RoBERTa/T5/GPT-3/Llama等 |
| **主要应用** | 故事理解、常识推理、文本生成 |

该数据集对研究自然语言理解中的因果推理、隐含信息提取和反事实学习具有重要意义。

**PASTA (Participant State Tracking in Narratives)** 是一个极具特色的数据集。它不仅完美契合你要求的 **T2（状态更新）**，更是你构建 **T5（反事实/防数据污染）** 的“现成宝库”。

PASTA 的核心魅力在于它自带了**“原版故事”与“微调反转故事（Counterfactual）”的成对数据**。

---

### 1. 任务匹配度分析

| 任务 | 匹配度 | 理由 |
| :--- | :--- | :--- |
| **T1: 时间计算** | 低 | 故事主要是逻辑推进，缺乏具体的时间数值。 |
| **T2: 状态更新** | **极高** | 专门用于追踪人物随事件发展而产生的**心理、生理、身份状态**变化。 |
| **T3: 并发冲突** | 低 | 文本为单线叙事，极少涉及多线程的资源/时间冲突。 |
| **T4: 长期记忆** | 低 | 文本只有 5 句话，不足以测试长上下文检索。 |
| **T5: 反事实** | **极高 (完美匹配)** | 数据集原生自带修改关键条件以反转结局的 `mod_` 字段，专门用于打破模型的预训练偏见。 |

---

### 2. 针对各 Task 的数据修改方案

#### **T2：状态更新 (Status Update - 心理/身份状态推理)**
PASTA 可以补充 OpenPI（偏物理状态）的不足，提供**心理状态和社会属性**的追踪。
* **利用字段：** `Input.line1` 到 `Input.line5` (作为上下文) + `Answer.assertion` (作为目标答案)。
* **修改逻辑：** 将 5 句话拼接成 Context，并针对角色的隐含状态提问。
* **数据示例：**
    * **[Context]**：Bill 和 Ted 是最好的朋友。他们是高中生。他们每天一起吃午饭，还喜欢一起玩硬币游戏。
    * **[Question]**：根据当前情况，Bill 和 Ted 处于什么年龄阶段？
    * **👉 测：** 模型能否从“高中生”这个过程状态，推理出“年长的青少年 (older teenagers)”这个最终属性状态。

#### **T5：反事实与防数据污染 (Counterfactual - 绝佳用例)**
由于 PASTA 基于广泛用于大模型预训练的 ROCStories，模型极有可能“背下”了原版故事。你可以利用 PASTA 的反事实对，来测试模型是“在背书”还是“在看当前 Context 推理”。
* **利用字段：** `Answer.mod_line1` 到 `Answer.mod_line5` (修改后的上下文) + `Answer.mod_assertion` (反转后的答案)。
* **修改逻辑：** 故意使用修改了关键句（如示例中的高改变成幼儿园）的 `mod_` 故事作为输入，观察模型是否会被预训练记忆（高中生）带偏。
* **数据示例：**
    * **[Context]**：在这个情境中，Bill 和 Ted 是最好的朋友。**他们是幼儿园学生。** 他们每天一起吃午饭，还喜欢玩硬币游戏。
    * **[Question]**：Bill 和 Ted 处于什么年龄阶段？
    * **👉 测：** 这是一个典型的反事实测试。如果模型输出“青少年（原版答案）”，说明它受到了训练数据污染的干扰；如果输出“幼儿 (toddlers)”，说明它真正在遵守你给定的新 Context 规则。

---

### 3. 数据处理建议

1.  **构造“对比测试对”（Contrastive Pairs）：**
    对于 T5 任务，强烈建议你把原版故事（Original）和修改版故事（Modified）成对放入 Benchmark。只有当 LLM 在原版故事回答正确，**并且**在修改版故事中也跟随 Context 发生了答案反转，才能算作该题真正得分。
2.  **利用 `Answer.lineX.on` 制造干扰：**
    PASTA 标注了哪一句话是推断状态的“关键句”（如示例中的 line2）。在构建 T2 任务时，你可以尝试把这句“关键句”移动到 Context 的最开头或最末尾，测试模型对关键状态信息的捕捉是否受位置影响。
3.  **状态类型分类：**
    提取数据时，可以根据 PASTA 的维度进一步细分。例如，将“情绪变化（开心到伤心）”和“身份认知（高中生到幼儿）”分开评测，这能让你的 Benchmark 报告更细致。

---

### 总结与定位

PASTA 的加入，补齐了你 Benchmark 中 **T5（反事实）** 的关键一环，并且让 **T2（状态追踪）** 从纯物理范畴（OpenPI）扩展到了人物心理与社会身份范畴。

**你想让我写一段 Python 代码，展示如何同时提取 PASTA 中的“原版故事”和“反事实故事”，并自动组装成一对 T5 的正反面对比测试用例吗？**
