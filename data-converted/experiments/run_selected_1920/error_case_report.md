# Multi-turn Error Examples Report

- run: run_selected_1920
- note: some datasets shuffle option letters across styles, so gold_keys are shown per style

## Categories

- single->multi: single correct but one or more multi styles wrong
- style-specific: only one multi style fails while other multi styles pass
- multi-help: single wrong but some multi style(s) correct

## Example 1 [single->multi]

- model: gpt-4o-mini
- group/dataset: TimeDial / TimeDial (full)
- source_id: 779
- highlighted styles: multi_v1, multi_v2, multi_v3

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 1 | A,C | A,C | no |
| multi_v1 | 0 | A,B,C,D | C,D | no |
| multi_v2 | 0 | B | B,D | no |
| multi_v3 | 0 | A,C,D | B,D | no |

Prompt cue snippets (first user turn):
```text
single  : Please read the full context and answer the question.  Context: A:Hi , Juliet , I'm treating Mr.Li and his team members from Galp to dinner tomorrow evening.Where do you think I should take them ? B: Well , Mr.Li has very good taste in wine , and Galp is one o
multi_v1: I just missed my bus and I am stuck waiting. Want to help me think through a question?
multi_v2: I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.
multi_v3: I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?
```

## Example 2 [single->multi]

- model: gpt-4o-mini
- group/dataset: TimeDial / TimeDial (full)
- source_id: 1147
- highlighted styles: multi_v1, multi_v2, multi_v3

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 1 | A,C | A,C | no |
| multi_v1 | 0 | A,B,C,D | C,D | no |
| multi_v2 | 0 | C | C,D | no |
| multi_v3 | 0 | A | A,B | no |

Prompt cue snippets (first user turn):
```text
single  : Please read the full context and answer the question.  Context: A:Hi , Anna . I haven ' t seen you for ages . Where have you been ? B: I ' Ve been away on holidays for sometime . A: No wonder I haven ' t seen you recently . Where did you spend your holidays ? 
multi_v1: I just missed my bus and I am stuck waiting. Want to help me think through a question?
multi_v2: I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.
multi_v3: I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?
```

## Example 3 [single->multi]

- model: gpt-4o-mini
- group/dataset: TimeDial / TimeDial (full)
- source_id: 1038
- highlighted styles: multi_v1, multi_v2, multi_v3

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 1 | A,B | A,B | no |
| multi_v1 | 0 | (empty) | A,B | yes |
| multi_v2 | 0 | (empty) | B,D | yes |
| multi_v3 | 0 | A,B,C,D | A,D | no |

Prompt cue snippets (first user turn):
```text
single  : Please read the full context and answer the question.  Context: A:How come it is slow as a snail today ? B: You mean the network connection ? A: Yes , I wanted to look for some information on the company page just now . It took me almost <MASK> to open it . Th
multi_v1: I just missed my bus and I am stuck waiting. Want to help me think through a question?
multi_v2: I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.
multi_v3: I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?
```

## Example 4 [single->multi]

- model: gpt-4o-mini
- group/dataset: SocialIQA / SocialIQA (full)
- source_id: siqa-4872
- highlighted styles: multi_v1, multi_v2, multi_v3

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 1 | B | B | no |
| multi_v1 | 0 | A,C | B | no |
| multi_v2 | 0 | C | A | no |
| multi_v3 | 0 | A,C | A | no |

Prompt cue snippets (first user turn):
```text
single  : Please read the full context and answer the question.  Context: The food at the wedding was spectacular, with many complicated and delicious dishes, and all the guest agreed that Bailey was a good cook.  Question: How would Others feel as a result?  Options: A
multi_v1: I just missed my bus and I am stuck waiting. Want to help me think through a question?
multi_v2: I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.
multi_v3: I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?
```

## Example 5 [single->multi]

- model: gpt-4o-mini
- group/dataset: SI-Bench / SI-Bench (full)
- source_id: 1739
- highlighted styles: multi_v1, multi_v2, multi_v3

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 1 | B | B | no |
| multi_v1 | 0 | A,B | B | no |
| multi_v2 | 0 | B | A | no |
| multi_v3 | 0 | B,C | A | no |

Prompt cue snippets (first user turn):
```text
single  : 请阅读下面原文并回答问题。  原文： 用户: 在干嘛呢？ 用户: 下班了吗？ 对方: 嗯 对方: 刚刚下班 用户: 辛苦了，我们什么时候能见见呢？ 对方: 见我干嘛  问题：该对话最符合哪类场景标签？  选项： A. 暗示 B. 反制主导 C. 真实性测试 D. 含糊其辞  请只输出正确选项字母（可多选）。
multi_v1: 我在等公交，风有点大，刚错过一班车。正好和你聊个题。
multi_v2: 我在餐厅点餐，周围有点吵。我们边聊边做一道题。
multi_v3: 我刚导航走错路，现在停在路边重新规划。等我两秒，想请你做道题。
```

## Example 6 [single->multi]

- model: gpt-4o-mini
- group/dataset: DROP / DROP (full)
- source_id: 8b92ddf8-a859-4510-8860-0d40c9c25672
- highlighted styles: multi_v1, multi_v2, multi_v3

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 1 | C | C | no |
| multi_v1 | 0 | A,B,C,D | B | no |
| multi_v2 | 0 | B | A | no |
| multi_v3 | 0 | A,B,C,D | B | no |

Prompt cue snippets (first user turn):
```text
single  : Please read the full context and answer the question.  Context: the total number of full-time equivalent jobs was 15,215. The number of jobs in the primary sector was 1,157, of which 1,052 were in agriculture and 105 were in forestry or lumber production. The 
multi_v1: I just missed my bus and I am stuck waiting. Want to help me think through a question?
multi_v2: I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.
multi_v3: I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?
```

## Example 7 [style-specific]

- model: doubao-seed-1-8-251228
- group/dataset: CosmosQA / CosmosQA (full)
- source_id: 37ZQELHEQ2CLZ41MT3CIJEZBLRAMNT##3Y9N9SS8L1QEEQ0TOTZ2GUA0WWBD3K##A2SUGF86KLTZB6##Blog_203497##q2_a1##3X0EMNLXER34SC78NAQ1AZNJDF1VPQ
- highlighted styles: multi_v1

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 1 | A | A | no |
| multi_v1 | 0 | (empty) | A | yes |
| multi_v2 | 1 | C | C | no |
| multi_v3 | 1 | D | D | no |

Prompt cue snippets (first user turn):
```text
single  : Please read the full context and answer the question.  Context: So I got a call a couple days ago from the assistant dean of admissions for the Flora Thorntan School of Music at USC , personally calling me to talk about financial aid and my admission to USC . 
multi_v1: I just missed my bus and I am stuck waiting. Want to help me think through a question?
multi_v2: I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.
multi_v3: I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?
```

## Example 8 [style-specific]

- model: doubao-seed-1-8-251228
- group/dataset: DROP / DROP (full)
- source_id: 4d269e06-3e8e-4212-927d-23c999aac84b
- highlighted styles: multi_v1

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 1 | C | C | no |
| multi_v1 | 0 | (empty) | C | yes |
| multi_v2 | 1 | B | B | no |
| multi_v3 | 1 | D | D | no |

Prompt cue snippets (first user turn):
```text
single  : Please read the full context and answer the question.  Context: Coming off an impressive home win over the Buccaneers, the Lions flew to Soldier Field for Round 2 of their NFC North duel with the Chicago Bears.  After a scoreless first quarter, Detroit jumped 
multi_v1: I just missed my bus and I am stuck waiting. Want to help me think through a question?
multi_v2: I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.
multi_v3: I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?
```

## Example 9 [style-specific]

- model: doubao-seed-2-0-pro-260215
- group/dataset: TempReason_T1 / TempReason (full)
- source_id: 334345
- highlighted styles: multi_v1

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 1 | C | C | no |
| multi_v1 | 0 | (empty) | D | yes |
| multi_v2 | 1 | D | D | no |
| multi_v3 | 1 | B | B | no |

Prompt cue snippets (first user turn):
```text
single  : Please read the full context and answer the question.  Context: Reference date: November 12, 1839  Question: What is the time 6 year and 3 month before Nov, 1839  Options: A. Apr, 1146 B. Jul, 1283 C. Aug, 1833 D. Jul, 1804  Return only the correct option lett
multi_v1: I just missed my bus and I am stuck waiting. Want to help me think through a question?
multi_v2: I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.
multi_v3: I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?
```

## Example 10 [style-specific]

- model: gpt-4o-mini
- group/dataset: CosmosQA / CosmosQA (full)
- source_id: 3BAKUKE49HAUOO8I9QY1G8SAWEF1RQ##3QEMNNSB2YXHKK2968QS1DY7X7GD71##A3VVR8NR3ED04C##Blog_1133397##q1_a2##3X0EMNLXER34SC78NAQ1AZNJD9PPVW
- highlighted styles: multi_v1

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 1 | D | D | no |
| multi_v1 | 0 | (empty) | B | yes |
| multi_v2 | 1 | B | B | no |
| multi_v3 | 1 | A | A | no |

Prompt cue snippets (first user turn):
```text
single  : Please read the full context and answer the question.  Context: A few days ago we had the ceremony of the first tomato . I lost all my tomato plants to blight last year , so it was a relief to have our first tomato no matter how small . However , it looks like
multi_v1: I just missed my bus and I am stuck waiting. Want to help me think through a question?
multi_v2: I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.
multi_v3: I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?
```

## Example 11 [multi-help]

- model: gpt-4o-mini
- group/dataset: CosmosQA / CosmosQA (full)
- source_id: 37ZQELHEQ2CLZ41MT3CIJEZBLRAMNT##3Y9N9SS8L1QEEQ0TOTZ2GUA0WWBD3K##A2SUGF86KLTZB6##Blog_203497##q2_a1##3X0EMNLXER34SC78NAQ1AZNJDF1VPQ
- highlighted styles: multi_v1, multi_v2, multi_v3

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 0 | (empty) | A | yes |
| multi_v1 | 1 | A | A | no |
| multi_v2 | 1 | C | C | no |
| multi_v3 | 1 | D | D | no |

Prompt cue snippets (first user turn):
```text
single  : Please read the full context and answer the question.  Context: So I got a call a couple days ago from the assistant dean of admissions for the Flora Thorntan School of Music at USC , personally calling me to talk about financial aid and my admission to USC . 
multi_v1: I just missed my bus and I am stuck waiting. Want to help me think through a question?
multi_v2: I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.
multi_v3: I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?
```

## Example 12 [multi-help]

- model: gpt-4o-mini
- group/dataset: CosmosQA / CosmosQA (full)
- source_id: 35F6NGNVM8HLFP0C2VK5HXK5M2DT7Q##3WS1NTTKEZA00TGLCF09AYR5YMC0FE##APRZ7BR8C0ZMQ##Blog_1475689##q1_a2##3PMR2DOWOOZMB073Z140B5UHG0I45E
- highlighted styles: multi_v1, multi_v2, multi_v3

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 0 | (empty) | A | yes |
| multi_v1 | 1 | A | A | no |
| multi_v2 | 1 | C | C | no |
| multi_v3 | 1 | C | C | no |

Prompt cue snippets (first user turn):
```text
single  : Please read the full context and answer the question.  Context: The game had become more and more fascinating as time wore on and Gojyo knew , although he would not admit it verbally , that it was because of the attraction . Denial aside he nonetheless loved s
multi_v1: I just missed my bus and I am stuck waiting. Want to help me think through a question?
multi_v2: I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.
multi_v3: I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?
```

## Example 13 [multi-help]

- model: doubao-seed-2-0-pro-260215
- group/dataset: TempReason_T1 / TempReason (full)
- source_id: 392287
- highlighted styles: multi_v1, multi_v2, multi_v3

| style | exact_match | prediction_keys | gold_keys | error |
|---|---:|---|---|---|
| single | 0 | (empty) | B | yes |
| multi_v1 | 1 | B | B | no |
| multi_v2 | 1 | C | C | no |
| multi_v3 | 1 | B | B | no |

Prompt cue snippets (first user turn):
```text
single  : Please read the full context and answer the question.  Context: Reference date: January 27, 1600  Question: What is the time 10 year and 1 month before Jan, 1600  Options: A. Dec, 1858 B. Dec, 1589 C. Jul, 1925 D. Jul, 1054  Return only the correct option lett
multi_v1: I just missed my bus and I am stuck waiting. Want to help me think through a question?
multi_v2: I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.
multi_v3: I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?
```
