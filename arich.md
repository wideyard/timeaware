# 一、总体实验框架（先统一范式）

所有实验统一遵循：

### 输入形式（统一）

```
[Context / 对话历史]
[时间推进 Δt]
[事件 a_t]
[问题 Query]
```

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

---

## 🟠 Level 2：Cross-cutting Analysis（横向分析）

* Steps scaling
* Context length
* Consistency
* Error propagation

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

