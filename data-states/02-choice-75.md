# 02. choice-75 数据集说明

## 1. 数据集定位
- 任务类型：目标导向程序脚本分支选择与理由生成
- 目录位置：data/choice-75
- README 来源：data/choice-75/README.md, data/choice-75/data/choice-75/README.md

## 2. 整体结构
- `dataset_key.json`：存储从 `goal` 到 `split`（即数据集划分，如 `train`、`dev`、`test`）的映射关系；其中的 `goal` 字段取自 `proScript` 数据集（请注意，当前版本中暂未提供 `test` 集的数据标注）。
- `index_key.json`：存储从 `goal` 到索引编号的映射关系，该索引用于命名 `.json` 数据文件（例如：第1个脚本对应文件 `1.json`）。
- `user_profile`、`verb_phrase_manual`、`verb_phrase_machine`：存放具体数据文件的文件夹，按数据集划分（split）进行归类存放。

### 数据字段说明
- `goal`：取自 `proScript` 数据集的文本内容（字符串类型）。
- `steps`：步骤列表（字符串列表）。
- `original_index`：在 `proScript` 数据集中的原始索引编号。
- `index`：在本文件系统中的索引编号（例如，若该字段值为 5，则对应文件为 `5.json`）。
- `branching_info`：与决策分支相关的数据字段集合。
- `branching_step`：包含决策分支的那个步骤（文本内容）。
- `branching_idx`：`branching_step` 在原始 `steps` 列表中的索引位置。
- `option 1`、`option 2`：针对 `branching_step` 所提供的两个选项。
- `dataset`：该数据点所属的数据集划分（split）。
- `freeform_ra`：情境（scenarios）列表；列表中的每个情境数据点均包含以下三项信息：[情境描述文本, 正确选项（Ground Truth）, 难度等级]。

**注：** 您可以安全地忽略任何未在上述列表中列出的字段；这些字段与本项目当前阶段的研究内容无关。 
```
{
"goal": "在拉面店工作",
"steps": [
"决定在拉面店工作",
"撰写简历",
"撰写求职信",
"向拉面店提交简历和求职信",
"等待拉面店联系",
"前往参加面试",
"接受录用通知"
],
"original_index": 552,
"curr_index": 6157,
"index": 5,
"branching_info": {
"branching_idx": 3,
"branching_step": "向拉面店提交简历和求职信",
"option 1": "打印所有材料并亲自提交给拉面店",
"option 2": "在线提交简历和求职信",
"type": "golden",
"dataset": "dev",
"freeform_ra": [
[
"对该职位有额外疑问",
1,
"中等"
],
[
"没有打印机",
2,
"简单"
],
[
"住处离拉面店很远",
2,
"简单"
],
[
"想要给对方留下好印象",
1,
"中等"
],
[
"是日本文化的爱好者",
0,
"不适用"
]
]
}
}
```

## 3. 数据构造方法
- 方法概述：围绕日常 goal 构造步骤序列，在关键分歧点设置两个候选分支并标注 rationale（如 op1_ra/op2_ra）。
- README/文件线索：# Choice-75: A Dataset on Decision Branching in Script Learning；- Location: `/data/final_dataset/`；- `dataset`: dataset, could be `train`, `dev`, `test`

## 4. 数据构造目的
- 目标：评测模型在程序化计划中做分支决策、解释决策依据以及检索相关步骤的能力。