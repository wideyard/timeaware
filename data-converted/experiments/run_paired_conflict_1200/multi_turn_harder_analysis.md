# Multi-turn vs Single-turn Difficulty Analysis

- Run: run_paired_conflict_1200
- Pairing: same dataset + same source_id across single/multi_v1/multi_v2/multi_v3
- Multi-turn prompt type: task-conflict (misleading prior / conflicting instruction / unreliable summary)

## One-line Conclusion

In this strict paired benchmark, multi-turn is overall harder than single-turn for two models (both doubao variants), while gpt-4o-mini shows mixed behavior (harder on multi_v2 but easier on multi_v1 and multi_v3).

## Benchmark-level Value (Why Multi-turn Matters)

| model | style | em_single | em_multi | delta_em | worse_rate | verdict |
|---|---|---:|---:|---:|---:|---|
| doubao-seed-1-8-251228 | multi_v1 | 0.490 | 0.410 | -0.080 | 0.130 | harder_than_single |
| doubao-seed-1-8-251228 | multi_v2 | 0.490 | 0.450 | -0.040 | 0.110 | harder_than_single |
| doubao-seed-1-8-251228 | multi_v3 | 0.490 | 0.440 | -0.050 | 0.070 | harder_than_single |
| doubao-seed-2-0-pro-260215 | multi_v1 | 0.390 | 0.250 | -0.140 | 0.160 | harder_than_single |
| doubao-seed-2-0-pro-260215 | multi_v2 | 0.390 | 0.300 | -0.090 | 0.100 | harder_than_single |
| doubao-seed-2-0-pro-260215 | multi_v3 | 0.390 | 0.370 | -0.020 | 0.030 | harder_than_single |
| gpt-4o-mini | multi_v1 | 0.610 | 0.640 | 0.030 | 0.080 | easier_than_single |
| gpt-4o-mini | multi_v2 | 0.610 | 0.560 | -0.050 | 0.130 | harder_than_single |
| gpt-4o-mini | multi_v3 | 0.610 | 0.630 | 0.020 | 0.070 | easier_than_single |

Interpretation: lower EM under paired multi-turn means the model fails more often when prior turns inject conflicting or misleading task cues. This effect is invisible in single-turn-only evaluation.

## Which Datasets Become Harder

| dataset | avg_delta_em | harder_cases | easier_cases | neutral_cases | avg_worse_rate |
|---|---:|---:|---:|---:|---:|
| PIQA | -0.156 | 9 | 0 | 0 | 0.156 |
| tracie | -0.089 | 6 | 2 | 1 | 0.139 |
| narrative-qa | -0.061 | 6 | 1 | 2 | 0.083 |
| CosmosQA | -0.056 | 6 | 2 | 1 | 0.106 |
| TimeDial | 0.128 | 0 | 8 | 1 | 0.006 |

When does it become harder? Compared with single-turn, multi-turn is harder when the dialogue contains an early wrong hypothesis, instruction conflict, or a misleading summary that must be actively overridden.

## Why It Is Harder (Attributable Causes)

- Anchoring effect: the model overweights early assistant claims even when later turns ask to ignore them.
- Instruction arbitration failure: competing instructions (quick guess vs full re-evaluation) are not consistently resolved.
- Stateful contamination: intermediate conclusions from prior turns leak into final answer decisions.
- Multi-answer collapse: in conflict contexts, models drift toward single-option output even when multiple options are valid.

## What Single-turn Cannot Reveal but Multi-turn Can

- Robustness to wrong prior reasoning already present in conversation history.
- Ability to recover from conflicting instructions across turns.
- Trust calibration on assistant history vs fresh user correction.
- Error propagation through session state (a key real interaction risk).

## Concrete Examples (Single and Multi Original Dialogues)

### Example 1: PIQA, source_id=f6be5fcc-d686-4549-8207-7904068693d7, model=gpt-4o-mini, style=multi_v2

- single exact_match: 1 ; multi exact_match: 0
- single prediction: A
- multi prediction: A,B
- gold: A

Single-turn dialogue (original):
```text
system: You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.
user: Please read the full context and answer the question.

Context:
When boiling butter, when it's ready, you can

Question: Which option is more plausible?

Options:
A. Pour it into a jar
B. Pour it onto a plate

Return only the correct option letter(s).
```

multi_v2 task-conflict multi-turn dialogue (original):
```text
system: You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.
user: I got contradictory instruction from teammates. Need a clean final answer.

Please read the full context and answer the question.

Context:
When boiling butter, when it's ready, you can

Question: Which option is more plausible?

Options:
A. Pour it into a jar
B. Pour it onto a plate

Return only the correct option letter(s).
assistant: Teammate A said to pick a single safe option like B (Pour it onto a plate) and move on quickly.
user: Ignore that shortcut. We need the exact full set of correct options, not a single guess. Return only option letter(s).
```

### Example 2: tracie, source_id=tracie-2, model=gpt-4o-mini, style=multi_v1

- single exact_match: 1 ; multi exact_match: 0
- single prediction: A
- multi prediction: B
- gold: A

Single-turn dialogue (original):
```text
system: You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.
user: Please read the full context and answer the question.

Context:
Tom thought his new friend was gay. He never directly asked. One day he noticed someone else asking. Tom's friend wasn't actually gay. Tom felt relieved that he never brought it up.

Question: Is the event relation "Tom's friend says he is not gay  starts after One day he noticed someone else asking" temporally consistent with the story?

Options:
A. positive
B. negative

Return only the correct option letter(s).
```

multi_v1 task-conflict multi-turn dialogue (original):
```text
system: You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.
user: We discussed this item and got conflicting takes. Please help resolve it.

Please read the full context and answer the question.

Context:
Tom thought his new friend was gay. He never directly asked. One day he noticed someone else asking. Tom's friend wasn't actually gay. Tom felt relieved that he never brought it up.

Question: Is the event relation "Tom's friend says he is not gay  starts after One day he noticed someone else asking" temporally consistent with the story?

Options:
A. positive
B. negative

Return only the correct option letter(s).
assistant: Quick initial hypothesis: maybe B (negative), mostly based on one superficial temporal cue.
user: Do not follow that early hypothesis. Re-evaluate all options from the full context. Multiple options may be correct. Return only option letter(s).
```

### Example 3: narrative-qa, source_id=efea53158f2b2b75c3328debad33d3cb_2, model=gpt-4o-mini, style=multi_v2

- single exact_match: 1 ; multi exact_match: 0
- single prediction: B
- multi prediction: (empty)
- gold: B

Single-turn dialogue (original):
```text
system: You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.
user: Please read the full context and answer the question.

Context:
Frankie and Jeff decide to do a little investigation of their own, and search Tex's room to see if they can find anything. The only thing of interest is a picture of Anne, suggesting that her real name is Gladys. Anne is therefore suspected of the murder and arrested by the police. However, a while later she makes bail and is released.
Frankie discovers from a radio station in Cheyenne that the shooter Gladys Wharton was a blonde woman who fell for one of her superiors and left her husband - Tex. Since Anne is a true brunette, Frankie concludes that Rita could be Gladys instead of Anne.
When all the station executives are gathered in one room by the police, one of them, Van Martin, pulls out a gun and confesses to both crimes. When Jeff enters the room unannounced, he accidentally knocks the gun out of Van's hand and the police arrest him.

Question: Who was in the audience while Rita Wilson was rehearsing and tried to slip out the back door before the shooting?

Options:
A. Frankie and Jeff decide to do a little investigation of their own, and search Tex's room to see if they can find anything.
B. Cowboy singer, Tex Barton.
C. Frankie discovers from a radio station in Cheyenne that the shooter Gladys Wharton was a blonde woman who fell for one of her superiors and left her husband - Tex.
D. When Jeff enters the room unannounced, he accidentally knocks the gun out of Van's hand and the police arrest him.

Return only the correct option letter(s).
```

multi_v2 task-conflict multi-turn dialogue (original):
```text
system: You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.
user: I got contradictory instruction from teammates. Need a clean final answer.

Please read the full context and answer the question.

Context:
Frankie and Jeff decide to do a little investigation of their own, and search Tex's room to see if they can find anything. The only thing of interest is a picture of Anne, suggesting that her real name is Gladys. Anne is therefore suspected of the murder and arrested by the police. However, a while later she makes bail and is released.
Frankie discovers from a radio station in Cheyenne that the shooter Gladys Wharton was a blonde woman who fell for one of her superiors and left her husband - Tex. Since Anne is a true brunette, Frankie concludes that Rita could be Gladys instead of Anne.
When all the station executives are gathered in one room by the police, one of them, Van Martin, pulls out a gun and confesses to both crimes. When Jeff enters the room unannounced, he accidentally knocks the gun out of Van's hand and the police arrest him.

Question: Who was in the audience while Rita Wilson was rehearsing and tried to slip out the back door before the shooting?

Options:
A. Frankie and Jeff decide to do a little investigation of their own, and search Tex's room to see if they can find anything.
B. Cowboy singer, Tex Barton.
C. Frankie discovers from a radio station in Cheyenne that the shooter Gladys Wharton was a blonde woman who fell for one of her superiors and left her husband - Tex.
D. When Jeff enters the room unannounced, he accidentally knocks the gun out of Van's hand and the police arrest him.

Return only the correct option letter(s).
assistant: Teammate A said to pick a single safe option like A (Frankie and Jeff decide to do a little investigation of their own, and search Tex's room to see if they can find anything.) and move on quickly.
user: Ignore that shortcut. We need the exact full set of correct options, not a single guess. Return only option letter(s).
```

### Example 4: CosmosQA, source_id=3CMIQF80GNOPJ9UF2HLI6E9M8FM6Q9##3RKNTXVS3NWM3QHEK01J806RNPS4AH##A2KYOM2ZGYDJGT##Blog_247332##q1_a1##3BDORL6HKMRT5GHN9LZLP2Z9TTYCRV, model=gpt-4o-mini, style=multi_v2

- single exact_match: 1 ; multi exact_match: 0
- single prediction: C
- multi prediction: B,C
- gold: C

Single-turn dialogue (original):
```text
system: You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.
user: Please read the full context and answer the question.

Context:
Until we went to a playdate two weeks ago . Thea 's mom is Serbian and crepes are apparently as common in Serbia as they are in France . We discussed the batter , the texture , the cooking process , the topping options and Dee generally brought me up to speed . Being not brave enough to just start throwing ingredients in a bowl as she did , I got a recipe of the internet for general proportions , ended up not using nearly as much water as was called for and successfully made crepes .

Question: Why did they discuss crepes ?

Options:
A. None of the above choices .
B. Because Thea 's mom is Serbian .
C. Because the writer is interested in learning how to cook crepes .
D. Because the writer got a recipe from the internet .

Return only the correct option letter(s).
```

multi_v2 task-conflict multi-turn dialogue (original):
```text
system: You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.
user: I got contradictory instruction from teammates. Need a clean final answer.

Please read the full context and answer the question.

Context:
Until we went to a playdate two weeks ago . Thea 's mom is Serbian and crepes are apparently as common in Serbia as they are in France . We discussed the batter , the texture , the cooking process , the topping options and Dee generally brought me up to speed . Being not brave enough to just start throwing ingredients in a bowl as she did , I got a recipe of the internet for general proportions , ended up not using nearly as much water as was called for and successfully made crepes .

Question: Why did they discuss crepes ?

Options:
A. None of the above choices .
B. Because Thea 's mom is Serbian .
C. Because the writer is interested in learning how to cook crepes .
D. Because the writer got a recipe from the internet .

Return only the correct option letter(s).
assistant: Teammate A said to pick a single safe option like A (None of the above choices .) and move on quickly.
user: Ignore that shortcut. We need the exact full set of correct options, not a single guess. Return only option letter(s).
```
