# 🧠 一、总体策略（核心思路）

> **把已有数据 → 映射到 Temporal World Modeling 框架**

---

## 🔄 三种改造方式（统一范式）

| 类型                   | 方法    | 用途    |
| -------------------- | ----- | ----- |
| 1. Temporalization   | 加时间维度 | T1/T2 |
| 2. State Structuring | 提取状态  | T2/T3 |
| 3. Rule Perturbation | 改规则   | T5    |

---

# 📦 二、按 Task 分类的数据集改造方案（重点）

---

# 🧪 T1：时间计算（Temporal Calculation）

---

## ✅ 可用数据集

### 1. TimeQA

* 本身就包含时间推理

---

### 2. DROP

* 包含数字/时间计算

---

## 🔧 改造方式

### 方法1：抽取时间表达

原始：

```text
John was born in 1990 and graduated in 2010.
```

改造：

```text
事件1：1990 出生  
事件2：2010 毕业  

问题：间隔多少年？
```

---

### 方法2：增加多步推理

👉 把单跳变成 multi-hop：

```text
A 在 B 之前 3 天  
B 在 C 之后 2 天  
问 A 和 C 的关系
```

---

## 🎯 用于

* T1-1 duration
* T1-2 offset
* T1-3 ordering

---

# 🧪 T2：状态更新（State Tracking）

---

## ✅ 可用数据集

### 1. ProPara

* 描述物理过程（状态变化）

---

### 2. TRIP

* 事件链 + 状态变化

---

## 🔧 改造方式

---

### 方法1：显式 State Matrix（关键升级）

原始：

```text
Mary went to the kitchen.
```

改造为：

```json
{
  "event": "Mary goes to kitchen",
  "state": {
    "Mary": {"location": "kitchen"}
  }
}
```

---

### 方法2：引入 Δt（时间间隔）

```text
8:00 Mary 在 kitchen  
8:30 去 garden  
```

---

### 方法3：增加干扰

* 插入无关句子（for T4）

---

## 🎯 用于

* T2 state tracking
* T2 consistency

---

# 🧪 T3：并发冲突（Concurrency）

---

## ✅ 可用数据集

### 1. SocialIQA

* 人类行为逻辑

---

### 2. ATOMIC

* 事件 → 结果关系

---

### 3. CosmosQA

* 常识推理

---

## 🔧 改造方式（核心）

---

### 方法1：构造冲突对

从 ATOMIC：

```text
X is at home  
X is at office
```

👉 自动生成：

```text
是否可能？
```

---

### 方法2：资源建模（升级点）

```text
会议室A被占用  
```

→ 转换为：

```json
"resource": "occupied"
```

---

### 方法3：组合冲突（高级）

* 空间 + 时间
* 人 + 资源

---

## 🎯 用于

* T3 conflict detection
* T3 resolution

---

# 🧪 T4：长期记忆（Long Context）

---

## ✅ 可用数据集

### 1. NarrativeQA

* 长故事

---

### 2. Qasper

* 长文档

---

### 3. LongBench

---

## 🔧 改造方式（关键）

---

### 方法1：插入时间事件

在长文本中：

```text
第1段：关键事件（时间）  
中间：大量噪声  
最后：问题  
```

---

### 方法2：时间跨度增强

* 早期事件 vs 当前问题

---

### 方法3：事件链抽取

把 narrative 转换为：

```text
event1 → event2 → event3
```

---

## 🎯 用于

* T4 retrieval
* T4 memory drift

---

# 🧪 T5：反事实（Counterfactual Sandbox）

---

## ✅ 可用数据集

### 1. PIQA

---

### 2. HellaSwag

---

### 3. Winogrande

---

## 🔧 改造方式（最关键创新）

---

### 方法1：规则替换

原始：

```text
水 100°C 沸腾
```

改造：

```text
在这个世界：
水 50°C 沸腾
```

---

### 方法2：因果链重写

```text
煮 10分钟 → 熟
```

改：

```text
煮 30分钟 → 熟
```

---

### 方法3：一致性测试

前后多次问同一规则

---

## 🎯 用于

* T5 reasoning vs memorization

---

# 三、统一Pipeline

---

## 🔧 数据构建流程

### Step 1：Dataset Selection

选原始数据集

### Step 2：Event Extraction

提取事件 + 时间

### Step 3：State Structuring

转为：

```json
S_t = (T_t, E_t, O_t)
```

---

### Step 4：Task Injection

根据 T1–T5：

* 加时间
* 加冲突
* 加噪声
* 改规则

---

### Step 5：Symbolic Verification

规则校验：

* 时间一致性
* 资源约束

