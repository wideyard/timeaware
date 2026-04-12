# 22. TRIP 数据集说明

## 1. 数据集定位
- 任务类型：旅行规划结构化生成与评测
- 目录位置：data/TRIP
- README 来源：data/TRIP/README.md

## 2. 数据规模（基于仓库内可见文件）
- data/TRIP/postprocess/sample_evaluation_format.jsonl: 1
- 已统计主文件合计（非去重）：1

## 3. 数据样例
- 样例来源：data/TRIP/postprocess/sample_evaluation_format.jsonl

```text
{"idx": 1, "JSON": {"org": "Savannah", "dest": "Baltimore", "days": 3, "visiting_city_number": 1, "date": ["2024-11-18", "2024-11-19", "2024-11-20"], "people_number": 1, "local_constraint": {"house rule": null, "cuisine": null, "room type": null, "transportati ...
```

## 4. 数据构造方法
- 方法概述：基于用户画像、预算和约束生成多天行程，采用 JSON 结构对齐评测。
- README/文件线索：We introduce TripCraft, a spatiotemporally coherent travel planning dataset that integrates real world constraints, including public transit schedules, event availability, diverse attraction categories, and user personas for enhanced personalization. To evaluate LLM generated plans beyond existing binary validation methods, we propose five continuous evaluation metrics, namely Temporal Meal Score, Temporal Attraction Score, Spatial Score, Ordering Score, and Persona Score which assess itinerary quality across multiple dimensions.；## 🔓 Dataset Access；To get access to our dataset and auxiliary databases, please send a request to AcadGrants@service.microsoft.com and cc to *shreya[at]iitbbs.ac.in*, *abhikjana[at]iitbbs.ac.in*, *gmanish[at]microsoft.com* and *chaudhurisoumyabrata[at]gmail.com*.

## 5. 数据构造目的
- 目标：测试模型在多约束规划任务中的可执行性与偏好对齐能力。

## 6. 你在使用前需要注意
- 关键注意事项：当前可见样本主要在 postprocess 中，属于评测格式示例。
- README 摘要：<div align="center"> <h1 align="center">🧙‍♀️TripCraft🌍: A Benchmark for Spatio-Temporally Fine Grained Travel Planning【ACL'25 (Main)】</h1>
- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。