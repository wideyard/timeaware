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

### 3. OpenPI2.0 (Open Domain Procedural Text Entity Tracking)

* **来源**: [EACL 2024](https://aclanthology.org/2024.eacl-long.10/)
* **下载**: [GitHub - allenai/openpi-dataset](https://github.com/allenai/openpi-dataset)
* **规模**: 开放域过程文本实体追踪
* **特点**: 追踪实体的位置、状态、属性值变化，包含离散和连续状态标注

---

### 4. WIQA (What-If Question Answering)

* **来源**: [EMNLP 2019](https://aclanthology.org/D19-1629/)
* **下载**: [HuggingFace - allenai/wiqa](https://huggingface.co/datasets/allenai/wiqa)
* **规模**: 39,705 questions (train: 29,808 / dev: 6,894 / test: 3,003)
* **特点**: 测试"如果改变某个步骤会怎样"的反事实推理，包含扰动-效果链标注

---

### 5. proScript (Partially Ordered Scripts Generation)

* **来源**: [EMNLP 2021 Findings](https://aclanthology.org/2021.findings-emnlp.184/)
* **下载**: [proscript.allenai.org](https://proscript.allenai.org/)
* **规模**:6,400+ crowdsourced partially ordered scripts
* **特点**: 脚本生成、边预测任务，覆盖日常场景（烹饪、洗衣、装配等）

---

### 6. Choice-75 (Decision Branching in Script Learning)

* **来源**: [LREC-COLING 2024](https://aclanthology.org/2024.lrec-main.285/)
* **特点**: 专注于脚本学习中的决策分支，研究选择如何影响后续步骤

---

### 7. bAbI Tasks (Task 1-6)

* **来源**: [Facebook AI Research](https://research.fb.com/downloads/babi/)
* **下载**: HuggingFace `facebook/babi`
* **规模**: 20个任务，Task 1-6 涉及状态追踪
* **特点**: 合成数据，适合作为 T2 基础数据集

---

### 8. RecipeQA (Recipe Question Answering)

* **来源**: [EMNLP 2018](https://aclanthology.org/D18-1509/)
* **下载**: [recipeqa.ai2.com](https://recipeqa.ai2.com/)
* **规模**: 36,862 questions over 20,833 recipes
* **特点**: 烹饪过程状态变化，多模态问答

---

### 9. PASTA (Participant States in Narratives)

* **来源**: [TACL 2023](https://arxiv.org/abs/2208.00329)
* **下载**: [GitHub: StonyBrookNLP/pasta](https://github.com/StonyBrookNLP/pasta)
* **规模**: ~10,000+ 叙事文本
* **特点**: 追踪叙事中参与者的状态变化，适合 T2 状态建模

---

### 10. Ingredient States Recipe Dataset (2025)

* **来源**: [arXiv 2507.17232](https://arxiv.org/abs/2507.17232)
* **特点**: 高质量食谱数据集，原生状态标注，非常适合改造为 T2

---

### 11. StateAct (State Tracking for Planning)

* **来源**: [arXiv 2410.02810](https://arxiv.org/abs/2410.02810v2/)
* **特点**: LLM 状态追踪与规划，适合改造为 T2

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

---

# 四、T2 数据集汇总表（新增）

---

## 📊 数据集对比

| 数据集 | 任务类型 | 数据规模 | T2 契合度 | 来源 |
|--------|---------|---------|----------|------|
| **ProPara** | 状态追踪 | ~500 processes | ⭐⭐⭐⭐⭐ | AI2 |
| **TRIP** | 状态变化 | 需申请 | ⭐⭐⭐⭐⭐ | Microsoft |
| **situated_gen** | 情境生成 | 5,641 samples | ⭐⭐⭐⭐ | Allen AI |
| **OpenPI2.0** | 实体追踪 | 开放域 | ⭐⭐⭐⭐⭐ | AI2 |
| **WIQA** | 过程推理 | 39,705 questions | ⭐⭐⭐⭐⭐ | AI2 |
| **proScript** | 脚本生成 | 6,400+ scripts | ⭐⭐⭐⭐⭐ | CMU/AI2 |
| **Choice-75** | 决策分支 | 75 scenarios | ⭐⭐⭐⭐ | LREC 2024 |
| **bAbI (Task 1-6)** | 基础推理 | 合成数据 | ⭐⭐⭐ | FAIR |
| **RecipeQA** | 烹饪过程 | 36,862 questions | ⭐⭐⭐⭐ | EMNLP 2018 |
| **PASTA** | 叙事状态 | 10,000+ narratives | ⭐⭐⭐⭐⭐ | Stony Brook |
| **Ingredient States** | 食谱状态 | 高质量标注 | ⭐⭐⭐⭐⭐ | Tokyo 2025 |
| **StateAct** | 状态规划 | LLM 状态追踪 | ⭐⭐⭐⭐ | arXiv 2024 |

---

## 🔗 下载链接汇总

| 数据集 | HuggingFace / GitHub |
|--------|---------------------|
| OpenPI2.0 | [github.com/allenai/openpi-dataset](https://github.com/allenai/openpi-dataset) |
| WIQA | [huggingface.co/datasets/allenai/wiqa](https://huggingface.co/datasets/allenai/wiqa) |
| proScript | [proscript.allenai.org](https://proscript.allenai.org/) |
| PASTA | [github.com/StonyBrookNLP/pasta](https://github.com/StonyBrookNLP/pasta) |
| bAbI | [huggingface.co/datasets/facebook/babi_qa](https://huggingface.co/datasets/facebook/babi_qa) |
| ProPara | [github.com/allenai/propara](https://github.com/allenai/propara) |
| Choice-75 | [github.com/JoeyHou/choice-75](https://github.com/JoeyHou/choice-75) |
| bAbI | [huggingface.co/datasets/facebook/babi](https://huggingface.co/datasets/facebook/babi) |
| RecipeQA | [recipeqa.ai2.com](https://recipeqa.ai2.com/) |
| ProPara | [github.com/allenai/propara](https://github.com/allenai/propara) |

---

## 🎯 推荐组合

| 研究方向 | 推荐数据集组合 |
|---------|---------------|
| **实体状态追踪** | ProPara + OpenPI2.0 |
| **过程推理** | WIQA + proScript |
| **脚本学习** | proScript + Choice-75 |
| **基础能力测试** | bAbI (Task 1-6) |
| **多模态过程理解** | RecipeQA |

---

## ⚠️ 注意事项

1. **TRIP 数据集**: 需向 Microsoft 申请访问权限
2. **OpenPI2.0**: 为 OpenPI 的改进版，推荐使用最新版本
3. **bAbI**: 合成数据，仅适合作为基础测试集
4. **proScript**: 部分有序脚本，适合复杂过程建模

---

*文档更新时间: 2026-03-30*

