# TimeAware Benchmark 使用指南

## 概述

基于 `arich.md` 设计的统一时间推理评测框架，提供：

1. **统一的数据格式** (`task_schema.py`)
2. **数据集适配器** (`dataset_adapter.py`)
3. **五大任务生成器** (`task_generators.py`)
4. **三层评测模块** (`evaluation.py`)

---

## 快速开始

### 1. 转换数据集

```bash
python -m arch.main --convert-data
```

或使用Python代码：

```python
from arch import convert_all_datasets

samples = convert_all_datasets('data', 'output/arch/converted')
# 输出: 87192 samples converted
```

### 2. 运行评测

```bash
# 评测单个模型
python -m arch.main --evaluate --model gpt-4o-mini

# 多模型对比
python -m arch.main --compare
```

### 3. 生成新任务数据

```bash
# 生成所有任务
python -m arch.main --generate

# 生成指定任务
python -m arch.main --generate --task t1_temporal_calculation --num-samples 100
```

---

## 统一输入格式

```
[Context]
对话历史/上下文

[时间推进]
Δt (如 "3天", "2小时")

[事件]
事件描述

[问题]
Query
```

## 统一输出格式

```json
{
    "answer": "答案",
    "state": {"location": "...", "status": "..."},
    "reasoning": "推理过程"
}
```

---

## 五大任务

| 任务 | 编号 | 描述 | 评测指标 |
|------|------|------|----------|
| 时间计算 | T1 | Duration/Offset/Ordering | Accuracy, Step Accuracy |
| 状态更新 | T2 | 随时间更新世界状态 | Final Accuracy, State Accuracy, Consistency |
| 并发冲突 | T3 | 检测空间/资源/注意力冲突 | Conflict Detection Rate, Resolution Accuracy |
| 长期记忆 | T4 | 长上下文时间信息维持 | Retrieval Accuracy, Memory Consistency |
| 反事实 | T5 | 虚构规则下的推理 | Accuracy, Consistency |

---

## 三层评测模块

1. **Answer-level**: 答案正确性评测
2. **State-level**: 状态字段逐项评测
3. **Chain-level**: 多次回答一致性评测

---

## API 示例

### 加载和评测

```python
from arch import (
    load_converted_data, run_model_prediction, run_evaluation
)

# 加载数据
samples = load_converted_data('output/arch/converted/all_samples.json')

# 运行预测
predictions = run_model_prediction(samples, 'gpt-4o-mini')

# 运行评测
report = run_evaluation(samples, predictions, 'output/arch/eval_report.json')

# 打印报告
from arch import print_report
print_report(report)
```

### 自定义评测

```python
from arch import (
    TemporalSample, TaskType, DifficultyLevel,
    TemporalBenchmarkEvaluator
)

# 创建样本
sample = TemporalSample(
    id='test_001',
    task_type=TaskType.T1_TEMPORAL_CALCULATION,
    context='会议8点开始，持续1小时',
    query='什么时候结束？',
    answer='9点'
)

# 评测
evaluator = TemporalBenchmarkEvaluator()
results = evaluator.evaluate([sample], [{'answer': '9点'}])
print(results[0].answer_level_score)
```

---

## 目录结构

```
output/arch/
├── converted/           # 转换后的数据集
│   ├── all_samples.json
│   ├── mctaco.json
│   ├── timedial.json
│   └── ...
├── eval_gpt-4o-mini.json
└── generated_samples.json
```
