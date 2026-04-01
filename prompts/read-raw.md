我想设计一个对话式评测llm的时间感知能力的benchmark，其中会有5个Task，包括：

每个 Task 都是 “上下文 + 单次预测”结构

T1：时间计算（静态 + 上下文干扰）

输入：
[Context]
今天是周一
我下午3点开会，持续2小时
[Question]
会议几点结束？
测：Duration, Offset, Ordering

T2：状态更新
[Context]
我3点开始开会
现在是4点
[Question]
我现在在做什么？
测：
状态推理（而不是记忆原句）
Location, Status 变化追踪

T3：并发冲突
[Context]
我3点到4点开会
我3点要去看电影
[Question]
这个安排合理吗？
测：
是否发现冲突（不是算数题）
Space Conflict, Resource Conflict

T4：长期记忆
[Context]
第1轮：我周五有面试
（中间10轮闲聊）
[Question]
我这周有什么重要安排？
测：
long-context retrieval
memory decay
跨长文本信息检索

T5：反事实（防数据污染）
[Context]
在这个世界中，水在50度沸腾
现在水是60度
[Question]
水会发生什么？
测：
是否遵守新规则
Rule Perturbation, 规则变换


以下是  数据集的简单介绍


下面是一个数据集样例:


告诉我这个数据集适合哪一种或者哪几种任务，应该怎么修改数据。


请阅读 data\tracie 目录下的所有文件，总结这个数据集的特征，要给出一些数据示例，保存到data-Interpretation目录下。