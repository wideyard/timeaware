针对你设计的 LLM 时间感知能力 Benchmark，结合 **LongBench** 的数据集特性，最适合承载的任务是 **T4（长期记忆）**，其次可以通过改造其 Synthetic 或 Multi-doc QA 任务来辅助实现 **T1（时间计算）**。

LongBench 的核心优势在于 **“长文本检索”** 和 **“抗干扰能力”**，这与你 T4 任务的需求高度匹配。以下是具体的适配分析及修改建议：

---

### 1. 最适配任务：T4 长期记忆 (Long-context Retrieval)

**适配理由：**
LongBench 的 `PassageRetrieval`（段落检索）和 `HotpotQA`（多文档问答）本质上就是在极长的上下文（5k-15k字）中寻找特定信息。你的 T4 任务需要测试模型在“10轮闲聊”后的记忆，在 LongBench 的量级下，这可以升级为“在 10,000 字的无关对话或文档后，找回最初的时间约定”。

**如何修改数据：**
* **构建 Context：** 采用 LongBench 的 `PassageRetrieval-zh/en` 模式。将“我周五有面试”作为 **Gold Paragraph（金句）** 插入到长文本的起始位置（Head）、中间（Middle）或末尾（Tail）。
* **干扰项：** 填充 5k-15k 字的无关文本（可以使用 LongBench 原有的 Wikipedia 段落）。
* **Question：** “根据上下文，我这周有什么重要安排？”
* **修改点：** 增加“时间噪音”。在干扰文本中加入大量虚假日期（如“他周三去游泳”、“下周二有聚会”），测试模型是否会产生 **Memory Decay** 或被近期的错误时间信息干扰。

---

### 2. 次适配任务：T1 时间计算 (Complex Reasoning)

**适配理由：**
LongBench 中的 `2WikiMultihopQA` 需要跨越多个段落进行推理。你可以将简单的 T1 任务升级为“跨文档时间链推理”。

**如何修改数据：**
* **构建 Context：** 参考 `2WikiMultihopQA` 的多跳逻辑。
    * 段落 A：我下午 3 点要参加一个由张三主持的会议。
    * 段落 B：张三主持的会议通常比常规时间长 1 小时，常规时间是 2 小时。
    * 中间填充 3000 字的其他项目报告。
* **Question：** “会议预计几点结束？”
* **测试目标：** 将 **Static Computation** 转化为 **Contextual Reasoning**，测试模型能否在长文本中提取时间参数并进行计算。

---

### 3. 不太适配但可借鉴的任务：T5 反事实 (Rule Perturbation)

**适配理由：**
LongBench 的 `LCC`（代码补全）和 `Synthetic` 任务对格式和规则有严格要求。

**如何修改数据：**
* **修改建议：** 利用 LongBench 的 `Few-shot` 模板（如 `SAMSum` 或 `TREC`）。
* **操作：** 在 Context 的开头给出 **System Prompt 级别的定义**：“在这个世界线，一小时等于 100 分钟”。然后紧接一个 LongBench 风格的长对话。
* **Question：** “如果我 1:00 开始运动，运动了 1.5 小时（即 150 分钟），现在是几点？”
* **修改点：** 考察模型在处理长文本时，是否会因为 **KV Cache 偏移** 或 **注意力的衰减** 而忘记了开头定义的“反事实规则”，退回到常识（一小时 60 分钟）进行回答。

---

### 总结：数据修改方案表

如果你想基于 LongBench 的格式（JSON）来封装你的 Benchmark，建议如下：

| 你的 Task | 对应的 LongBench 模板 | 修改动作 |
| :--- | :--- | :--- |
| **T1 时间计算** | `2WikiMultihopQA` | 将推理链条拆分到不同段落，加入无关文档干扰。 |
| **T2 状态更新** | `Single-doc QA` | 文本改写为日志格式，在末尾提问当前状态。 |
| **T3 并发冲突** | `MultiFieldQA` | 混合多份行程单，要求模型识别重叠的时间区间。 |
| **T4 长期记忆** | `PassageRetrieval` | **重点推荐**。将关键时间点埋在万字长文的随机位置。 |
| **T5 反事实** | `Few-shot (SAMSum)` | 在 Few-shot 示例中植入错误的时间逻辑法则。 |