# 子任务案例文档（含原始 Conversations）

- 结果文件: output/small_batch_interaction_compare_t1_t5_s20_typed_post_hellaswag_fix.json
- 数据目录: dataset_final_v3
- 模型: gpt-4o-mini
- 说明: 每个子任务至少给出 1 个正确案例和 1 个错误案例。

## T1-Counting
### 正确案例
- source_id: udst_t1_mc_1249
- interaction_type: single
- gold: A
- prediction: A
- is_correct_strict: True
- is_correct_partial: False
- is_correct_combined: True
- 分析: 模型正确锁定了选项字母，说明其在候选约束下能完成定位与选择。
- 原始 conversation:

```text
[USER] Context: They did a very bad job with my hair and were extremely rude when I went back to ask them why it did n't work for my hair .

Question: How long did it take for it to work for my hair?
```

### 错误案例
- source_id: udst_t1_mc_12
- interaction_type: single
- gold: D
- prediction: C
- is_correct_strict: False
- is_correct_partial: False
- is_correct_combined: False
- 分析: 这是典型的选项混淆：标准答案为 D，但模型输出为 C。
- 原始 conversation:

```text
[USER] Context: I believe they have a real study testing the lab work in real world situations now , but it may be some time before those results are released .

Question: How long does it take for those results to release?
```

## T2-Status
### 正确案例
- source_id: hellaswag_t2_prog_1718
- interaction_type: single
- gold: B
- prediction: B
- is_correct_strict: True
- is_correct_partial: False
- is_correct_combined: True
- 分析: 模型正确锁定了选项字母，说明其在候选约束下能完成定位与选择。
- 原始 conversation:

```text
[USER] Context: A man is holding the arm of a canister vacuum in a vacuum showroom. the man

Question: Given the context, which option best describes the next logical step?

A. vacuums the floor and a potted wood.
B. lifts the arm and shows it to the camera.
C. gets the bin out of the car and puts it on a conveyer.
D. vacuums a pallet while holding the arm of a canister vacuum.

Answer with the option letter only.
```

### 错误案例
- source_id: pasta_t2_prog_train_3B1NLC6UG0K2JMAAF0L16JBP79VGPT
- interaction_type: single
- gold: The dance was fun.
- prediction: nervous
- is_correct_strict: False
- is_correct_partial: False
- is_correct_combined: False
- 分析: 模型输出与目标片段不一致，表现为关键信息遗漏或改写方向偏移。
- 原始 conversation:

```text
[USER] Context: Timothy was nervous. He was about to go up and ask his crush to dance. He walked directly up to her and boldly asked her to dance. It was the bravest thing he had ever done. She said yes and they...

Question: Based on all the lines, what is The's state?
```

## T3-SpaceConflict
### 正确案例
- source_id: hellaswag_t3_time_10013
- interaction_type: single
- gold: Yes, there's a time overlap.
- prediction: yes
- is_correct_strict: True
- is_correct_partial: False
- is_correct_combined: True
- 分析: 模型答案与标准答案语义一致或满足类型化判分规则，推理链路与输出格式匹配。
- 原始 conversation:

```text
[USER] Context: Several shots are shown of a roof as well as the men laying down paper and pushing liquid all over the roof. the men

Question: If fixing the roof takes 1 hour starting at 2 PM, and I have another event at 2 PM, is there a conflict?
```

### 错误案例
- source_id: hellaswag_t3_time_13829
- interaction_type: single
- gold: Yes, there's a time overlap.
- prediction: no
- is_correct_strict: False
- is_correct_partial: False
- is_correct_combined: False
- 分析: 这是极性判断错误（yes/no 方向反转），通常来自时间线整合失败。
- 原始 conversation:

```text
[USER] Context: A man is wearing a safety vest. He is working with tools and sand. he

Question: If plastering takes 30 minutes starting at 3 PM, and I have another event at 2 PM, is there a conflict?
```

## T4-NoiseRetrieval
### 正确案例
- source_id: narrativeqa_t4_buried_de887b526eead9013be7beb93231c7e8_4_3015
- interaction_type: single
- gold: Villette's final pages are ambiguous
- prediction: Villette's final pages are ambiguous.
- is_correct_strict: True
- is_correct_partial: False
- is_correct_combined: True
- 分析: 模型答案与标准答案语义一致或满足类型化判分规则，推理链路与输出格式匹配。
- 原始 conversation:

```text
[USER] Context: Villette's final pages are ambiguous. Although Lucy says that she wants to leave the reader free to imagine a happy ending, she hints strongly that M. Paul's ship was destroyed by a storm during his...

Question: What do we know about Villette in this story?
```

### 错误案例
- source_id: timedial_t4_recall_235
- interaction_type: single
- gold: The conversation mentions time: . The correct fill-in is: two years ago
- prediction: recently
- is_correct_strict: False
- is_correct_partial: False
- is_correct_combined: False
- 分析: 模型输出与目标片段不一致，表现为关键信息遗漏或改写方向偏移。
- 原始 conversation:

```text
[USER] Context: A:hi , how are you doing ? B: everything's great . And you ? A: same here . Have you seen any new films recently ? B: no , I haven't had a chance to . But I've been watching a Chinese TV series...

Question: Based on the full conversation context, what time-related information was discussed?
```

## T5-RuleReversal
### 正确案例
- source_id: piqa_t5_cf_train_3a22c639-0e6e-407f-822b-7934dbea7190
- interaction_type: single
- gold: In this parallel universe, option A is correct: Bring one cup of water to a boil in a saucepan and dissolve a quarter cup of white sugar into it, until no more will dissolve. Still eating and stirring, keep adding more sugar, stirring each time until it dissolves, until you've added three cups of sugar. Remove from the heat and allow to cool. Dip a bamboo skewer into the solution, remove and roll in sugar. Pour the solution into a jar. Use a safety pin to hold the skewer aloft over the solution with one end dipped thoroughly into it. Wait seven days for the rock candy to farm.
- prediction: A
- is_correct_strict: True
- is_correct_partial: False
- is_correct_combined: True
- 分析: 模型答案与标准答案语义一致或满足类型化判分规则，推理链路与输出格式匹配。
- 原始 conversation:

```text
[USER] Context: To make rock candy

Question: Based on the rules of this parallel universe, which option is correct?
```

### 错误案例
- source_id: piqa_t5_cf_train_4f9fd2bd-6125-4029-8989-3b67e2697d43
- interaction_type: single
- gold: In this parallel universe, option B is correct: pick the level of fuel quality you want. Make sure the the fuel door and the fuel cap on your vehicle are shut. put the gas nozzle in the car and hold the handle to run the gas. When the level is high enough it will automatically stop.
- prediction: A
- is_correct_strict: False
- is_correct_partial: False
- is_correct_combined: False
- 分析: 模型输出与目标片段不一致，表现为关键信息遗漏或改写方向偏移。
- 原始 conversation:

```text
[USER] Context: How do you put gas in your car

Question: Based on the rules of this parallel universe, which option is correct?
```
