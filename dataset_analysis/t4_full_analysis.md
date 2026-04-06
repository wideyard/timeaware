# T4数据集完整分析报告

## 1. 对话长度问题统计

### 符合标准 (>1000字)
| 子维度 | 符合率 | 平均长度 | 截断问题 | 状态 |
|--------|--------|----------|----------|------|
| T4-Buried-Info | 100% | 11,731字 | 500条 | 需修复截断 |
| T4-Section-Nav | 100% | 7,486字 | 无 | ✓ OK |
| T4-T4-Detail | 99.8% | 1,081字 | 500条 | 需修复截断 |

### 需要扩展 (<1000字)
| 子维度 | 符合率 | 平均长度 | 需增加 | 截断问题 | 优先级 |
|--------|--------|----------|--------|----------|--------|
| T4-Noisy-Retrieval | 0% | 342字 | +658字 | 无 | 高 |
| T4-T4-Section | 0% | 388字 | +613字 | 无 | 高 |
| T4-Buried-Time | 0% | 395字 | +605字 | 500条 | 高 |
| T4-Process-Memory | 0.6% | 610字 | +390字 | 63条 | 中 |
| T4-Noise-Retrieval | 4% | 753字 | +247字 | 无 | 中 |
| T4-Convo-Cross | 0% | 821字 | +180字 | 100条 | 中 |
| T4-Convo-Recall | 25% | 863字 | +138字 | 256条 | 低 |
| T4-T4-Distractor | 0% | 883字 | +118字 | 无 | 低 |

## 2. 截断问题汇总

### 按来源分类

| 转换器 | 影响的子维度 | 截断类型 |
|--------|-------------|----------|
| cosmosqa_conversational_converter.py | T5-T5-Emotion, T4-Convo-Dialog, T2-T2-Tense | context[:200], context[:500] |
| narrativeqa_conversational_converter.py | T4-Convo-Cross, T4-T4-Detail, T4-T4-Buried | context截断 |
| timeqa_conversational_converter.py | T4-Buried-Time | conversation, answer截断 |
| qasper_conversational_converter.py | T4-Convo-Recall, T4-T4-Noise | context截断 |
| choice75_conversational_converter.py | T2-T2-Progressive | conversation截断 |
| uds_t_*_converter.py | T3-T3-Concurrent | conversation截断 |

### 关键发现

**CosmosQA转换器问题 (line 538, 573)**:
```python
# 截断问题
conversation.append({
    "role": "user",
    "content": f"Let me tell you about my experience. {context_first_person[:200]}..."
})
context=context[:500]  # Should be context=context[:2000] or full context
```

**NarrativeQA转换器问题**:
- Context被截断，导致故事不完整

## 3. 修复优先级

### 高优先级 (影响>100条)
1. **cosmosqa_conversational_converter.py** - 影响3个子维度，>1000条
2. **narrativeqa_conversational_converter.py** - 影响3个子维度，>4000条
3. **qasper_conversational_converter.py** - 影响2个子维度，>1200条

### 中优先级
4. **timeqa_conversational_converter.py** - 500条
5. **choice75_conversational_converter.py** - 527条

### 低优先级
6. **uds_t_converter.py** - 517条

## 4. 修复方案

### 方案A: 修改转换器并重新生成
- 修改 `context[:200]` → `context[:2000]`
- 修改 `context[:500]` → `context[:2000]`
- 重新运行所有转换器
- **预计时间**: 2-3小时

### 方案B: 直接修改已生成的JSONL
- 读取原始数据
- 替换截断的context/conversation/answer
- 保持其他字段不变
- **预计时间**: 1小时

### 方案C: 混合方案 (推荐)
1. 高影响转换器先修复 (cosmosqa, narrativeqa, qasper)
2. 其他数据集保留，标记为"需要修复"
3. 对于无法修复的数据，移除截断条目

## 5. T4 Multi-hop构造方案

### 数据来源
- T1-T1-Multihop.jsonl (500条) → 扩展成长对话

### 扩展方法
```python
原始短对话:
  user: "I started at 2:00 PM, then drove 23 minutes, then 38 more minutes."
  query: "When did I finish?"
  
扩展后长对话 (>1000字):
  user: "Let me tell you about my day..."
  assistant: "Please continue..."
  user: "I started by going to the store..." [噪声对话]
  assistant: "What happened next?"
  user: "By the way, the weather was nice..." [噪声对话]
  assistant: "I see. So about your schedule..." [噪声对话]
  user: "Actually, I forgot to mention..." [噪声对话]
  ...更多噪声对话...
  user: "Back to my schedule. I started at 2:00 PM..."
  query: "When did I finish?"
```

### 构造参数
- 原始数据: 500条 T1-Multihop
- 目标数据: 500条 T4-Multi-hop
- 对话长度: >1000字
- 噪声比例: 60-70%

## 6. 下一步行动

### 立即执行
1. 修复 cosmosqa_conversational_converter.py 的截断逻辑
2. 修复 narrativeqa_conversational_converter.py 的截断逻辑
3. 修复 qasper_conversational_converter.py 的截断逻辑
4. 重新生成 T4-Convo-Dialog, T4-Convo-Recall, T4-T4-Buried 等

### 后续执行
5. 构造 T4-Multi-hop 数据集
6. 扩展 T4 短对话数据集
7. 执行维度合并