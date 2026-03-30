# 一、总体实验框架（先统一范式）

所有实验统一遵循：

---

## 🆕 核心创新：对话式时序评测（Conversational Temporal Evaluation）

### 动机

> 现有数据集均为**静态单次问答**形式，信息一次性呈现，偏离真实LLM使用场景。
> 真实场景中，用户与LLM进行**多轮对话**，信息逐步揭示，状态持续演进。

### 创新点

| 维度 | 传统数据集 | 对话式评测（本文） |
|------|-----------|------------------|
| 信息呈现 | 一次性全部给出 | 多轮对话逐步揭示 |
| 状态依赖 | 无上下文依赖 | 状态随对话演进 |
| 干扰模式 | 无干扰信息 | 对话历史中的冗余/干扰 |
| 一致性 | 单点验证 | 跨轮次一致性追踪 |
| 真实性 | 脱离实际使用 | 对齐真实交互场景 |

### 评测架构升级

```
┌─────────────────────────────────────────────────────────┐
│                    每个Task = 双轨评测                    │
├─────────────────────────────────────────────────────────┤
│  Track A: 静态评测（Baseline）                           │
│  └─ 传统单次问答，信息一次性呈现                           │
│                                                         │
│  Track B: 对话式评测（创新）                              │
│  └─ 多轮对话，信息逐步揭示，测试上下文状态追踪能力            │
└─────────────────────────────────────────────────────────┘
```

### 核心假设

> **Gap Hypothesis**: 对话式评测下，LLM的时序推理能力会**显著下降**，
> 因为模型需要在对话历史中维护状态、处理干扰、保持一致性。

---

## 评测范式（统一）

### 范式A：静态评测（Baseline）

输入形式：

```
[Context / 对话历史]
[时间推进 Δt]
[事件 a_t]
[问题 Query]
```

---

### 范式B：对话式评测（创新）

输入形式（多轮）：

```
Round 1: [对话历史空] + [问题1]
Round 2: [模型回答1] + [新事件] + [问题2]
...
Round N: [完整对话历史] + [关键问题]
```

**关键设计**：
1. **信息渐进** - 关键信息分散在不同轮次
2. **干扰注入** - 对话中插入无关对话
3. **状态演进** - 实体状态随对话变化
4. **矛盾探测** - 在对话中埋入矛盾信息

---

### 输出要求（强约束）

模型必须输出：

```json
{
  "answer": "...",
  "state": {...},   ← 可选（用于分析）
  "reasoning": "..." ← 可选（用于 consistency）
}
```

---

### 自动评测模块（3层）

1. **Answer-level**
2. **State-level（关键）**
3. **Chain-level（Consistency）**




现在的实验应该分为两层：

---

## 🔵 Level 1：Task-based Evaluation（主线）

| Task    | 实验编号  |
| ------- | ----- |
| T1 时间计算 | Exp-1 |
| T2 状态更新 | Exp-2 |
| T3 并发冲突 | Exp-3 |
| T4 长期记忆 | Exp-4 |
| T5 反事实  | Exp-5 |

**🆕 每个Task均包含双轨评测：**
- 📌 **Track A**: 静态评测（Baseline）
- 🆕 **Track B**: 对话式评测（创新）

---

## 🟠 Level 2：Cross-cutting Analysis（横向分析）

* Steps scaling
* Context length
* Consistency
* Error propagation
* **🆕 对话式 vs 静态评测对比**

👉 这些是“分析维度”，不是 task

---

# 二、五大Task的完整实验设计

---

# 🧪 Exp-1：T1 时间计算（Temporal Calculation）

---

## 🎯 测什么

最基础能力：

> 是否能正确处理时间运算（duration / offset / ordering）

---

## 🧪 数据设计

三类子任务：

### T1-1 Duration

```text
会议8:00开始，持续1小时20分钟，什么时候结束？
```

### T1-2 Temporal Offset

```text
如果现在是周三，3天后是？
```

### T1-3 Ordering

```text
A发生在B之前，B发生在C之后，谁最早？
```

---

## ⚙️ 难度控制

| 变量   | 设置        |
| ---- | --------- |
| 步数   | 1 / 2 / 3 |
| 单位混合 | 分钟/小时/天   |
| 嵌套   | 有/无       |

---

## 📊 指标

* Accuracy（必须接近上限）
* Step Accuracy（用于debug）

---

## 🆕 对话式评测（Track B）

### 数据设计

信息分散在不同轮次：

```text
User: 明天我要开个会，准备安排8:00开始。
LLM:  好的，已记录。

User: 对了，会议需要持续1小时20分钟。
LLM:  明白了，预计9:20结束。

User: 如果会议中间休息15分钟呢？
LLM:  那么结束时间会推迟到9:35。

User: 那实际上会议开多久？
LLM:  [需要从历史中提取信息]
```

### 核心测试点

| 测试项 | 说明 |
|-----|------|
| 信息提取 | 能否从历史中正确聚合分散的时间信息 |
| 干扰过滤 | 能否忽略对话中的无关内容 |
| 状态更新 | 能否在上下文中更新计算结果 |

### 预期发现

> 即使是简单的时间计算，在对话中也会出现信息遗漏、状态混乱

---

## 📈 预期结论

👉 这个实验的作用不是证明难，而是：

> ✔ 模型在基础时间计算上表现很好（作为对照组）

---

# 🧪 Exp-2：T2 状态更新（State Tracking）

---

## 🎯 测什么（核心能力）

> 模型是否能随着时间正确更新世界状态

---

## 🧪 数据构造

多步事件：

```text
8:00 张三在家  
8:30 出门 → 公司  
9:00 开会  

问：9:00 张三在哪？
```

---

## ⚙️ 关键变量

| 变量      | 设置                |
| ------- | ----------------- |
| Steps   | 3 / 5 / 10        |
| Entity数 | 1 / 3             |
| 状态维度    | location / status |

---

## 📊 指标（重点）

### 1. Final Accuracy

### 2. State Accuracy（🔥）

逐字段评估：

| 字段       | Acc |
| -------- | --- |
| location |     |
| status   |     |

---

### 3. Consistency（🔥）

前后状态是否冲突

---

## 🆕 对话式评测（Track B）

### 数据设计

状态在对话中逐步演变：

```text
User: 张三今天早上在家。
LLM:  好的，已记录张三8:00在家。

User: 他8:30出门去公司了。
LLM:  明白了，张三现在在去公司的路上。

User: [插入无关对话：天气如何？午餐推荐？]
LLM:  [回答无关问题]

User: 他9:00到公司后直接开会了。
LLM:  已更新，张三9:00在公司开会。

User: [又插入无关对话]
LLM:  [回答]

User: 刚才张三到公司后做了什么？
LLM:  [需要从历史中追踪状态]
```

### 核心测试点

| 测试项 | 说明 |
|-----|------|
| 状态追踪 | 能否在干扰中保持状态演绎 |
| 信息提取 | 能否从历史回溯关键事件 |
| 状态回滚 | 能否回答中间状态问题 |
| 干扰免疫 | 能否过滤无关对话 |

### 预期发现

> **关键假设**：对话中的干扰信息会显著降低状态追踪准确率
> 
> 模型在动态对话中的状态 drift 会比静态评测更严重

---

## 📈 预期发现

* 短链 OK
* 长链 drift

👉 得出：

> ❗模型没有稳定的 state tracking 能力

---

# 🧪 Exp-3：T3 并发冲突（Concurrency）

---

## 🎯 测什么

> 模型是否理解现实世界约束（不能同时做两件冲突的事）

---

## 🧪 子任务拆分（非常关键）

---

### T3-1 空间冲突

```text
9:00 张三在A  
9:00 张三在B  
是否合理？
```

---

### T3-2 资源冲突

```text
会议室A已被占用  
李四还能用吗？
```

---

### T3-3 注意力冲突

```text
9:00 开会  
9:00 写复杂代码  
```

---

## ⚙️ 难度设计

| Level | 描述   |
| ----- | ---- |
| Easy  | 显式冲突 |
| Hard  | 隐含冲突 |

---

## 📊 指标

| 指标                      | 说明     |
| ----------------------- | ------ |
| Conflict Detection Rate | 能否识别冲突 |
| Resolution Accuracy     | 能否合理解决 |

---

## 🆕 对话式评测（Track B）

### 数据设计

冲突信息分散在不同轮次：

```text
User: 张三明天9:00到11:00要开会。
LLM:  已记录，张三9:00-11:00开会。

User: 对了，他9:00还要去见客户。
LLM:  [应该识别冲突] 这和时间有冲突...

User: 那会议室A呢？
LLM:  [继续对话...]

User: 帮我确认一下张三明天的安排。
LLM:  [需要识别之前埋设的冲突]

User: 等等，会议改到10:00了。
LLM:  [状态更新后的冲突检测]

User: 那还有什么冲突吗？
LLM:  [重新评估冲突状态]
```

### 核心测试点

| 测试项 | 说明 |
|-----|------|
| 冲突记忆 | 能否在后续轮次记住冲突 |
| 延迟识别 | 能否在问询时才指出冲突 |
| 动态冲突 | 状态更新后重新检测冲突 |
| 冲突解释 | 能否主动解释冲突原因 |

### 特殊设计：隐藏冲突

```text
Round 1-5: 铺垫行程A
Round 6-10: 铺垫行程B（与A冲突）
Round 11: 直接问"有什么问题？"
```

> 测试模型是否会**主动**发现并报告冲突

### 预期发现

> 对话中的冲突更容易被忽略，因为信息分散在时间轴上
> 
> 静态评测：冲突信息一次性呈现，更容易识别
> 对话评测：冲突分散在多轮，需要跨轮次记忆和推理

---

## 📈 核心结论

👉 非常重要：

> LLM往往**忽略冲突，而不是解决冲突**

---

# 🧪 Exp-4：T4 长期记忆（Long-Horizon Memory）

---

## 🎯 测什么

> 模型是否能在长上下文中维持时间信息

---

## 🧪 数据设计

结构：

```text
[事件发生在很早]
...（大量无关对话）...
[问题]
```

---

## ⚙️ 变量

| 变量             | 设置            |
| -------------- | ------------- |
| Context length | 2k / 8k / 32k |
| 时间跨度           | 短 / 长         |
| 噪声比例           | 0% / 80%      |

---

## 📊 指标

### 1. Retrieval Accuracy

是否找到关键信息

### 2. Final Accuracy

### 3. Memory Consistency

---

## 📈 分析重点

区分三种失败：

| 类型    | 含义            |
| ----- | ------------- |
| 找不到   | retrieval问题   |
| 找到了但错 | reasoning问题   |
| 前后不一致 | consistency问题 |

---

## 🆕 对话式评测（Track B）

### 数据设计

关键信息分散在长对话中：

```text
[Round 1-5] 普通闲聊（铺垫初始事件）
User: 对了，上周二我们定了那个重要会议。
LLM:  好的，已记录。会议详细信息是？

User: 会议时间是3月15号下午2点，地点A会议室。
LLM:  明白了，3/15下午2点，A会议室。

[Round 6-50] 大量无关对话（插入噪声）
User: 今天天气不错...
User: 对了那个项目怎么做的？
User: 午餐推荐一下？
...
LLM:  [各种回答]

[Round 51] 关键问题
User: 之前说的会议是什么时候？
LLM:  [需要从历史中检索]
```

### 核心测试点

| 测试项 | 说明 |
|-----|------|
| 远距离检索 | 能否从早期轮次提取信息 |
| 噪声过滤 | 能否忽略中间50轮无关对话 |
| 时间精确度 | 能否记住具体时间而非模糊描述 |
| 对比推理 | 能否回答"是哪个月？""周几？" |

### 变量设计

| 对话长度 | 信息位置 | 检索难度 |
|------|------|------|
| 20轮 | 开头5% | 简单 |
| 50轮 | 开头10% | 中等 |
| 100轮 | 中间50% | 困难 |
| 200轮 | 开头5% | 极难 |

### 预期发现

> 对话式记忆比静态上下文更难
> 
> - 静态：信息聚在一起，可反复阅读
> - 对话：信息分散，中间有大量干扰

---

## 🎯 关键结论

> ❗Long context ≠ Long-term reasoning

---

# 🧪 Exp-5：T5 反事实（Counterfactual / Sandbox）

---

## 🎯 测什么

> 模型是否依赖训练数据 vs 真正推理

---

## 🧪 数据构造

改变规则：

```text
这个世界：
水在50°C沸腾  
煮熟需要30分钟  

问：煮10分钟熟了吗？
```

---

## ⚙️ 对照组

| Setting | 描述   |
| ------- | ---- |
| Normal  | 现实规则 |
| Sandbox | 虚构规则 |

---

## 📊 指标

* Accuracy drop
* Consistency drop

---

## 🆕 对话式评测（Track B）

### 数据设计

虚构规则在对话中逐步建立：

```text
User: 我们来玩个游戏，这个世界有些不同规则。
LLM:  好的，请告诉我这个世界的规则。

User: 首先，水在这个世界50°C就沸腾了。
LLM:  明白了，水50°C沸腾（而非100°C）。

User: 其次，食物煮熟需要30分钟。
LLM:  记住了，煮熟需30分钟。

User: 对了，重力的方向是向上的。
LLM:  已记录，重力向上。

[Round 5-15] 测试问题
User: 我把水加热到60°C，会怎样？
LLM:  [应用虚构规则]

User: 那如果我煮鸡蛋10分钟呢？
LLM:  [应用虚构规则]

User: 等等，现实世界中水100°C沸腾对吧？
LLM:  [测试是否会混淆]

User: 在这个虚构世界中呢？
LLM:  [必须坚持虚构规则]
```

### 核心测试点

| 测试项 | 说明 |
|-----|------|
| 规则记忆 | 能否记住对话中建立的虚构规则 |
| 规则应用 | 能否正确应用虚构规则推理 |
| 上下文隔离 | 能否区分"现实"和"虚构"对话 |
| 规则组合 | 能否组合多条虚构规则推理 |

### 特殊挑战：规则冲突

```text
Round 1-5: 建立规则A（虚构世界）
Round 6-10: 自然对话（穿插现实世界常识）
Round 11: 应用规则A

问题：模型是否会因现实常识干扰而违背虚构规则？
```

### 预期发现

> **关键假设**：对话中的规则混淆会更严重
> 
> - 静态：规则与问题在同一上下文，边界清晰
> - 对话：规则在历史中，与当前轮次有距离，易被现实常识覆盖

### 对比设计

| 设置 | 静态评测 | 对话评测 |
|-----|---------|---------|
| 规则呈现 | 一次性声明 | 分散在多轮 |
| 干扰程度 | 低（无对话干扰） | 高（中间有其他话题） |
| 规则冲突 | 少（边界清晰） | 多（现实常识混入） |

---

## 📈 核心结论（杀手级）

> ❗模型在未知规则下显著退化 → 说明依赖记忆而非推理

---

# 三、统一大表（论文必备）

---

## 📊 Table：Task × Model 总览

| Model  | T1 | T2 | T3 | T4 | T5 | Overall |
| ------ | -- | -- | -- | -- | -- | ------- |
| GPT-4o | -- | -- | -- | -- | -- | ------- |
| Claude | -- | -- | -- | -- | -- | ------- |
| LLaMA  | -- | -- | -- | -- | -- | ------- |

---

## 🎯 这个表的意义

👉 一眼看出：

* T1 很高（baseline）
* T2/T3/T5 明显掉

---

# 四、Task + Scaling 结合（高级分析）

---

你可以再加一个**二维分析表**：

## 📊 Table：Task × Steps

| Task | Steps=2 | Steps=5 | Steps=10 |
| ---- | ------- | ------- | -------- |
| T2   | ------- | ------- | -------- |
| T3   | ------- | ------- | -------- |

👉 得出：

> Temporal reasoning 随深度崩溃

---

# 五、Reviewer会非常喜欢的点（你现在补上了）

你现在的实验体系具备：

✅ taxonomy → task
✅ task → experiment
✅ experiment → metric
✅ metric → insight

这就是：

> **完整 scientific loop**

---

# 六、对话式评测创新点（重要）

---

## 🆕 核心创新：从静态到动态评测

### 为什么这是创新？

| 现有工作 | 本文创新 |
|---------|---------|
| 单次问答，信息一次性呈现 | 多轮对话，信息逐步揭示 |
| 无上下文依赖 | 状态随上下文演化 |
| 无干扰信息 | 包含冗余和噪声 |
| 单点准确率 | 跨轮次一致性追踪 |
| 脱离真实使用场景 | 对齐实际交互模式 |

### 研究问题（Research Questions）

**RQ1**: 对话式评测下的时序推理能力是否显著低于静态评测？
- 假设：Gap = Accuracy(Static) - Accuracy(Conversational) > 0

**RQ2**: 哪些时序推理能力在对话中退化最严重？
- 假设：State Tracking 和 Conflict Detection 退化最严重

**RQ3**: 干扰信息的类型如何影响性能？
- 假设：无关对话 > 时间混淆 > 状态冲突

**RQ4**: 对话长度如何影响时序推理？
- 假设：线性退化，Long-Horizon 最敏感

---

## 📊 对话式评测核心设计框架

### 信息揭示模式

```
┌─────────────────────────────────────────────────────────────┐
│                    信息揭示模式                              │
├─────────────────────────────────────────────────────────────┤
│  Progressive: 关键信息分散在不同轮次                          │
│  Interleaved: 信息与干扰对话交错出现                          │
│  Contradiction: 后续轮次覆盖/否定前序信息                      │
│  Query-Buried: 关键问题埋藏在对话深处                         │
└─────────────────────────────────────────────────────────────┘
```

### 测试维度

| 维度 | 静态评测 | 对话评测 | 测量指标 |
|------|---------|---------|---------|
| 信息提取 | 单次读取 | 多轮聚合 | Extraction Gap |
| 干扰免疫 | 无干扰 | 中间有噪声 | Noise Gap |
| 状态追踪 | 显式状态 | 隐式演化 | Drift Gap |
| 一致性 | 单点验证 | 跨轮次检查 | Consistency Gap |
| 冲突检测 | 同时呈现 | 分散揭示 | Detection Delay |

---

## 🎯 预期核心发现

### 主要发现（Main Findings）

1. **对话式评测性能显著低于静态评测**
   - 平均 Gap > 15-20%

2. **State Tracking 和 Conflict Detection 退化最严重**
   - 退化程序：T3 > T2 > T4 > T5 > T1

3. **干扰信息显著降低推理准确性**
   - 无干扰 vs 有干扰，Gap > 10%

4. **对话长度与性能呈负相关**
   - Long-Horizon Memory 最敏感

### 次要发现（Secondary Findings）

5. **模型倾向于"遗忘"早期对话中的时间约束**
6. **冲突检测在对话中更容易失败（信息分散）**
7. **反事实规则在对话中更易被现实常识覆盖**

---

## 📈 论文贡献点

### 方法学贡献

✅ **首个对话式时序推理评测框架**
- 从静态到动态的范式转换
- 对齐真实LLM使用场景

✅ **系统的 Gap 分析**
- 量化对话式评测相比静态评测的性能下降
- 揭示LLM在真实交互场景中的弱点

✅ **创新的测试设计**
- 信息渐进揭示
- 干扰注入机制
- 跨轮次一致性验证

### 实证贡献

✅ **五个维度的全面分析**
- T1-T5 五个Task的对话式评测设计
- 每个Task的核心测试点分析

✅ **系统性发现**
- 哪些能力退化最严重
- 哪些干扰最有效
- 哪些任务最敏感

---

## 🔬 实验设计补充

### 对照实验

| 实验组 | 形式 |
|-------|------|
| Baseline | 静态单次问答 |
| Track B | 多轮对话（无干扰） |
| Track B+ | 多轮对话（有干扰） |
| Track B++ | 多轮对话（有矛盾） |

### 分析维度

1. **Performance Gap**: Static vs Conversational 每个Task的准确率差异
2. **Noise Effect**: 干扰信息对性能的影响
3. **Length Effect**: 对话长度与性能关系
4. **Consistency Decay**: 一致性随对话轮次的退化

---

## 🎓 论文写作建议

### 标题建议

> **Conversational Temporal Reasoning: A New Benchmark Beyond Static Evaluation**
> 对话式时序推理：超越静态评测的新基准

### 创新点表述

1. **首个**系统将对话式评测引入时序推理评测
2. **首次**量化静态与对话评测的性能差距
3. **新颖**的信息渐进揭示测试框架

### Contribution Statement 模板

> We introduce the first conversational evaluation framework for temporal reasoning, 
> revealing significant performance gaps between static and conversational settings. 
> Our systematic analysis across five core temporal reasoning tasks demonstrates that 
> LLMs struggle to maintain state, detect conflicts, and apply rules across 
> multi-turn conversations—limitations that static evaluations fail to capture.

---

**这使你的工作成为领域首创！** 🚀

---

# 七、数据集转换方案

---

## ATOMIC 数据集转换

### 数据集概述

**ATOMIC (Atlas of Machine Commonsense)** 是一个社会常识知识图谱，包含丰富的"If-Then"关系：

| 字段 | 说明 | 时间维度 |
|------|------|---------|
| `xNeed` | 前置条件 | Before |
| `event` | 核心事件 | During |
| `xEffect` | 物理后果 | After |
| `xWant` | 后续意图 | After |
| `oReact` | 他人反应 | After |
| `xAttr` | 性格属性 | Implication |

### 任务匹配度

| 任务 | 匹配度 | 利用字段 |
|------|-------|---------|
| **T2: 状态更新** | ⭐⭐⭐ 高 | `xNeed` → `event` → `xEffect` |
| **T3: 冲突检测** | ⭐⭐ 中 | `xAttr`, `xNeed`, 属性冲突 |
| **T5: 反事实** | ⭐⭐⭐ 极高 | `oReact`, 颠覆常识因果 |

### 转换方案

#### T2: 状态更新 (State Tracking)

**核心逻辑**: 利用 `xNeed → event → xEffect` 时间链

```python
# 静态评测 (Track A)
Context: "前提：【xNeed】\n事件：【event】"
Query: "当前状态是什么？"
Answer: 【xEffect】

# 对话式评测 (Track B)
Round 1: User: "我正在【xNeed】。"
Round 2: User: "对，我在【event】。"
Round 3: [插入无关对话]
Round 4: User: "做完之后我会处于什么状态？"
```

**子任务**:
- `T2-1`: 状态推断（根据事件推断当前状态）
- `T2-2`: 状态转换序列（多步推断）
- `T2-3`: 愿望驱动（从xWant推断目的）
- `T2-Conv-1`: 信息渐进揭示
- `T2-Conv-2`: 干扰信息过滤
- `T2-Conv-3`: 状态回滚

#### T3: 冲突检测 (Conflict Detection)

**核心逻辑**: 利用属性冲突和意图冲突

```python
# 显式冲突
Event A: "去图书馆" (需要安静)
Event B: "开派对" (喧闹)
Query: "这两个事件能否同时发生？"

# 对话式隐藏冲突
Round 1: "我明天要去图书馆，需要安静的环境"
Round 2: "对了，我还在同一时间安排了派对"
Round 3: "你觉得这个安排有问题吗？"
```

**子任务**:
- `T3-1`: 属性推断（从事件推断属性）
- `T3-2`: 冲突识别（识别属性冲突）
- `T3-3`: 事件对冲突（显式冲突检测）
- `T3-Conv`: 对话中隐藏冲突

#### T5: 反事实推理 (Counterfactual)

**核心逻辑**: 颠覆 `oReact` 常识反应

```python
# 正常情况 (对照组)
Event: "PersonX做了某事"
Query: "其他人会有什么反应？"
Answer: 【oReact (原样)】

# 反事实情况 (实验组)
Context: "【反事实规则】在这个世界里，人们对于被偷窃感到自豪。"
Event: "PersonX偷了PersonY的钱包。"
Query: "PersonY现在心情如何？"
Answer: 【反转的反应 (自豪/高兴而非生气)】
```

**对话式反事实**:
```python
Round 1: User: "我们来玩一个虚构世界的游戏。"
Round 2: User: "在这个世界里，【反事实规则】。"
Round 3: User: "顺便说，现实世界里【原样】..."
Round 4: User: "那在虚构世界里，【事件】，人们会怎样？"
# 测试模型是否会混淆现实与虚构规则
```

### 输出格式

```json
{
  "task": "T2",
  "sub_task": "T2-Conv-1",
  "track": "B",
  "context": "[多轮对话模式]",
  "delta_t": "对话过程中",
  "event": "某人sets the alarm",
  "query": "对话历史中提到了什么？",
  "answer": "将会准时醒来",
  "state": {
    "type": "conversational_state_tracking",
    "information_progression": ["准备", "进行", "完成"]
  },
  "conversation": [
    {"role": "user", "content": "我正在准备起床。"},
    {"role": "assistant", "content": "好的。"},
    ...
  ],
  "ground_truth_state": {
    "extracted_info": {
      "prerequisite": "to have a clock",
      "event": "sets the alarm",
      "effect": "wakes up on time"
    }
  },
  "difficulty": "hard"
}
```

### 统计数据（最新）

| 维度 | 数量 |
|------|------|
| 原始数据 | 24,312 |
| 严格过滤后 | 6,976 (28.7%) |
| **总样本数** | **24,492** |
| T2 状态更新 | 20,928 |
| T3 冲突检测 | 800 |
| T5 反事实 | 2,764 |

**难度分布**:
- medium: 7,276
- hard: 15,452
- very_hard: 1,764

### 过滤条件

**严格过滤**：所有关键字段都必须有有效值

```python
# 过滤字段（9个）
KEY_FIELDS = ['oEffect', 'oReact', 'oWant', 'xAttr', 'xEffect', 
              'xIntent', 'xNeed', 'xReact', 'xWant']

# 过滤条件
1. event 不为空
2. 所有关键字段至少有一个非"none"的有效值
3. 仅保留完整链条的数据
```

### 关键创新点

1. **If-Then 时间链**: 首次将ATOMIC的因果关系转化为时间序列评测
2. **仅对话式数据**: 专注于对话式评测，更贴近实际LLM使用场景
3. **反事实构造**: 系统性颠覆常识反应（如：happy → sad），测试规则跟随能力
4. **对话噪声注入**: 在对话中插入无关信息（天气、宠物），测试抗干扰能力
5. **状态回滚**: 测试模型能否记住对话中早期状态

---

## 数据处理流程

```
ATOMIC CSV (v4_atomic_all_agg.csv)
    │
    ▼
┌──────────────────────┐
│  Strict Quality Filter│ 
│  9关键字段全有有效值  │
│  24,312 → 6,976      │
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│  Task Assignment     │
│  T2: xNeed→xEffect  │
│  T3: 属性冲突/事件对 │
│  T5: oReact反转     │
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│  Conversational Gen  │
│  仅生成对话式数据    │
│  (Track B Only)      │
└──────────────────────┘
    │
    ▼
   JSONL Output
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `atomic_conversational_converter.py` | ATOMIC对话式转换程序 |
| `converted_data_v2/atomic_conversational.jsonl` | 转换后数据（24,492条） |
| `converted_data_v2/atomic_conversational_report.json` | 统计报告 |

---

**注**: 其他数据集的时间计算任务(T1)和时间冲突任务(T3)需要额外设计。

---

## CosmosQA 数据集转换

### 数据集概述

**CosmosQA** 是基于个人博客的叙事性问答数据集，核心特点：

| 特点 | 说明 |
|------|------|
| 叙事性 | 博客文本充满主观感受 |
| 模糊时间 | 缺乏严谨的数字对齐 |
| 隐含习惯 | 自然语言时态标记 |
| 长上下文 | 适合测试长期记忆 |

### 字段结构

| 字段 | 说明 |
|------|------|
| `context` | 叙事性上下文（博客段落）|
| `question` | 问题 |
| `answer0-3` | 四个选项 |
| `label` | 正确答案索引 |

### 任务匹配度

| 任务 | 匹配度 | 理由 |
|------|-------|------|
| **T1: 时间计算** | 低 | 博客缺乏严谨数字，不建议 |
| **T2: 状态更新** | 中 | 从过去时态推断当前状态 |
| **T3: 并发冲突** | 低 | 叙事逻辑发散，难构造冲突 |
| **T4: 长期记忆** | **极高** | 博客上下文长，适合埋藏时间钩子 |
| **T5: 反事实** | **极高** | 反转情感-行为关系 |

### 转换方案

#### T2: 状态更新（时态推断）

```python
# T2-Convo-Tense: 从时态推断状态
User: "I saw both of these bands Wednesday night."
User: "Good Old War is acoustic and makes me smile."
User: "Anyway, what's the weather today?"  # 干扰
Query: "I mentioned 'saw', 'played'. Is this something that already happened?"
Answer: "Already happened (past tense verbs: saw, played)"

# T2-Convo-Timeline: 时间线状态
User: "Let me tell you what happened Wednesday night."
User: [叙事内容]
Query: "At the time 'Wednesday night', what was I doing?"
```

#### T4: 长期记忆（叙事埋藏）

```python
# T4-Convo-Buried: 埋藏时间钩子
User: "Last week I had something planned."  # 时间钩子在开头
User: [大量叙事背景...]  # 6-8轮叙事
User: "I also watched a movie recently."  # 干扰
Query: "What important event did I mention earlier?"
Answer: "I had something planned"

# T4-Convo-Noisy: 噪声叙事中的信息提取
User: [叙事内容]
User: "By the way, what's your favorite color?"  # 噪声
User: [更多叙事]
Query: [原始CosmosQA问题]
```

#### T5: 反事实（情感-行为反转）

```python
# T5-Convo-Emotion: 情感反转
User: "I saw the band and they made me happy."
User: "I really enjoyed this experience."
Assistant: "Normal reaction: happy → enjoyed."
User: "But in THIS world: happy means OPPOSITE (sad)."
Query: "How should I interpret my feeling in this world?"
Answer: "You are feeling sad (not happy)"

# T5-Convo-Rule: 反事实规则
User: "In this hypothetical world:"
User: "If something makes you happy → avoid it."
User: "If something makes you sad → seek more of it."
Query: "In this world, what behavior should I choose?"
Answer: "Follow reversed emotional rules"
```

### 数据处理技巧

1. **时态锚点化**: 利用 `saw`, `played`, `went`, `did` 等过去时动词
2. **时间标记提取**: `Wednesday night`, `last week`, `yesterday` 等时间词
3. **情感检测**: `happy`, `sad`, `angry`, `surprised`, `blown away` 等
4. **第一人称转化**: `This person` → `I`，增强对话感

### 统计数据

| 维度 | 数量 |
|------|------|
| 原始样本（使用） | 5,000 |
| **转换后样本** | **15,001** |
| T2 状态更新 | 3,461 |
| T4 长期记忆 | 7,134 |
| T5 反事实 | 4,406 |

**子任务分布**:
- T2-Convo-Tense: 2,931（时态推断）
- T2-Convo-Timeline: 530（时间线状态）
- T4-Convo-Buried: 3,567（埋藏时间）
- T4-Convo-Noisy: 3,567（噪声提取）
- T5-Convo-Emotion: 839（情感反转）
- T5-Convo-Rule: 3,567（规则改变）

**难度分布**:
- medium: 2,931
- hard: 4,936
- very_hard: 7,134

### 文件说明

| 文件 | 说明 |
|------|------|
| `cosmosqa_conversational_converter.py` | CosmosQA转换程序 |
| `converted_data_v3/cosmosqa_conversational.jsonl` | 转换后数据（15,001条） |
| `converted_data_v3/cosmosqa_conversational_report.json` | 统计报告 |

---

## DROP 数据集转换

### 数据集概述

**DROP (Discrete Reasoning Over Paragraphs)** 是数值推理数据集，核心特点：

| 特点 | 说明 |
|------|------|
| 数值推理 | 加减法、排序、计数 |
| 体育比赛 | 橄榄球赛事描述，精确得分时间 |
| 跨句引用 | 需要理解上下文进行推理 |
| 计分明晰 | Field goal=3分，Touchdown=6分 |

### 字段结构

| 字段 | 说明 |
|------|------|
| `section_id` | 章节ID（如nfl_2201） |
| `passage` | 叙事性段落（比赛描述） |
| `question` | 问题 |
| `answers_spans` | 答案（spans + types） |

### 任务匹配度

| 任务 | 匹配度 | 理由 |
|------|-------|------|
| **T1: 时间计算** | ⭐⭐⭐ 极高 | 数值加减天然适合时间计算 |
| **T2: 状态更新** | ⭐⭐ 中 | 侧重结果而非状态变化 |
| **T3: 并发冲突** | ⭐⭐⭐ 高 | 体育比赛时间重叠冲突 |
| **T4: 长期记忆** | ⭐⭐ 中 | 文本长度适中 |
| **T5: 反事实** | ⭐⭐⭐ 极高 | 修改计分规则，测试数据污染 |

### 转换方案

#### T1: 时间计算 (Time Calculation)

**核心逻辑**: 将离散事件点转化为时间轴计算

```python
# T1-Convo-Duration: 时长计算
User: "The game started at 2:00 PM."
User: "The first quarter lasted 15 minutes."
User: "By the way, how's the weather?"  # 干扰
Query: "If the first half lasted 23 minutes, when did halftime begin?"
Answer: "2:23 PM"

# T1-Convo-Addition: 时间加法
User: "I ran for 15 minutes first, then 10 more minutes."
User: "What's for dinner today?"  # 干扰
Query: "How long did I run in total?"
Answer: "25 minutes"

# T1-Convo-Sequence: 时间序列
User: [比赛描述]
Query: "At what time reference did this occur?"
Answer: [从原文提取时间]
```

#### T3: 并发冲突 (Conflict Detection)

**核心逻辑**: 构造同一时间的空间/资源冲突

```python
# T3-Convo-TimeOverlap: 时间重叠
User: "The game was in the first quarter (1:00-1:15 PM)."
User: "Meanwhile, the coach was at a press conference downtown at 1:10 PM."
Query: "Is there any scheduling conflict?"
Answer: "Yes, coach cannot be at game and press conference simultaneously"

# T3-Convo-Conflict: 事件冲突
User: "During the game, a concert was scheduled at the same time."
User: "Both events need parking. The stadium lot is shared."
Query: "What conflict might occur?"
Answer: "Parking shortage - both events compete for limited spaces"
```

#### T5: 反事实 (Counterfactual Scoring)

**核心逻辑**: 修改计分规则，防止模型依赖预训练常识

```python
# T5-Convo-RuleChange: 规则改变
User: "Let's imagine a different football league."
User: "Touchdown = 10 points (not 6)"
User: "Field goal = 1 point (not 3)"
User: "Extra point = 5 points (not 1)"
Query: "If 2 touchdowns + 1 field goal, how many points?"
Answer: "21 points"  # 计算方式：2×10 + 1×1 = 21

# T5-Convo-Counterfactual: 反事实计分
User: "In this practice game, touchdowns are worth DOUBLE."
User: "Field goals are FREE (0 points)."
Query: "How many practice points from 3 touchdowns?"
Answer: "36 points"  # 3×12 = 36
```

### 统计数据

| 维度 | 数量 |
|------|------|
| 原始样本（使用） | 3,000 |
| **转换后样本** | **13,530** |
| T1 时间计算 | 5,806 |
| T3 并发冲突 | 3,049 |
| T5 反事实 | 4,675 |

**子任务分布**:
- T1-Convo-Duration: 2,091（时长计算）
- T1-Convo-Addition: 2,091（时间加法）
- T1-Convo-Sequence: 1,624（时间序列）
- T3-Convo-TimeOverlap: 1,624（时间重叠）
- T3-Convo-Conflict: 1,425（事件冲突）
- T5-Convo-RuleChange: 3,000（规则改变）
- T5-Convo-Counterfactual: 1,675（反事实计分）

**难度分布**:
- easy: 2,091
- medium: 7,014
- hard: 4,425

### 关键创新点

1. **数值转时间**: DROP的数值推理天然适合转化为时间计算
2. **计分规则反转**: 修改NFL计分规则，测试模型是否依赖预训练常识
3. **时间冲突构造**: 利用比赛时间段构造并发冲突场景
4. **跨句推理**: DROP原文需跨句理解，适合时间轴推理

### 文件说明

| 文件 | 说明 |
|------|------|
| `drop_conversational_converter.py` | DROP转换程序 |
| `converted_data_v3/drop_conversational.jsonl` | 转换后数据（13,530条） |
| `converted_data_v3/drop_conversational_report.json` | 统计报告 |

---

## Choice-75 数据集转换

### 数据集概述

**Choice-75** 是基于ProScript的分支选择数据集，核心特点是：

| 字段 | 说明 |
|------|------|
| `goal` | 脚本目标（如"go out for a picnic"） |
| `steps` | 步骤序列（时间有序） |
| `branching_idx` | 分支点索引 |
| `branching_step` | 分支步骤内容 |
| `option 1/2` | 两个分支选项 |
| `freeform_ra` | 场景列表：[场景描述, 正确选项, 难度] |

### 任务匹配度

| 任务 | 匹配度 | 理由 |
|------|-------|------|
| **T1: 时间计算** | ⭐⭐ 中 | 可为步骤分配时长，计算总时间 |
| **T2: 状态更新** | ⭐⭐⭐ 极高 | 步骤序列天然时间序，状态随步骤演进 |
| **T3: 冲突检测** | ⭐⭐⭐ 高 | 两个分支选项的时间/资源冲突 |
| **T5: 反事实** | ⭐⭐ 中 | 颠覆场景理由，改变选择结果 |

### 转换方案

#### T2: 状态更新 (State Tracking)

**核心逻辑**: 利用 `steps` 序列的时间序

```python
# T2-Convo-Progressive: 步骤渐进
User: "I already take a shower."
User: "I already get ready for the day."
User: "Now I am driving to the park."
User: "What should I do next?"
Answer: "park the car"  # 下一步

# T2-Convo-Branch: 分支状态
User: "I'm at 'park the car'. What should I do?"
Answer: "Choose between: park on the street OR park inside the park"
```

**子任务**:
- `T2-Convo-Progressive`: 步骤渐进（下一步是什么）
- `T2-Convo-State`: 状态推断（当前状态）
- `T2-Convo-Rollback`: 状态回滚（初始状态）
- `T2-Convo-Branch`: 分支状态（决策点）

#### T3: 冲突检测 (Conflict Detection)

**核心逻辑**: 利用 `option 1/2` 和 `scenario`

```python
# T3-Convo-Conflict: 场景冲突
User: "My situation: I have a tight budget."
User: "At 'park the car', should I choose: park on street (free) or park inside (paid)?"
Answer: "Choose park on street because tight budget"

# T3-Convo-TimeConflict: 时间冲突
User: "Option A takes 10 minutes, Option B takes 30 minutes."
User: "I need to finish everything within 1 hour."
Answer: "Choose the faster option based on time constraint"
```

#### T1: 时间计算 (Time Calculation)

**核心逻辑**: 为步骤分配时长

```python
# T1-Convo-Duration: 总时长
User: "Step: take a shower (15 min)."
User: "Step: get ready (10 min)."
User: "Step: drive (20 min)."
Query: "How long to complete everything?"
Answer: "About 45 minutes"

# T1-Convo-Parallel: 并行时间
User: "Can I do step A and step B at the same time?"
Query: "If parallel, how much time together?"
Answer: "15 minutes (max of both)"
```

#### T5: 反事实 (Counterfactual)

**核心逻辑**: 颠覆 `scenario` 理由

```python
# T5-Convo-Counterfactual: 理由反转
User: "Given 'tight budget', I should choose: park on street."
User: "But what if the OPPOSITE was true? NOT (tight budget)!"
Query: "In this opposite scenario, which option?"
Answer: "Choose park inside (reasoning reversed)"

# T5-Convo-RuleChange: 规则改变
User: "[Hypothetical world] park inside is quick and free."
User: "[Reality] Usually park on street is better."
Query: "In HYPOTHETICAL world, which to choose?"
Answer: "Follow hypothetical rules"
```

### 统计数据

| 维度 | 数量 |
|------|------|
| 原始数据 | 224 条 |
| 有效样本 | 224 条 |
| **转换后样本** | **2,582** |
| T1 时间计算 | 448 |
| T2 状态更新 | 794 |
| T3 冲突检测 | 670 |
| T5 反事实 | 670 |

**子任务分布**:
- T2-Convo-Progressive: 218
- T2-Convo-State: 176
- T2-Convo-Rollback: 176
- T2-Convo-Branch: 224
- T3-Convo-Conflict: 446
- T3-Convo-TimeConflict: 224
- T1-Convo-Duration: 224
- T1-Convo-Parallel: 224
- T5-Convo-Counterfactual: 446
- T5-Convo-RuleChange: 224

**难度分布**:
- medium: 1,112
- hard: 1,246
- very_hard: 224

### 关键创新点

1. **脚本时间序**: 利用步骤序列的时间先后关系
2. **分支决策点**: 在 `branching_idx` 处创建决策对话
3. **场景理由**: 利用 `freeform_ra` 中的场景描述进行冲突检测
4. **时长估计**: 为每个步骤估算时长，进行时间计算
5. **反事实推理**: 颠覆场景理由，测试模型规则跟随能力

### 文件说明

| 文件 | 说明 |
|------|------|
| `choice75_conversational_converter.py` | Choice-75转换程序 |
| `converted_data_v2/choice75_conversational.jsonl` | 转换后数据（2,582条） |
| `converted_data_v2/choice75_conversational_report.json` | 统计报告 |

---

## HellaSwag 数据集转换

### 数据集概述

**HellaSwag** 是基于活动完成预测的数据集，核心特点：

| 特点 | 说明 |
|------|------|
| 活动延续 | 预测视频脚本/故事的下一步 |
| 常识推理 | 需要理解活动的逻辑续接 |
| 多选项 | 4个选项中选正确续接 |
| 状态转换 | 活动从初始到完成的状态变化 |

### 字段结构

| 字段 | 说明 |
|------|------|
| `activity_label` | 活动标签（如"Removing ice from car"） |
| `ctx_a` | 上下文A（活动描述前半） |
| `ctx_b` | 上下文B（活动描述后半） |
| `endings` | 4个可能续接选项 |
| `label` | 正确答案索引（0-3） |

### 任务匹配度

| 任务 | 匹配度 | 理由 |
|------|-------|------|
| **T1: 时间计算** | 低 | 缺乏时间数字 |
| **T2: 状态更新** | ⭐⭐⭐ 极高 | 活动状态续接，先天时间序 |
| **T3: 并发冲突** | ⭐⭐⭐ 高 | 活动选项之间的时间/资源冲突 |
| **T4: 长期记忆** | 低 | 文本长度短 |
| **T5: 反事实** | ⭐⭐⭐ 极高 | 错误答案变为正确（规则反转） |

### 转换方案

#### T2: 状态更新 (State Tracking)

**核心逻辑**: 利用活动的 进度状态

```python
# T2-Convo-State: 状态推断
User: "I'm currently removing ice from car."
Assistant: "Got it, you're removing ice from car."
User: "[Context details] By the way, I had coffee this morning."
Query: "Given what I'm doing, what is my current state?"
Answer: "Currently in progress: the man continues removing the snow on his car."

# T2-Convo-Progressive: 步骤渐进
User: "I started [activity] a few minutes ago."
User: "[Context progression]"
Query: "Am I done with this activity, or is it still in progress?"
Answer: "Still in progress. The next logical step is: [correct_ending]"
```

**子任务**:
- `T2-Convo-State`: 从活动描述推断当前状态（进行中/已完成）
- `T2-Convo-Progressive`: 活动渐进，预测下一步

#### T3: 冲突检测 (Conflict Detection)

**核心逻辑**: 利用多个活动选项构造时间/资源冲突

```python
# T3-Convo-Conflict: 活动冲突
User: "I'm doing [activity_1]."  # 一人做某事
User: "My friend is doing [activity_2]."  # 另一人做另一事
User: "Can we both do these at the same time in the same place?"
Answer: "Yes/No, [reasoning about compatibility]"

# T3-Convo-TimeConflict: 时间冲突
User: "I scheduled [activity] for 2 PM."
User: "It will take about 2 hours."
User: "But I also have a meeting at 3 PM."
Query: "Is there a time conflict?"
Answer: "Yes, there's a time overlap. / No, these times don't overlap."
```

**子任务**:
- `T3-Convo-Conflict`: 两活动之间的空间/资源冲突
- `T3-Convo-TimeConflict`: 时间安排冲突检测

#### T5: 反事实 (Counterfactual)

**核心逻辑**: 颠覆正确答案规则，错误选项变为正确

```python
# T5-Convo-RuleReversal: 规则反转
User: "In THIS world, the OPPOSITE happens:"
User: "What was 'wrong' is now 'right', and 'right' is 'wrong'."
User: "[Activity context]"
Query: "In this opposite world, how does the activity continue?"
Answer: [原本错误选项的续接]

# T5-Convo-WrongToRight: 错误变正确
User: "Let's imagine a strange movie plot where:"
User: "[Wrong option] is actually the correct continuation."
User: "[Activity context]"
Query: "Following this strange logic, what happens next?"
Answer: [原本错误选项]
```

**子任务**:
- `T5-Convo-RuleReversal`: 规则反转（正确变错误，错误变正确）
- `T5-Convo-WrongToRight`: 错误答案在反事实世界变为正确

### 统计数据

| 维度 | 数量 |
|------|------|
| 原始样本（使用） | 5,000 |
| **转换后样本** | **30,000** |
| T2 状态更新 | 10,000 |
| T3 冲突检测 | 10,000 |
| T5 反事实 | 10,000 |

**子任务分布**:
- T2-Convo-State: 5,000（状态推断）
- T2-Convo-Progressive: 5,000（步骤渐进）
- T3-Convo-Conflict: 5,000（活动冲突）
- T3-Convo-TimeConflict: 5,000（时间冲突）
- T5-Convo-RuleReversal: 5,000（规则反转）
- T5-Convo-WrongToRight: 5,000（错误变正确）

**难度分布**:
- easy: 5,000
- medium: 10,000
- hard: 10,000
- very_hard: 5,000

### 关键创新点

1. **活动状态推断**: 从上下文推断活动进行状态（进行中vs已完成）
2. **冲突场景构造**: 利用不同活动选项构造时间/空间冲突
3. **反事实规则**: 颠覆正确答案规则，错误选项变为正确
4. **对话噪声**: 注入无关对话（天气、咖啡），测试抗干扰能力

### 文件说明

| 文件 | 说明 |
|------|------|
| `hellaswag_conversational_converter.py` | HellaSwag转换程序 |
| `converted_data_v3/hellaswag_conversational.jsonl` | 转换后数据（30,000条） |

---

## LongBench 数据集转换

### 数据集概述

**LongBench** 是长文本理解评测基准，核心特点：

| 特点 | 说明 |
|------|------|
| 长文本检索 | 在5k-15k字中寻找特定信息 |
| 多文档推理 | 跨文档信息整合 |
| 抗干扰能力 | 测试噪声环境下的信息提取 |
| 多任务覆盖 | 单文档QA、多文档QA、摘要、代码等 |

### 任务匹配度

| 任务 | 匹配度 | 理由 |
|------|-------|------|
| **T1: 时间计算** | ⭐⭐ 高 | 2WikiMultihopQA多跳推理，跨文档时间计算 |
| **T2: 状态更新** | 低 | 不直接支持状态追踪 |
| **T3: 并发冲突** | 低 | 不直接支持冲突检测 |
| **T4: 长期记忆** | ⭐⭐⭐ 极高 | PassageRetrieval长文本检索，埋藏时间信息 |
| **T5: 反事实** | ⭐⭐⭐ 极高 | 长对话中规则跟随，测试KV Cache衰减 |

### 转换方案

#### T4: 长期记忆 (Long-term Memory)

**核心逻辑**: 在长文本中埋藏关键时间信息，测试远距离检索

```python
# T4-Convo-Buried: 埋藏时间锚点
User: "Let me tell you about something important. I need to be there by March 3. [长文本背景]"
Assistant: "Got it, I've noted that you have something scheduled for March 3."
User: [噪声段落1] "By the way, how's the weather?"
Assistant: "I see. Noted."
User: [噪声段落2] "What did you eat for lunch?"
Assistant: "I see. Noted."
User: "What important time did I mention earlier?"
Answer: "March 3"  # 需要从早期对话中检索

# T4-Convo-Noisy: 时间噪声干扰
User: "Here's something: [长文本]... Also, important: the deadline is 3:00."
User: "Oh, and I also have something at 2:30 PM."  # 干扰时间
User: "I also have something at Monday morning."  # 更多干扰
Query: "What was the important deadline I mentioned?"
Answer: "3:00"  # 需要区分重要时间和干扰时间

# T4-Convo-Distractor: 相似时间辨认
User: "I have an important meeting at 9:00 AM."
User: [噪声段落] "Also meeting at 10:00 AM."  # 干扰
User: [噪声段落] "Another meeting at 11:00 AM."  # 干扰
Query: "What time is my IMPORTANT meeting? Not the other ones."
Answer: "9:00 AM"
```

**子任务**:
- `T4-Convo-Buried`: 时间信息埋藏在长文本早期位置
- `T4-Convo-Noisy`: 噪声时间干扰，测试信息筛选
- `T4-Convo-Distractor`: 多个相似时间，辨认关键信息

#### T1: 时间计算 (Time Calculation)

**核心逻辑**: 利用2WikiMultihopQA的多跳推理结构

```python
# T1-Convo-Multihop: 多跳时间计算
User: "[文档A]... My meeting starts at 9:00 AM."
Assistant: "Okay, meeting at 9:00 AM."
User: "[文档B]... The meeting lasts 1 hour."
Assistant: "Got it, 1 hour meeting starting at 9:00 AM."
User: "After that, I have another task that takes 30 minutes."
Assistant: "Understood. 30 minutes for the next task."
User: "If I start at 9:00 AM, spend 1 hour then 30 minutes, when will I finish?"
Answer: "10:30 AM"  # 需要跨文档提取时间信息并计算

# T1-Convo-Duration: 时长链累加
User: "Task A takes 30 minutes."
User: "Task B takes 45 minutes."
User: "Task C takes 1 hour."
User: "How much total time for all tasks?"
Answer: "2 hours 15 minutes"  # 需要2小时15分钟
```

**子任务**:
- `T1-Convo-Multihop`: 跨文档多跳推理计算
- `T1-Convo-Duration`: 时长链累加

#### T5: 反事实 (Counterfactual)

**核心逻辑**: 在长对话中植入反事实规则，测试规则跟随

```python
# T5-Convo-RuleChange: 规则改变
User: "Let's imagine a different world. In this world, 1 hour = 100 minutes (not 60)."
Assistant: "I understand. In this world, 1 hour equals 100 minutes."
User: "In this world, I have a meeting starting at 9:00 AM that lasts 1 hour."
Assistant: "Okay, meeting at 9:00 AM for 1 hour in this special world."
User: "If my meeting is 1 hour in that world, how many minutes is that?"
Answer: "100 minutes"  # 需要跟随反事实规则，而非常识

# T5-Convo-Confusion: 上下文规则混淆
User: "Context A: Meeting at 9:00 AM. Rule: before noon = SHORT (30 min)."
Assistant: "Understood. Meetings before noon are short."
User: "Context B: Meeting at 2:00 PM. Rule: after noon = LONG (2 hours)."
Assistant: "Understood. Meetings after noon are long."
User: "For Meeting A and Meeting B, how long is each?"
Answer: "Meeting A (before noon): 30 minutes. Meeting B (after noon): 2 hours."
```

**子任务**:
- `T5-Convo-RuleChange`: 长对话中的反事实时间规则
- `T5-Convo-Confusion`: 多上下文规则混淆测试

### 统计数据

| 维度 | 数量 |
|------|------|
| 原始样本（使用） | 500 (per file) |
| **转换后样本** | **4,900** |
| T1 时间计算 | 1,200 |
| T4 长期记忆 | 600 |
| T5 反事实 | 3,100 |

**子任务分布**:
- T1-Convo-Multihop: 600（多跳计算）
- T1-Convo-Duration: 600（时长累加）
- T4-Convo-Buried: 200（埋藏时间）
- T4-Convo-Noisy: 200（噪声检索）
- T4-Convo-Distractor: 200（相似辨认）
- T5-Convo-RuleChange: 1,550（规则改变）
- T5-Convo-Confusion: 1,550（上下文混淆）

**难度分布**:
- easy: 600
- medium: 600
- hard: 1,950
- very_hard: 1,750

### 关键创新点

1. **长文本检索**: 时间信息埋藏在5k-15k文本中，测试远距离记忆
2. **时间噪声**: 注入虚假时间信息，测试Memory Decay
3. **多跳推理**: 跨文档提取时间参数并计算
4. **规则跟随**: 长对话中保持反事实规则，测试注意力衰减

### 数据来源

| 文件 | 任务 | 说明 |
|------|------|------|
| `passage_retrieval_en.jsonl` | T4 | 英文段落检索 |
| `passage_retrieval_zh.jsonl` | T4 | 中文段落检索 |
| `2wikimqa.jsonl` | T1 | 多跳QA推理 |
| `hotpotqa.jsonl` | T1 | Hotpot多文档QA |
| `musique.jsonl` | T1 | 多跳音乐QA |
| `samsum.jsonl` | T5 | 对话摘要 |
| `qasper.jsonl` | T5 | 论文QA |
| `multifieldqa_en.jsonl` | T5 | 多领域QA |

### 文件说明

| 文件 | 说明 |
|------|------|
| `longbench_conversational_converter.py` | LongBench转换程序 |
| `converted_data_v3/longbench_conversational.jsonl` | 转换后数据（4,900条） |

---

## NarrativeQA 数据集转换

### 数据集概述

**NarrativeQA (ConTEB版本)** 是基于文学作品和剧本的叙事性问答数据集，核心特点：

| 特点 | 说明 |
|------|------|
| 叙事纵深 | 复杂的人物关系、情节起伏、环境描写 |
| 分片结构 | chunk_id提供文档内时间序 |
| 长上下文 | 平均151.9 tokensper chunk，适合长期记忆测试 |
| 文学性 | 修辞丰富，需要提取事件主干 |

### 字段结构

| 字段 | 说明 |
|------|------|
| `chunk_id` | 文档分片ID（格式：doc-id_chunk-id）|
| `chunk` | 剧情片段文本 |
| `query` | GPT-4o生成的问题 |
| `og_query` | 原始问题 |
| `answer` | 答案 |

### 任务匹配度

| 任务 | 匹配度 | 理由 |
|------|-------|------|
| **T1: 时间计算** | ⭐⭐ 中 | 叙事中有"几天后"等逻辑偏移 |
| **T2: 状态更新** | ⭐⭐⭐ 极高 | 剧情发展=人物状态连续演变 |
| **T3: 并发冲突** | 低 | 叙事多为单线，难提取时间冲突 |
| **T4: 长期记忆** | ⭐⭐⭐ 极高 |跨chunk长线情节检索 |
| **T5: 反事实** | ⭐⭐ 中 | 修改角色结局，测试预训练知识影响 |

### 转换方案

#### T2: 状态更新 (State Tracking)

**核心逻辑**: 利用叙事文本追踪人物状态变化

```python
# T2-Convo-State: 状态追踪
User: "I'm reading a story. Here's a part: Mark by day is a loner, but by night
he runs a pirate radio station."
Assistant: "Got it, this is about Mark. Let me know if you have questions."
User: "What does Mark do during the day?"
Answer: "By day, Mark is seen as a loner, hardly talking to anyone around him."

# T2-Convo-Progressive: 状态演进
User: "In this story, Mark begins with: starts a pirate radio station..."
User: "Then his identity is discovered by Nora..."
User: "Then the radio show becomes popular..."
Query: "Based on these events, what is Mark's current situation?"
Answer: "Mark's radio show is popular and influential after confronting a student suicide."
```

**子任务**:
- `T2-Convo-State`: 从叙事片段推断人物当前状态
- `T2-Convo-Progressive`: 跨chunk状态演进追踪

#### T4: 长期记忆 (Long-term Memory)

**核心逻辑**: 利用chunk_id分组，埋藏关键信息

```python
# T4-Convo-Buried: 埋藏信息检索
User: "Here's a story detail: Mark's pirate station theme song is 'Everybody Knows'by Leonard Cohen."
User: [噪声对话1] "What's the weather like?"
User: [噪声对话2] "I need to buy groceries."
User: [噪声对话3] "Did you see the game?"
Query: "What important detail did I mention earlier about Mark's station?"
Answer: "Mark's pirate station theme song is 'Everybody Knows' by Leonard Cohen."

# T4-Convo-Cross: 跨chunk检索
User: "Story part 1: [chunk_0 内容]"
User: [噪声/其他chunk]
User: "Story part 2: [chunk_1 内容]"
Query: "From the first story part, what was mentioned?"
Answer: [从chunk_0检索关键信息]

# T4-Convo-Detail: 细节回忆
User: "Here's a story excerpt: [长叙事文本]"
User: [噪声问题]
Query: "What is an important detail about [角色]?"
Answer: [提取具体细节]
```

**子任务**:
- `T4-Convo-Buried`: 关键事实埋藏在叙事中
- `T4-Convo-Cross`: 跨chunk信息检索
- `T4-Convo-Detail`: 叙事细节回忆

#### T1: 时间计算 (Time Calculation)

**核心逻辑**: 利用chunk_id顺序构建时间序

```python
# T1-Convo-Ordering: 事件排序
User: "Story fragment 3: [chunk_2 内容]"
User: "Story fragment 1: [chunk_0 内容]"
User: "Story fragment 2: [chunk_1 内容]"
Query: "In what chronological order do these story fragments occur?"
Answer: "Fragment 1, Fragment 2, Fragment 3"
```

**子任务**:
- `T1-Convo-Ordering`: 叙事片段时间排序

#### T5: 反事实 (Counterfactual)

**核心逻辑**: 修改剧情走向，测试预训练知识影响

```python
# T5-Convo-Twist: 剧情反转
User: "In the original story: Mark runs a pirate radio station..."
User: "But in THIS version: Mark makes a completely different choice."
Query: "How does Mark's different choice affect the outcome?"
Answer: [基于反事实推理的回答]
```

**子任务**:
- `T5-Convo-Twist`: 剧情反转反事实推理

### 统计数据

| 维度 | 数量 |
|------|------|
| 原始文档 | 1,572 |
| 原始chunk | 7,807 |
| 使用query | 5,000 |
| **转换后样本** | **10,281** |
| T1 时间计算 | 84 |
| T2 状态更新 | 3,083 |
| T4 长期记忆 | 6,195 |
| T5 反事实 | 919 |

**子任务分布**:
- T1-Convo-Ordering: 84（事件排序）
- T2-Convo-State: 2,988（状态追踪）
- T2-Convo-Progressive: 95（状态演进）
- T4-Convo-Buried: 3,008（埋藏信息）
- T4-Convo-Cross: 100（跨chunk检索）
- T4-Convo-Detail: 3,087（细节回忆）
- T5-Convo-Twist: 919（剧情反转）

**难度分布**:
- medium: 6,159
- hard: 4,022
- very_hard: 100

### 关键创新点

1. **叙事状态追踪**: 利用文学文本追踪人物状态演变
2. **跨chunk检索**: 利用chunk_id构建时间序，测试长期记忆
3. **反事实剧情**: 修改原著走向，测试预训练知识干扰
4. **文学理解**: 修辞较多的文本，需要提取事件主干

### 文件说明

| 文件 | 说明 |
|------|------|
| `narrativeqa_conversational_converter.py` | NarrativeQA转换程序 |
| `converted_data_v3/narrativeqa_conversational.jsonl` | 转换后数据（10,281条） |

---

## OpenPI 2.0 数据集转换

### 数据集概述

**OpenPI 2.0 (Open Procedure Tracking)** 是专门为实体状态追踪设计的数据集，核心特点：

| 特点 | 说明 |
|------|------|
| 状态变化 | 每个步骤都有`before`和`after`状态 |
| 显著性评分 | Saliency分数标识状态变化重要性 |
| 属性追踪 | location, condition, possession, is_destroyed |
| 过程导引 | WikiHow风格的任务步骤 |

### 字段结构

| 字段 | 说明 |
|------|------|
| `goal` | 任务目标（如"清洁挡风玻璃"） |
| `steps` | 步骤列表 |
| `states` | 实体状态变化（entity → attribute → before/after） |
| `saliency` | 状态变化显著性（≥0.3为重要） |

### 任务匹配度

| 任务 | 匹配度 | 理由 |
|------|-------|------|
| **T1: 时间计算** | 低 | 步骤为逻辑序，缺乏具体时间 |
| **T2: 状态更新** | ⭐⭐⭐ 极高 | `before`/`after`完美匹配状态追踪 |
| **T3: 并发冲突** | ⭐⭐ 高 | location属性可构造空间冲突 |
| **T4: 长期记忆** | 低 | 文本长度短 |
| **T5: 反事实** | 中 | 可修改流程结果 |

### 转换方案

#### T2: 状态更新 (State Tracking)

**核心逻辑**: 利用`before`/`after`字段追踪实体状态变化

```python
# T2-Convo-State: 单步状态追踪
User: "I'm making a simple windshield cleaner. Step 1: Purchase a blackboard eraser."
Assistant: "Okay, step 1 completed."
User: "After step 1, where is the eraser?"
Answer: "at customer's house | in home"  # 从after字段提取

# T2-Convo-Progressive: 多步状态演进
User: "Step 1: Purchase eraser. Step 2: Store in glove box. Step 3: Use to clean."
User: "Through all steps, what is the condition of the eraser?"
Answer: "used"  # 从最终状态推断

# T2-Convo-Intermediate: 中间状态查询
User: [完整流程呈现]
User: "After step 2 but before the final step, where was the eraser?"
Answer: "in the glove box"  # 中间状态检索
```

**子任务**:
- `T2-Convo-State`: 对物体状态提问（位置、条件、所有权）
- `T2-Convo-Progressive`: 跨步骤状态追踪
- `T2-Convo-Intermediate`: 中间状态检索

#### T3: 冲突检测 (Conflict Detection)

**核心逻辑**: 利用location/condition属性构造空间/资源冲突

```python
# T3-Convo-Location: 空间冲突
User: "The eraser is now stored in the car's glove box."
User: "Now I want to use the eraser in my office upstairs."
Query: "Is there any issue with this plan?"
Answer: "Yes, there's a potential conflict. The eraser is currently 
in the glove box, but you want to use it in the office. You may need 
to retrieve it first."

# T3-Convo-Resource: 资源冲突
User: "After cleaning, the cloth's condition changed from 'new' to 'dirty'."
User: "Can I use the same cloth again?"
Query: "Given the cloth is now 'dirty', is it available for reuse?"
Answer: "No, the cloth is currently 'dirty' and may not be suitable 
for reuse. Consider cleaning or replacing it first."
```

**子任务**:
- `T3-Convo-Location`: 物品位置与使用位置冲突
- `T3-Convo-Resource`: 物品状态与二次使用冲突
- `T3-Convo-Procedure`: 跨步骤状态一致性检测

### 数据处理要点

1. **显著性过滤**: 仅保留 `saliency >= 0.3` 的状态变化
2. **属性筛选**: 聚焦 `location`, `condition`, `possession`, `is_destroyed`
3. **同义词整合**: `possession | ownership` 作为评估匹配库

### 统计数据

| 维度 | 数量 |
|------|------|
| 原始procedure | 55 |
| **转换后样本** | **885** |
| T2 状态更新 | 761 |
| T3 冲突检测 | 124 |

**子任务分布**:
- T2-Convo-State: 548（单步状态）
- T2-Convo-Progressive: 213（演进追踪）
- T3-Convo-Location: 122（空间冲突）
- T3-Convo-Resource: 2（资源冲突）

**难度分布**:
- medium: 397
- hard: 488

### 关键创新点

1. **before/after字段**: 直接利用标注的状态变化对
2. **显著性过滤**: 保留人类直觉共识的重要变化
3. **物理属性聚焦**: location/condition互斥性强，评测严谨
4. **过程追踪**: WikiHow步骤天然时间序

### 文件说明

| 文件 | 说明 |
|------|------|
| `openpi_conversational_converter.py` | OpenPI 2.0转换程序 |
| `converted_data_v3/openpi_conversational.jsonl` | 转换后数据（885条） |

---

## 数据集转换总结

### 各数据集任务覆盖

| 数据集 | T1 | T2 | T3 | T4 | T5 |
|--------|----|----|----|----|----|
| ATOMIC | - |✓ | ✓ | - | ✓ |
| Choice-75 | ✓ | ✓ | ✓ | - | ✓ |
| CosmosQA | - | ✓ | - | ✓ | ✓ |
| DROP | ✓ | - | ✓ | - | ✓ |
| HellaSwag | - | ✓ | ✓ | - | ✓ |
| LongBench | ✓ | - | - | ✓ | ✓ |
| NarrativeQA | ✓ | ✓ | - | ✓ | ✓ |
| OpenPI 2.0 | - | ✓ | ✓ | - | - |

---

## PASTA 数据集转换

### 数据集概述

**PASTA (Participant State Tracking in Narratives)** 是参与者状态推理数据集，核心特点：

| 特点 | 说明 |
|------|------|
| 故事状态推理 | 从5句故事推断参与者心理/身份状态 |
| 反事实设计 | 原生包含原版故事 vs 修改版故事成对数据 |
| 最少支持集 | 标注了推断状态的关键句子 |
| 防数据污染 | 使用修改版故事测试模型是否依赖预训练记忆 |

### 字段结构

| 字段 | 说明 |
|------|------|
| `Input.line1-5` | 原版故事5句话 |
| `Answer.assertion` | 从故事推断的参与者状态 |
| `Answer.lineX.on` | 该句是否为关键证据（布尔值）|
| `Answer.mod_line1-5` | 修改后的反事实故事 |
| `Answer.mod_assertion` | 反事实状态 |

### 任务匹配度

| 任务 | 匹配度 | 理由 |
|------|-------|------|
| **T1: 时间计算** | 低 | 故事缺乏具体时间 |
| **T2: 状态更新** | ⭐⭐⭐ 极高 | 专门追踪心理/身份状态变化 |
| **T3: 并发冲突** | 低 | 单线叙事 |
| **T4: 长期记忆** | 低 | 文本仅5句 |
| **T5: 反事实** | ⭐⭐⭐ 极高 | 原生反事实对，完美测试数据污染 |

### 转换方案

#### T2: 状态更新 (State Tracking)

**核心逻辑**: 从故事推断参与者状态

```python
# T2-Convo-State: 状态推断
User: "Here's a short story: Bill and Ted were best friends. They were high school students..."
User: "What can you infer about Bill's identity or role?"
Answer: "Bill and Ted were older teenagers."  # 从"高中生"推断

# T2-Convo-Progressive: 渐进状态追踪
User: "Line 1: Bill and Ted were best friends."
User: "Line 2: They were high school students." (关键证据)
User: "Line 3: They would eat lunch together every day."
...
Query: "Based on all lines, what is Bill's state?"
Answer: "Bill and Ted were older teenagers."

# T2-Convo-Evidence: 证据识别
User: "Story: [完整故事]"
User: "The story suggests that Bill and Ted were older teenagers."
Query: "Which line(s) are most crucial for this inference?"
Answer: "The key evidence is: Line 2: They were high school students."
```

**子任务**:
- `T2-Convo-State`: 从故事推断参与者状态
- `T2-Convo-Progressive`: 逐句追踪状态演变
- `T2-Convo-Evidence`: 识别关键证据句子

#### T5: 反事实 (Counterfactual - 防数据污染)

**核心逻辑**: 使用修改版故事测试模型是否依赖预训练记忆

```python
# T5-Convo-Counterfactual: 反事实测试
User: "Read this story carefully: Bill and Ted were best friends. 
       They were KINDERGARTEN students. [修改版故事]"
User: "Based on this story, what is true about Bill?"
Answer: "Bill and Ted were toddlers."  
# 如果回答"teenagers" = 数据污染（用了预训练记忆）
# 如果回答"toddlers" = 真正遵循当前上下文

# T5-Convo-Contrastive: 对比对测试
User: "Original story: They were high school students. 
       (Inference: older teenagers)"
User: "Different version: They were kindergarten students.
       (Question: What is true in the DIFFERENT version?)"
Answer: "Bill and Ted were toddlers."

# T5-Convo-RuleChange: 规则跟随 vs 预训练记忆
User: "In this story, some facts are DIFFERENT from what you might expect."
User: "[修改版故事]"
User: "You might have heard similar stories where they were teenagers. 
       Is that true here?"
Answer: "No, I should only use facts from THIS story."
Query: "So in THIS story, what is true?"
Answer: "Bill and Ted were toddlers."  # 正确遵循新规则

# T5-Convo-Reversal: 状态反转
User: "Consider this scenario: [修改版故事]"
Query: "Based on this scenario, describe the participant's state."
Answer: [反事实状态]
```

**子任务**:
- `T5-Convo-Counterfactual`: 反事实故事推理
- `T5-Convo-Contrastive`: 对比原版vs修改版
- `T5-Convo-RuleChange`: 规则跟随测试
- `T5-Convo-Reversal`: 状态反转理解

### 数据处理要点

1. **对比测试对**: 同一故事的原版和修改版成对测试
2. **关键句子标注**: 利用 `lineX.on` 定位最小支持集
3. **状态分类**: 情感/性格/身份/物理状态等维度

### 统计数据

| 维度 | 数量 |
|------|------|
| 原始样本（使用） | 8,476 |
| **转换后样本** | **20,969** |
| T2 状态更新 | 11,493 |
| T5 反事实 | 9,476 |

**子任务分布**:
- T2-Convo-State: 5,000（状态推断）
- T2-Convo-Progressive: 1,493（渐进追踪）
- T2-Convo-Evidence: 5,000（证据识别）
- T5-Convo-Counterfactual: 5,000（反事实测试）
- T5-Convo-Contrastive: 1,432（对比对）
- T5-Convo-RuleChange: 1,509（规则跟随）
- T5-Convo-Reversal: 1,535（状态反转）

**难度分布**:
- medium: 4,527
- hard: 8,501
- very_hard: 7,941

### 关键创新点

1. **原生反事实对**: 原版故事 + 修改版故事成对数据
2. **防数据污染测试**: 使用修改版测试模型是否依赖预训练记忆
3. **关键证据标注**: 标注了推断所需的最小句子集合
4. **心理/身份状态**: 补充OpenPI缺失的心理状态维度

### 文件说明

| 文件 | 说明 |
|------|------|
| `pasta_conversational_converter.py` | PASTA转换程序 |
| `converted_data_v3/pasta_conversational.jsonl` | 转换后数据（20,969条） |

---

## PIQA 数据集转换

### 数据集概述

**PIQA (Physical Interaction QA)** 是物理常识推理数据集，核心特点：

| 特点 | 说明 |
|------|------|
| 物理常识 | 关于日常生活操作的物理合理性判断 |
| 二选一 | 每个问题有两个候选方案，选择正确的 |
| 短文本 | goal平均7词，solution平均18-19词 |
| 标签均衡 | 正负标签约各50% |

### 字段结构

| 字段 | 说明 |
|------|------|
| `goal` | 目标/问题（如"How do I...") |
| `sol1` | 候选方案1 |
| `sol2` | 候选方案2 |
| `label` | 正确答案索引（0或1）|

### 任务匹配度

| 任务 | 匹配度 | 理由 |
|------|-------|------|
| **T1: 时间计算** | 低 | 缺乏时间概念 |
| **T2: 状态更新** | ⭐⭐ 中 | 可为物理动作添加时间线 |
| **T3: 并发冲突** | ⭐⭐ 中 | 可改造为物理资源冲突 |
| **T4: 长期记忆** | 低 | 文本极短 |
| **T5: 反事实** | ⭐⭐⭐ 极高 | 原错误答案在平行宇宙变正确 |

### 转换方案

#### T2: 状态更新 (State Tracking)

**核心逻辑**: 为物理动作添加时间轴

```python
# T2-Convo-Timeline: 物理状态时间线
User: "At 2:00 PM, I started boiling butter."
User: "At 2:10 PM, I poured it into a jar."
Query: "Now it's 2:15 PM. What is the butter's state?"
Answer: "The substance is now in liquid form in the jar."

# T2-Convo-Sequence: 动作序列追踪
User: "I want to attach metal legs to a chair."
User: "Options: A) Weld the metal (correct) B) Nail the metal (wrong)"
User: "I chose Option A."
Query: "After completing this action, what will be the result?"
Answer: "The metal legs are now permanently attached to the chair."
```

**子任务**:
- `T2-Convo-Timeline`: 为物理动作构造时间线状态
- `T2-Convo-Sequence`: 追踪动作序列结果

#### T3: 冲突检测 (Conflict Detection)

**核心逻辑**: 检测物理方案适用性

```python
# T3-Convo-Resource: 物理资源/方案冲突
User: "Goal: Attach metal legs to a chair."
User: "Approaches: A) Weld the metal (correct) B) Nail the metal (wrong)"
Query: "Is there any issue with either approach? Which should I use?"
Answer: "Approach A (Weld the metal) is correct. Approach B (Nail) 
would not work because metal doesn't hold nails well."
```

**子任务**:
- `T3-Convo-Resource`: 物理/方案适用性判断

#### T5: 反事实 (Counterfactual - 防数据污染)

**核心逻辑**: 平行宇宙中，原错误答案变正确

```python
# T5-Convo-Counterfactual: 平行宇宙物理规则
User: "In this parallel universe, metal is soft like wood."
User: "I need to attach metal legs to a chair."
User: "Options: A) Pour it onto a plate B) Pour it into a jar"
Query: "Based on this parallel universe's rules, which is correct?"
Answer: "In this parallel universe, option A (nailing) is correct 
because metal is soft enough to be nailed."

# T5-Convo-RuleReverse: 物理规则反转
User: "In this world, physical properties are reversed from normal."
User: "Specifically, heat causes things to freeze, cold makes them boil."
User: "I want to boil butter. Which approach works?"
Answer: "With reversed physics, you need to cool it, not heat it."

# T5-Convo-ChoiceInversion: 正确/错误答案互换
User: "In NORMAL world: Welding metal is correct for attaching legs."
User: "But in the OPPOSITE world: Physics is reversed!"
Query: "Same goal, same options. Which is correct in OPPOSITE world?"
Answer: "In the opposite world, nailing (normally wrong) becomes correct."
```

**子任务**:
- `T5-Convo-Counterfactual`: 平行宇宙物理规则反转
- `T5-Convo-RuleReverse`: 物理规则反转测试
- `T5-Convo-ChoiceInversion`: 正确答案与错误答案互换

### 统计数据

| 维度 | 数量 |
|------|------|
| 原始样本（使用） | 5,000 |
| **转换后样本** | **11,712** |
| T2 状态更新 | 2,312 |
| T3 冲突检测 | 1,510 |
| T5 反事实 | 7,890 |

**子任务分布**:
- T2-Convo-Timeline: 810（时间线状态）
- T2-Convo-Sequence: 1,502（动作序列）
- T3-Convo-Resource: 1,510（资源冲突）
- T5-Convo-Counterfactual: 5,000（平行宇宙）
- T5-Convo-RuleReverse: 1,449（规则反转）
- T5-Convo-ChoiceInversion: 1,441（选择反转）

**难度分布**:
- medium: 3,822
- hard: 6,449
- very_hard: 1,441

### 关键创新点

1. **反数据污染测试**: PIQA基于ROCStories，模型可能见过原数据
2. **物理反直觉**: 平行宇宙中原本错误的物理操作变为正确
3. **时间线构造**: 为物理动作添加时间轴，追踪状态演变
4. **常识验证**: 原错误答案在正常世界的物理不合理性

### 文件说明

| 文件 | 说明 |
|------|------|
| `piqa_conversational_converter.py` | PIQA转换程序 |
| `converted_data_v3/piqa_conversational.jsonl` | 转换后数据（11,712条） |

---

## TimeDial 数据集转换

### 数据集概述

**TimeDial** 是多轮日常对话中的时间推理评测数据集，核心特点是：

| 特点 | 说明 |
|------|------|
| 多轮对话 | 平均11.7轮对话，测试对话中的时间理解 |
| 干扰项设计 | 专门设计了字面干扰项（Spurious features） |
| 时间计算 | 完型填空形式，填入 `<MASK>` |
| 抗干扰测试 | 测试模型是否会被上下文数字干扰 |

### 字段结构

| 字段 | 说明 |
|------|------|
| `conversation` | 多轮对话列表 |
| `correct1/2` | 正确答案选项 |
| `incorrect1/2` | 错误干扰选项 |
| `incorrect1_rule` | 干扰项类型（Rule 1: phrase matching, Rule 2: numeral matching, Rule 3: other） |

### 任务匹配度

| 任务 | 匹配度 | 理由 |
|------|-------|------|
| **T1: 时间计算** | ⭐⭐⭐ 极高 | 专为时间计算+干扰项测试设计 |
| **T2: 状态更新** | 低 | 不涉及状态追踪 |
| **T3: 并发冲突** | 低 | 不涉及冲突检测 |
| **T4: 长期记忆** | ⭐⭐ 中 | 多轮对话，测试时间信息检索 |
| **T5: 反事实** | 低 | 常识推理，无反事实设计 |

### 转换方案

#### T1: 时间计算 (Time Calculation)

**核心逻辑**: 利用干扰项测试抗干扰能力

```python
# T1-Convo-Calc: 时间计算（抗干扰）
User: "We need to take the system offline for maintenance."
User: "It'll be down for at least twelve hours, back by 6 PM Saturday."
User: "By the way, today's weather is great!"
User: "So we've prepared for the downtime. We've allowed <MASK> to be safe."
Query: "What time duration best fits the context?"
Answer: "48 hours"  # 需要推理，而非抄写"two hours"或"12"

# T1-Convo-Distractor: 干扰项测试
User: "The meeting starts in two hours. It'll last for twelve hours."
User: "Actually, I meant 2 PM, not two hours from now. Twelve hours is too long."
User: "How much time should we reserve for this project?"
Query: "Looking past the distractors, what is the actual time needed?"
Answer: [从干扰项中正确识别时间]

# T1-Convo-MultiChoice: 多选形式
User: [多轮对话，含<MASK>]
Options: A. two hours (incorrect) B. 12 days (incorrect) C. 48 hours (correct)
Query: "Which option best fills the <MASK>?"
Answer: "C"
```

**子任务**:
- `T1-Convo-Calc`: 时间计算，包含数字干扰
- `T1-Convo-Distractor`: 干扰项识别测试
- `T1-Convo-MultiChoice`: 多选形式评测

#### T4: 长期记忆 (Long-term Memory)

**核心逻辑**: 在多轮对话中追踪时间信息

```python
# T4-Convo-Dialog: 对话时间检索
User: [第1轮] "I'll be there tomorrow at 3 PM."
User: [第2-8轮] [大量对话噪声]
User: [第9轮] "What time did I say I'd arrive?"
Answer: "3 PM tomorrow"  # 需要从早期对话中检索

# T4-Convo-Recall: 时间锚点回忆
User: [对话开始] "The deadline is March 15th."
User: [大量中间对话]
Query: "What important date did I mention at the beginning?"
Answer: "March 15th"
```

**子任务**:
- `T4-Convo-Dialog`: 多轮对话时间追踪
- `T4-Convo-Recall`: 时间锚点检索

### 干扰类型分析

TimeDial 的核心价值在于明确的干扰项标注：

| Rule 类型 | 干扰机制 | 测试价值 |
|-----------|----------|----------|
| Rule 1 (Phrase matching) | 上下文短语直接匹配 | 测试是否能进行推理而非抄写 |
| Rule 2 (Numeral matching) | 上下文数字直接复制 | 测试是否能抗数字干扰 |
| Rule 3 (Other) | 其他干扰模式 | 综合抗干扰能力 |

### 统计数据

| 维度 | 数量 |
|------|------|
| 原始样本 | 1,446 |
| **转换后样本** | **5,660** |
| T1 时间计算 | 4,287 |
| T4 长期记忆 | 1,373 |

**子任务分布**:
- T1-Convo-Calc: 1,429（时间计算）
- T1-Convo-Distractor: 1,429（干扰项测试）
- T1-Convo-MultiChoice: 1,429（多选形式）
- T4-Convo-Dialog: 1,058（对话检索）
- T4-Convo-Recall: 315（锚点回忆）

**难度分布**:
- hard: 4,231
- medium: 1,429

### 关键创新点

1. **抗干扰测试**: 专门设计干扰项，测试模型是否抄写上下文
2. **Rule标注**: 明确标注干扰类型（phrase matching vs numeral matching）
3. **多轮对话**: 在真实对话场景中测试时间推理
4. **时间计算**: 需要推理而非简单匹配

### 文件说明

| 文件 | 说明 |
|------|------|
| `timedial_conversational_converter.py` | TimeDial转换程序 |
| `converted_data_v3/timedial_conversational.jsonl` | 转换后数据（5,660条） |

---

## UDST-DurationQA 数据集转换

### 数据集概述

**UDST-DurationQA** 是UDS-T 的衍生版本，专门用于时长估算问答，核心特点：

| 特点 | 说明 |
|------|------|
| 时长问答 | 自然语言形式的时长估算问题 |
| 正负样本 | yes/no 标签标注答案合理性 |
| 常识测试 | 测试隐式常识时长理解 |
| 干扰选项 | 同一问题配对多个候选答案 |

### 字段结构

| 字段 | 说明 |
|------|------|
| `sentence` | 上下文句子 |
| `question` | 时长相关问题 |
| `answer` | 候选答案 |
| `label` | 标签（yes/no）|

### 任务匹配度

| 任务 | 匹配度 | 理由 |
|------|-------|------|
| **T1: 时间计算** | ⭐⭐⭐ 极高 | 专为时长估算设计，含干扰测试 |
| **T2: 状态更新** | 低 | 孤立短句，无状态流转 |
| **T3: 并发冲突** | 低 | 不涉及冲突场景 |
| **T4: 长期记忆** | 低 | 文本极短（平均20词）|
| **T5: 反事实** | 低 | 依赖现实常识 |

### 转换方案

#### T1: 时间计算 (Duration Estimation)

**核心逻辑**: 聚合 yes/no 配对，创建带干扰项的多选题

```python
# T1-Convo-MultiChoice: 多选形式（核心）
User: "Let me tell you about something: I called the school most probably 10 times before I finally enrolled in a 20 hour package."
Assistant: "I see. Please go on."
User: "Speaking of which, I had an interesting conversation yesterday."
Assistant: "Interesting, thanks for sharing."
User: "How long does it take for me to call the school?"
Options:
A. 4 days (incorrect)
B. for decades (incorrect)
C. 54 minutes (correct)
D. several years (incorrect)
Answer: C (测试抗干扰能力)

# T1-Convo-CommonSense: 开放式估算
User: "I baked a cake for my friend's birthday."
User: "How long did I bake the cake? (Please provide a reasonable duration estimate)"
Answer: "2 hours"  # 需要常识推理，而非抄写上下文数字

# T1-Convo-Distractor: 干扰项嵌入
User: "I baked a cake."
User: "By the way, I read about something that took 3 months once."
User: "How long did I bake the cake?"
Answer: "2 hours"  # 需要 ignoring 上下文中的 "3 months" 干扰
```

**子任务**:
- `T1-Convo-MultiChoice`: 多选形式，正确答案vs干扰项
- `T1-Convo-CommonSense`: 开放式时长估算
- `T1-Convo-Distractor`: 干扰项嵌入上下文，测试抗干扰

### 数据处理要点

1. **聚合配对**: 以 (sentence, question) 为Key 聚合 yes/no 答案
2. **干扰项构造**: yes 答案为正确选项，no 答案为干扰项
3. **常识测试**: 测试模型是否理解日常活动的合理时长

### 统计数据

| 维度 | 数量 |
|------|------|
| 原始entries (train/dev/test) | 49,894 |
| 唯一问题上下文 | 7,082 |
| **转换后样本** | **20,870** |
| T1 时间计算 | 20,870 |

**子任务分布**:
- T1-Convo-MultiChoice: 7,074（多选形式）
- T1-Convo-CommonSense: 6,722（常识估算）
- T1-Convo-Distractor: 7,074（干扰测试）

**难度分布**:
- medium: 6,724
- hard: 14,146

### 关键创新点

1. **干扰项设计**: yes/no 配对提供天然干扰项
2. **常识时长**: 测试隐式常识（如烤蛋糕2小时 vs 3个月）
3. **抗干扰测试**: 多选题形式，上下文包含干扰数字
4. **开箱即用**: 作者已完成时长问答重构

### 文件说明

| 文件 | 说明 |
|------|------|
| `udst_durationqa_conversational_converter.py` | UDST-DurationQA转换程序 |
| `converted_data_v3/udst_durationqa_conversational.jsonl` | 转换后数据（20,870条）|

---

## TRACIE 数据集转换

### 数据集概述

**TRACIE (Temporal Reasoning on Implicit Events)** 来自 NAACL 2021，专门测试隐式事件时序推理能力，核心特点是：

| 特点 | 说明 |
|------|------|
| 隐式时间 | 无时间戳，依赖常识和因果推理排序 |
| 正负配对 | 每个故事配套 starts before/after 正负样本 |
| NLI格式 | 原始格式为事件关系判断（positive/negative） |
| 分布鲁棒 | 提供IID和Uniform-prior两种切分 |

### 字段结构

| 字段 | 说明 |
|------|------|
| `event` | 查询语句（如"A starts after B"）|
| `story` | 上下文故事 |
| `answer` | 标签（positive/negative）|

### 任务匹配度

| 任务 | 匹配度 | 理由 |
|------|-------|------|
| **T1: 时间计算** | ⭐⭐⭐ 极高 | 隐式事件排序，无时间戳推理 |
| **T2: 状态更新** | ⭐⭐ 高 | 从时序推断状态变化 |
| **T3: 并发冲突** | 低 | 线性叙事，无冲突场景 |
| **T4: 长期记忆** | 低 | 故事平均43词，过短 |
| **T5: 反事实** | 低 | 依赖现实常识物理法则 |

### 转换方案

#### T1: 时间计算 (Temporal Ordering)

**核心逻辑**: 将正负样本配对，转换为时序推理问题

```python
# T1-Convo-Ordering: 事件排序
User: "Story: Chad had gone to an amusement park. He was riding on the roller coaster..."
Assistant: "I've read the story. What's your question about the events?"
User: "Based on the story's timeline, does 'Chad looked for his baseball cap' happen before or after 'he got off the ride'?"
Answer: "before"  # 需要从因果链推断

# T1-Convo-MultiChoice: 多选形式
User: "Read this story carefully: [story]"
User: "Question: Does 'A' happen before or after 'B'?"
Options: A. before B. after
Answer: "A" or "B"

# T1-Convo-Sequence: 事件序列排列
User: "In the story's timeline, list these events in chronological order:1. Event A
2. Event B"
Answer: "1. [earlier event]2. [later event]"

# T1-Convo-Causal: 因果推理
User: "Explain the causal chain that determines whether 'A' happens before 'after' B."Answer: [因果解释]
```

**子任务**:
- `T1-Convo-Ordering`: 直接排序问题
- `T1-Convo-MultiChoice`: 多选形式
- `T1-Convo-Sequence`: 事件序列排列
- `T1-Convo-Causal`: 因果解释（高难度）

#### T2: 状态更新 (State Tracking)

**核心逻辑**: 从时序推断状态变化

```python
# T2-Convo-State: 状态推断
User: "At the moment when 'B' occurs, has 'A' already happened?"
Answer: "yes" or "no"  # 需要时序推理

# T2-Convo-Consequence: 后果推断
User: "What must happen before 'A' can occur?"
Answer: [前置事件]
```

**子任务**:
- `T2-Convo-State`: 特定时刻状态
- `T2-Convo-Consequence`: 前置/后置事件推断

### 数据处理要点

1. **配对合并**: 将同一故事的 before/after 配对转换为一个推理问题
2. **Uniform-prior**: 使用uniform-prior切分，防止统计捷径作弊
3. **因果标注**: 利用正负标签推导正确的时序关系

### 统计数据

| 维度 | 数量 |
|------|------|
| 原始样本 | 4,248 |
|唯一故事 | 342 |
| 有效配对 | 2,044 |
| **转换后样本** | **9,479** |
| T1 时间计算 | 5,391 |
| T2 状态更新 | 4,088 |

**子任务分布**:
- T1-Convo-Ordering: 2,044（排序问题）
- T1-Convo-MultiChoice: 2,044（多选形式）
- T1-Convo-Sequence: 961（序列排列）
- T1-Convo-Causal: 342（因果推理）
- T2-Convo-State: 2,044（状态推断）
- T2-Convo-Consequence: 2,044（后果推断）

**难度分布**:
- medium: 5,994
- hard: 3,143
- very_hard: 342

### 关键创新点

1. **隐式时序**: 无时间戳，纯靠常识推理
2. **因果链理解**: 需要理解事件因果才能排序
3. **配对设计**: 正负样本配对，严格评测
4. **分布鲁棒**: Uniform-prior切分防止作弊

### 文件说明

| 文件 | 说明 |
|------|------|
| `tracie_conversational_converter.py` | TRACIE转换程序 |
| `converted_data_v3/tracie_conversational.jsonl` | 转换后数据（9,479条）|

---

## 数据集转换总结

### 各数据集任务覆盖

| 数据集 | T1 | T2 | T3 | T4 | T5 |
|--------|----|----|----|----|----|
| ATOMIC | - | ✓ | ✓ | - | ✓ |
| Choice-75 | ✓ | ✓ | ✓ | - | ✓ |
| CosmosQA | - | ✓ | - | ✓ | ✓ |
| DROP | ✓ | - | ✓ | - | ✓ |
| HellaSwag | - | ✓ | ✓ | - | ✓ |
| LongBench | ✓ | - | - | ✓ | ✓ |
| NarrativeQA | ✓ | ✓ | - | ✓ | ✓ |
| OpenPI 2.0 | - | ✓ | ✓ | - | - |
| PASTA | - | ✓ | - | - | ✓ |
| PIQA | - | ✓ | ✓ | - | ✓ |
| TimeDial | ✓ | - | - | ✓ | - |
| TRACIE | ✓ | ✓ | - | - | - |
| UDST-DurationQA | ✓ | - | - | - | - |

### 转换后数据总量

| 数据集 | 样本数 | 输出目录 |
|--------|--------|----------|
| ATOMIC | 24,492 | converted_data_v2 |
| Choice-75 | 2,582 | converted_data_v2 |
| CosmosQA | 15,001 | converted_data_v3 |
| DROP | 13,530 | converted_data_v3 |
| HellaSwag | 30,000 | converted_data_v3 |
| LongBench | 4,900 | converted_data_v3 |
| NarrativeQA | 10,281 | converted_data_v3 |
| OpenPI 2.0 | 885 | converted_data_v3 |
| PASTA | 20,969 | converted_data_v3 |
| PIQA | 11,712 | converted_data_v3 |
| TimeDial | 5,660 | converted_data_v3 |
| TRACIE | 9,479 | converted_data_v3 |
| UDST-DurationQA | 20,870 | converted_data_v3 |
| **总计** | **160,882** | - |

