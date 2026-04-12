import json
import csv
import re
import random
import hashlib
import argparse
from pathlib import Path

ROOT = Path('.')
DATA = ROOT / 'data'
OUT = ROOT / 'data-converted'
SEED = 42

parser = argparse.ArgumentParser()
parser.add_argument('--full', action='store_true', help='Run full conversion instead of 100-sample conversion')
args = parser.parse_args()

RUN_MODE = 'full' if args.full else 'sample'
SAMPLE_N = 10**9 if RUN_MODE == 'full' else 100

ALL_DATASETS = [
    'ATOMIC','choice-75','CosmosQA','DROP','HellaSwag','LongBench','MCTACO','narrative-qa','OpenPI2.0','pasta','PIQA','ProPara','qasper','SI-Bench','situated_gen','SocialIQA','TempReason','TimeDial','TimeQA','tracie','TRaVelER','TRIP','UDS_T_v1.0','UDST-DurationQA','winogrande'
]

TASK_MAP = {
    'CosmosQA': 'T4',
    'DROP': 'T4',
    'HellaSwag': 'T2',
    'MCTACO': 'T1',
    'narrative-qa': 'T4',
    'pasta': 'T2',
    'PIQA': 'T2',
    'qasper': 'T4',
    'SI-Bench': 'T4',
    'SocialIQA': 'T4',
    'TempReason': 'T1',
    'TimeDial': 'T1',
    'TimeQA': 'T1',
    'tracie': 'T3',
    'UDST-DurationQA': 'T1'
}

SKIP_REASON = {
    'ATOMIC': '根据你的要求，ATOMIC 不进行改造。',
    'choice-75': '主标注文件结构不统一且关键标签定义不稳定（含 archived/中间产物），试运行阶段跳过。',
    'LongBench': '多子任务异构且多数非统一问答标签，单脚本高质量改造风险高，试运行阶段跳过。',
    'OpenPI2.0': '以过程状态结构化标注为主，缺少统一问答金标字段，试运行阶段跳过。',
    'ProPara': '原始任务需复杂过程状态对齐与多文件联动，试运行阶段跳过。',
    'situated_gen': '当前主文件缺少明确答案标签字段，无法保证“全部有正确答案”，跳过。',
    'TRaVelER': '目录主要为模型结果文件而非原始标注集，避免二次污染，跳过。',
    'TRIP': '当前可见数据以后处理样例为主，缺少稳定可扩展金标训练集，跳过。',
    'UDS_T_v1.0': '语义标注表非直接QA样式，改造成对话选择题需要额外任务定义，试运行阶段跳过。',
    'winogrande': '当前目录无主数据文件，仅README，跳过。'
}

DATASET_LANG = {
    'SI-Bench': 'zh'
}

NOISE_STYLES = ['v1', 'v2', 'v3']

STYLE_DESCRIPTION = {
    'v1': 'environment noise + light timeline perturbation',
    'v2': 'third-party interruption + task switching',
    'v3': 'timeline conflict + action interruption'
}


def dataset_lang(name: str) -> str:
    return DATASET_LANG.get(name, 'en')


def seeded_rng(key: str):
    h = int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)
    return random.Random(SEED + (h % 1000000007))


def read_jsonl(path: Path):
    for i, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            yield i, json.loads(line)
        except Exception:
            continue


def split_sentences(text: str):
    if not text:
        return []
    parts = re.split(r'(?<=[.!?。！？])\s+', text)
    cleaned = [p.strip() for p in parts if p and len(p.strip()) >= 20]
    return cleaned


def context_distractors(context: str, answer: str, n=3):
    sents = split_sentences(context)
    ans_l = (answer or '').lower()
    cands = [s for s in sents if ans_l not in s.lower()]
    rng = seeded_rng('distractors:' + answer[:50])
    rng.shuffle(cands)
    picks = cands[:n]
    fallback = [
        'Not enough evidence in the passage.',
        'The passage suggests a different conclusion.',
        'The statement conflicts with the given context.'
    ]
    while len(picks) < n:
        picks.append(fallback[len(picks) % len(fallback)])
    return picks[:n]


def shuffle_options(options, answer_texts, key):
    rng = seeded_rng(key)
    opts = list(options)
    rng.shuffle(opts)
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    labeled, answer_key = [], []
    for i, t in enumerate(opts):
        k = letters[i]
        labeled.append({'key': k, 'text': t})
        if t in answer_texts:
            answer_key.append(k)
    return labeled, answer_key


def make_single(dataset, task, sid, context, question, options, answer_texts, extra=None):
    if extra is None:
        extra = {}
    lang = dataset_lang(dataset)
    labeled, answer_key = shuffle_options(options, set(answer_texts), f'{dataset}:{sid}:single')
    opt_text = '\n'.join([f"{o['key']}. {o['text']}" for o in labeled])

    if lang == 'zh':
        sys = '你是一个严谨的推理助手。请严格依据原文回答，不要编造信息。'
        usr = f"请阅读下面原文并回答问题。\n\n原文：\n{context}\n\n问题：{question}\n\n选项：\n{opt_text}\n\n请只输出正确选项字母（可多选）。"
    else:
        sys = 'You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.'
        usr = f"Please read the full context and answer the question.\n\nContext:\n{context}\n\nQuestion: {question}\n\nOptions:\n{opt_text}\n\nReturn only the correct option letter(s)."

    return {
        'dataset_name': dataset,
        'task_type': task,
        'source_id': sid,
        'format': 'single_turn',
        'language': lang,
        'messages': [
            {'role': 'system', 'content': sys},
            {'role': 'user', 'content': usr}
        ],
        'options': labeled,
        'answer_key': answer_key,
        'metadata': extra
    }


def build_noisy_messages(lang, style, sid, context, question, opt_text):
    rng = seeded_rng(f'noise:{lang}:{style}:{sid}')
    add_extra_pair = rng.random() < 0.55

    if lang == 'zh':
        if style == 'v1':
            conv = [
                {'role': 'user', 'content': '我在等公交，风有点大，刚错过一班车。正好和你聊个题。'},
                {'role': 'assistant', 'content': '哈哈太惨了，你发来吧，我陪你一起看。'},
                {'role': 'user', 'content': f'好，我先贴原文（请完整读）：\n\n{context}\n\n我看一下到站提醒，还要十几分钟。'},
                {'role': 'assistant', 'content': '收到，我先过一遍。你把题目和选项也发我。'}
            ]
            if add_extra_pair:
                conv.extend([
                    {'role': 'user', 'content': '顺带一提，刚才旁边有人打翻咖啡，现场有点乱，不过不影响题目。'},
                    {'role': 'assistant', 'content': '笑死，画面感有了。行，我们继续看题。'}
                ])
            conv.append({'role': 'user', 'content': f'问题：{question}\n\n选项：\n{opt_text}\n\n请只输出最终正确选项字母（可多选）。'})
            return conv

        if style == 'v2':
            conv = [
                {'role': 'user', 'content': '我在餐厅点餐，周围有点吵。我们边聊边做一道题。'},
                {'role': 'assistant', 'content': '行呀，你先点单，弄好我们就开做。'},
                {'role': 'user', 'content': f'（对店员）一杯冰美式，谢谢。\n\n好了继续，原文如下：\n\n{context}'},
                {'role': 'assistant', 'content': '我看到了，继续。'}
            ]
            if add_extra_pair:
                conv.extend([
                    {'role': 'user', 'content': '（朋友插话）你不是说今天不做题吗？我说先做这一题就好。'},
                    {'role': 'assistant', 'content': '哈哈懂了，做完这题就收工。'}
                ])
            conv.append({'role': 'user', 'content': f'问题：{question}\n\n选项：\n{opt_text}\n\n请比较所有选项后，只返回正确字母。'})
            return conv

        conv = [
            {'role': 'user', 'content': '我刚导航走错路，现在停在路边重新规划。等我两秒，想请你做道题。'},
            {'role': 'assistant', 'content': '先注意安全，我在这等你。准备好就发。'},
            {'role': 'user', 'content': f'好了，继续。原文如下（不要省略）：\n\n{context}'},
            {'role': 'assistant', 'content': 'ok，我读完了，你发问题吧。'}
        ]
        if add_extra_pair:
            conv.extend([
                {'role': 'user', 'content': '补充个背景：我前阵子说过不太想做这类题，但这次还是想认真判断。'},
                {'role': 'assistant', 'content': '懂，这次感觉状态到了。我们按原文来判断。'}
            ])
        conv.append({'role': 'user', 'content': f'问题：{question}\n\n选项：\n{opt_text}\n\n请仅输出答案字母（可多选）。'})
        return conv

    if style == 'v1':
        conv = [
            {'role': 'user', 'content': 'I just missed my bus and I am stuck waiting. Want to help me think through a question?'},
            {'role': 'assistant', 'content': 'Of course. Send it over and we can figure it out together.'},
            {'role': 'user', 'content': f'Great, here is the full context (do not skip any part):\n\n{context}\n\nuh, let me check the transit app... still delayed.'},
            {'role': 'assistant', 'content': 'No rush. I read it, send the question and options when you are ready.'}
        ]
        if add_extra_pair:
            conv.extend([
                {'role': 'user', 'content': 'Also, random side note: someone nearby dropped a coffee cup. Anyway, back to the question.'},
                {'role': 'assistant', 'content': 'What a scene. Yep, let us get back to the question.'}
            ])
        conv.append({'role': 'user', 'content': f'Question: {question}\n\nOptions:\n{opt_text}\n\nThink carefully through all options and return only the final correct option letter(s).'})
        return conv

    if style == 'v2':
        conv = [
            {'role': 'user', 'content': 'I am in a cafe placing an order, so there may be interruptions. I still want to solve one reasoning question.'},
            {'role': 'assistant', 'content': 'Nice, cafe study mode. Send the context when you are set.'},
            {'role': 'user', 'content': f'(to staff) One avocado toast, please.\n\nBack now. Here is the context:\n\n{context}'},
            {'role': 'assistant', 'content': 'Got it, I read through it. Keep going.'}
        ]
        if add_extra_pair:
            conv.extend([
                {'role': 'user', 'content': '(friend jumps in) You said you were done for today.\nI know, but I want to finish this one first.'},
                {'role': 'assistant', 'content': 'Fair enough, one last question is always how it starts.'}
            ])
        conv.append({'role': 'user', 'content': f'Question: {question}\n\nOptions:\n{opt_text}\n\nReturn only the correct option letter(s).'})
        return conv

    conv = [
        {'role': 'user', 'content': 'I took a wrong turn while driving and just pulled over to re-route. Can we do a reasoning item now?'},
        {'role': 'assistant', 'content': 'Yep, first things first, stay safe. Send it when you are parked.'},
        {'role': 'user', 'content': f'I am parked now. Here is the full context:\n\n{context}'},
        {'role': 'assistant', 'content': 'Nice, I am with you so far.'}
    ]
    if add_extra_pair:
        conv.extend([
            {'role': 'user', 'content': 'Minor conflict note: last month I said I was tired of this kind of task, but this one seems worth solving.'},
            {'role': 'assistant', 'content': 'That is relatable. Let us solve this one cleanly based on the text.'}
        ])
    conv.append({'role': 'user', 'content': f'Question: {question}\n\nOptions:\n{opt_text}\n\nCompare all options and output only the final answer letter(s).'})
    return conv


def make_multi(dataset, task, sid, context, question, options, answer_texts, style='v1', extra=None):
    if extra is None:
        extra = {}
    lang = dataset_lang(dataset)
    labeled, answer_key = shuffle_options(options, set(answer_texts), f'{dataset}:{sid}:multi:{style}')
    opt_text = '\n'.join([f"{o['key']}. {o['text']}" for o in labeled])
    messages = build_noisy_messages(lang, style, sid, context, question, opt_text)

    return {
        'dataset_name': dataset,
        'task_type': task,
        'source_id': sid,
        'format': 'multi_turn',
        'language': lang,
        'messages': messages,
        'options': labeled,
        'answer_key': answer_key,
        'metadata': dict(extra, noise_style=style)
    }


def convert_cosmosqa():
    path = DATA / 'CosmosQA' / 'data' / 'train.csv'
    out = []
    with path.open('r', encoding='utf-8', errors='ignore', newline='') as f:
        rd = csv.DictReader(f)
        for i, row in enumerate(rd):
            if i >= SAMPLE_N:
                break
            opts = [row['answer0'], row['answer1'], row['answer2'], row['answer3']]
            ans = opts[int(row['label'])]
            out.append((row['id'], row['context'], row['question'], opts, [ans], {'split': 'train'}))
    return out


def convert_drop():
    path = DATA / 'DROP' / 'DROP.jsonl'
    out = []
    for i, obj in read_jsonl(path):
        if len(out) >= SAMPLE_N:
            break
        aobj = obj.get('answers_spans') or {}
        spans = aobj.get('spans', []) if isinstance(aobj, dict) else []
        if not spans:
            continue
        ans = spans[0]
        passage = obj.get('passage', '')
        nums = re.findall(r'\b\d+(?:\.\d+)?\b', passage)
        nums = [n for n in nums if n != ans]
        rng = seeded_rng(obj.get('query_id', str(i)))
        rng.shuffle(nums)
        opts = [ans] + nums[:3]
        if len(opts) < 4:
            opts += context_distractors(passage, ans, 4 - len(opts))
        out.append((obj.get('query_id', f'drop-{i}'), passage, obj.get('question', ''), opts[:4], [ans], {'split': 'all'}))
    return out


def convert_hellaswag():
    path = DATA / 'HellaSwag' / 'data' / 'hellaswag_train.jsonl'
    out = []
    for _, obj in read_jsonl(path):
        if len(out) >= SAMPLE_N:
            break
        label = obj.get('label')
        endings = obj.get('endings', [])
        if label is None or len(endings) < 4:
            continue
        ans = endings[int(label)]
        out.append((str(obj.get('ind', f'hella-{len(out)}')), obj.get('ctx', ''), 'Choose the most plausible continuation.', endings[:4], [ans], {'split': 'train'}))
    return out


def convert_mctaco():
    path = DATA / 'MCTACO' / 'dataset' / 'dev_3783.tsv'
    out = []
    for i, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines()):
        if len(out) >= SAMPLE_N:
            break
        p = line.split('\t')
        if len(p) < 5:
            continue
        sentence, question, candidate, label, category = p[0], p[1], p[2], p[3].strip().lower(), p[4]
        if label not in ('yes', 'no'):
            continue
        q = f"{question} Candidate answer: \"{candidate}\". Is this candidate plausible based on the sentence and temporal commonsense?"
        out.append((f'mctaco-{i}', sentence, q, ['yes', 'no'], [label], {'split': 'dev', 'category': category}))
    return out


def convert_narrativeqa():
    qp = DATA / 'narrative-qa' / 'queries.jsonl'
    cp = DATA / 'narrative-qa' / 'chunks.jsonl'
    chunks = {}
    for _, c in read_jsonl(cp):
        chunks[c.get('chunk_id')] = c.get('chunk', '')
    out = []
    for i, q in read_jsonl(qp):
        if len(out) >= SAMPLE_N:
            break
        ans = q.get('answer')
        if not ans:
            continue
        ctx = chunks.get(q.get('chunk_id'), '')
        if not ctx:
            continue
        # Some rewritten `query` values are noisy in this dump; `og_query` is aligned with `answer`.
        question = (q.get('og_query') or q.get('query') or '').strip()
        if not question:
            continue
        opts = [ans] + context_distractors(ctx, ans, 3)
        out.append((q.get('chunk_id', f'nqa-{i}'), ctx, question, opts, [ans], {'split': 'mixed'}))
    return out


def convert_pasta():
    path = DATA / 'pasta' / 'data' / 'tr_data.jsonl'
    out = []
    for i, obj in read_jsonl(path):
        if len(out) >= SAMPLE_N:
            break
        assertion = obj.get('Answer.assertion')
        if not assertion:
            continue
        support = []
        for k in ['Answer.line1.on','Answer.line2.on','Answer.line3.on','Answer.line4.on','Answer.line5.on']:
            if obj.get(k) is True:
                support.append(k.replace('Answer.', '').replace('.on', ''))
        if not support:
            continue
        ctx = '\n'.join([f"line{j}: {obj.get(f'Input.line{j}', '')}" for j in range(1, 6)])
        q = f"Assertion: {assertion}. Which lines support this assertion?"
        out.append((obj.get('AssignmentId', f'pasta-{i}'), ctx, q, ['line1', 'line2', 'line3', 'line4', 'line5'], support, {'split': 'train', 'title': obj.get('Input.Title', '')}))
    return out


def convert_piqa():
    qpath = DATA / 'PIQA' / 'physicaliqa-train-dev' / 'train.jsonl'
    lpath = DATA / 'PIQA' / 'physicaliqa-train-dev' / 'train-labels.lst'
    labels = lpath.read_text(encoding='utf-8', errors='ignore').splitlines()
    out = []
    for i, (_, obj) in enumerate(read_jsonl(qpath)):
        if len(out) >= SAMPLE_N or i >= len(labels):
            break
        opts = [obj.get('sol1', ''), obj.get('sol2', '')]
        lb = labels[i].strip()
        if lb not in ('0', '1'):
            continue
        ans = opts[int(lb)]
        out.append((obj.get('id', f'piqa-{i}'), obj.get('goal', ''), 'Which option is more plausible?', opts, [ans], {'split': 'train'}))
    return out


def flatten_qasper_full_text(full_text):
    if not isinstance(full_text, list):
        return ''
    chunks = []
    for sec in full_text:
        if not isinstance(sec, dict):
            continue
        name = sec.get('section_name') or ''
        paras = sec.get('paragraphs') or []
        if name:
            chunks.append(f"[Section] {name}")
        for p in paras:
            if isinstance(p, str):
                chunks.append(p)
    return '\n'.join(chunks)


def convert_qasper():
    data = json.loads((DATA / 'qasper' / 'qasper-train-v0.3.json').read_text(encoding='utf-8', errors='ignore'))
    out = []
    for pid, paper in data.items():
        if len(out) >= SAMPLE_N:
            break
        abstract = paper.get('abstract', '')
        full_txt = flatten_qasper_full_text(paper.get('full_text'))
        context = (abstract + '\n\n' + full_txt).strip()
        if not context:
            continue

        # build local answer pool for better distractor relevance
        local_pool = []
        for qa in paper.get('qas', []):
            for a in qa.get('answers', []):
                txt = a.get('answer', {}).get('free_form_answer')
                if txt:
                    local_pool.append(txt)

        for qidx, qa in enumerate(paper.get('qas', [])):
            if len(out) >= SAMPLE_N:
                break
            q = qa.get('question', '')
            answers = []
            for a in qa.get('answers', []):
                txt = a.get('answer', {}).get('free_form_answer')
                if txt:
                    answers.append(txt)
            if not q or not answers:
                continue
            ans = answers[0]
            rng = seeded_rng(f'{pid}-{qidx}')
            cands = [x for x in local_pool if x != ans]
            rng.shuffle(cands)
            distract = cands[:3]
            if len(distract) < 3:
                distract += context_distractors(context, ans, 3 - len(distract))
            opts = [ans] + distract[:3]
            out.append((f'{pid}-{qidx}', context, q, opts, [ans], {'split': 'train'}))
    return out[:SAMPLE_N]


def convert_si_bench():
    p = DATA / 'SI-Bench' / 'SI-Bench.json'
    arr = json.loads(p.read_text(encoding='utf-8', errors='ignore'))
    if isinstance(arr, dict):
        arr = arr.get('data', [])
    scenarios = sorted({x.get('second_level_scenario', '') for x in arr if x.get('second_level_scenario')})
    out = []
    for i, obj in enumerate(arr):
        if len(out) >= SAMPLE_N:
            break
        label = obj.get('second_level_scenario')
        if not label:
            continue
        rng = seeded_rng(str(obj.get('id', i)))
        neg = [s for s in scenarios if s != label]
        rng.shuffle(neg)
        opts = [label] + neg[:3]
        out.append((str(obj.get('id', f'si-{i}')), obj.get('chat_messages', ''), '该对话最符合哪类场景标签？', opts, [label], {'split': 'all'}))
    return out


def convert_socialiqa():
    qpath = DATA / 'SocialIQA' / 'train.jsonl'
    lpath = DATA / 'SocialIQA' / 'train-labels.lst'
    labels = lpath.read_text(encoding='utf-8', errors='ignore').splitlines()
    out = []
    for i, (_, obj) in enumerate(read_jsonl(qpath)):
        if len(out) >= SAMPLE_N or i >= len(labels):
            break
        opts = [obj.get('answerA', ''), obj.get('answerB', ''), obj.get('answerC', '')]
        lb = labels[i].strip()
        if not lb.isdigit():
            continue
        idx = max(0, min(2, int(lb) - 1))
        ans = opts[idx]
        out.append((f'siqa-{i}', obj.get('context', ''), obj.get('question', ''), opts, [ans], {'split': 'train'}))
    return out


def convert_tempreason():
    path = DATA / 'TempReason' / 'train_l1.json'
    pool = []
    out = []
    for i, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines()):
        if len(out) >= SAMPLE_N:
            break
        try:
            obj = json.loads(line)
        except Exception:
            continue
        ans_list = obj.get('text_answers', {}).get('text', [])
        if not ans_list:
            continue
        ans = ans_list[0]
        rng = seeded_rng(obj.get('id', str(i)))
        neg = [x for x in pool if x != ans]
        rng.shuffle(neg)
        opts = [ans] + neg[:3]
        if len(opts) < 4:
            opts += ['Unknown time', 'Not enough information', 'Different date'][:4 - len(opts)]
        context = f"Reference date: {obj.get('date', '')}"
        out.append((obj.get('id', f'tempreason-{i}'), context, obj.get('question', ''), opts, [ans], {'split': 'train_l1'}))
        pool.append(ans)
        if len(pool) > 5000:
            pool.pop(0)
    return out


def convert_timedial():
    arr = json.loads((DATA / 'TimeDial' / 'test.json').read_text(encoding='utf-8', errors='ignore'))
    out = []
    for i, obj in enumerate(arr[:SAMPLE_N]):
        conv = obj.get('conversation', [])
        if not conv:
            continue
        c1, c2 = obj.get('correct1', ''), obj.get('correct2', '')
        i1, i2 = obj.get('incorrect1', ''), obj.get('incorrect2', '')
        opts = [x for x in [c1, c2, i1, i2] if x]
        ans = [x for x in [c1, c2] if x]
        if not opts or not ans:
            continue
        turns = []
        for t in conv:
            tt = t.strip()
            if tt.startswith('A:'):
                turns.append({'role': 'user', 'content': tt[2:].strip()})
            elif tt.startswith('B:'):
                turns.append({'role': 'assistant', 'content': tt[2:].strip()})
            else:
                turns.append({'role': 'user', 'content': tt})
        context = '\n'.join(conv)
        q = 'Based on the dialogue, which option(s) best fill <MASK>?'
        out.append((str(obj.get('id', f'timedial-{i}')), context, q, opts, ans, {'split': 'test', 'dialogue_turns': turns}))
    return out


def convert_timeqa():
    path = DATA / 'TimeQA' / 'dataset' / 'dev.easy.json'
    pool = []
    out = []
    for i, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines()):
        if len(out) >= SAMPLE_N:
            break
        try:
            obj = json.loads(line)
        except Exception:
            continue
        ans = obj.get('targets', [None])[0]
        if not ans:
            continue
        rng = seeded_rng(obj.get('idx', str(i)))
        neg = [x for x in pool if x != ans]
        rng.shuffle(neg)
        opts = [ans] + neg[:3]
        if len(opts) < 4:
            opts += ['Unknown', 'Not stated', 'Another time point'][:4 - len(opts)]
        out.append((obj.get('idx', f'timeqa-{i}'), obj.get('context', ''), obj.get('question', ''), opts, [ans], {'split': 'dev.easy'}))
        pool.append(ans)
        if len(pool) > 5000:
            pool.pop(0)
    return out


def parse_tracie_line(line):
    if 'event:' not in line or 'story:' not in line or 'answer:' not in line:
        return None
    try:
        eidx = line.index('event:') + len('event:')
        sidx = line.index('story:')
        aidx = line.rindex('answer:')
        event = line[eidx:sidx].strip()
        story = line[sidx + len('story:'):aidx].strip()
        ans = line[aidx + len('answer:'):].strip()
        return event, story, ans
    except Exception:
        return None


def convert_tracie():
    path = DATA / 'tracie' / 'data' / 'iid' / 'tracie_train.txt'
    out = []
    for i, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines()):
        if len(out) >= SAMPLE_N:
            break
        parsed = parse_tracie_line(line)
        if not parsed:
            continue
        event, story, ans = parsed
        if ans not in ('positive', 'negative'):
            continue
        q = f"Is the event relation \"{event}\" temporally consistent with the story?"
        out.append((f'tracie-{i}', story, q, ['positive', 'negative'], [ans], {'split': 'train'}))
    return out


def convert_udst_durationqa():
    path = DATA / 'UDST-DurationQA' / 'data' / 'train.tsv'
    out = []
    for i, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines()):
        if len(out) >= SAMPLE_N:
            break
        p = line.split('\t')
        if len(p) < 4:
            continue
        sent, question, cand, label = p[0], p[1], p[2], p[3].strip().lower()
        if label not in ('yes', 'no'):
            continue
        # naturalized yes/no question around candidate duration
        q = f"{question} Is it reasonable that the duration is \"{cand}\"?"
        out.append((f'udst-{i}', sent, q, ['yes', 'no'], [label], {'split': 'train'}))
    return out


CONVERTERS = {
    'CosmosQA': convert_cosmosqa,
    'DROP': convert_drop,
    'HellaSwag': convert_hellaswag,
    'MCTACO': convert_mctaco,
    'narrative-qa': convert_narrativeqa,
    'pasta': convert_pasta,
    'PIQA': convert_piqa,
    'qasper': convert_qasper,
    'SI-Bench': convert_si_bench,
    'SocialIQA': convert_socialiqa,
    'TempReason': convert_tempreason,
    'TimeDial': convert_timedial,
    'TimeQA': convert_timeqa,
    'tracie': convert_tracie,
    'UDST-DurationQA': convert_udst_durationqa
}

OUT.mkdir(exist_ok=True)
summary = {}
skipped = {}
examples = []
noise_report = {}

for ds in ALL_DATASETS:
    if ds not in CONVERTERS:
        skipped[ds] = SKIP_REASON.get(ds, 'No stable converter implemented for this dataset in sample mode.')
        continue
    try:
        rows = CONVERTERS[ds]()
        if not rows:
            skipped[ds] = 'No valid answer-bearing samples extracted.'
            continue
        rows = rows[:SAMPLE_N]
        task = TASK_MAP[ds]
        single = []
        multi_by_style = {style: [] for style in NOISE_STYLES}
        source_ids = []

        for sid, ctx, q, opts, ans, meta in rows:
            s = make_single(ds, task, sid, ctx, q, opts, ans, extra=meta)
            source_ids.append(str(sid))
            clean_meta = {k: v for k, v in (meta or {}).items() if k != 'dialogue_turns'}
            for style in NOISE_STYLES:
                m = make_multi(ds, task, sid, ctx, q, opts, ans, style=style, extra=clean_meta)
                multi_by_style[style].append(m)
            single.append(s)

        ddir = OUT / ds / RUN_MODE
        ddir.mkdir(parents=True, exist_ok=True)
        legacy_multi = ddir / f'{ds}_multi.jsonl'
        if legacy_multi.exists():
            legacy_multi.unlink()
        (ddir / f'{ds}_single.jsonl').write_text('\n'.join(json.dumps(x, ensure_ascii=False) for x in single), encoding='utf-8')
        for style in NOISE_STYLES:
            (ddir / f'{ds}_multi_{style}.jsonl').write_text('\n'.join(json.dumps(x, ensure_ascii=False) for x in multi_by_style[style]), encoding='utf-8')

        summary[ds] = {
            'status': 'converted',
            'task_type': task,
            'sample_size': len(rows),
            'output_files': [
                str((ddir / f'{ds}_single.jsonl').as_posix()),
                str((ddir / f'{ds}_multi_v1.jsonl').as_posix()),
                str((ddir / f'{ds}_multi_v2.jsonl').as_posix()),
                str((ddir / f'{ds}_multi_v3.jsonl').as_posix())
            ]
        }
        noise_report[ds] = {
            'sample_size': len(rows),
            'source_ids': source_ids
        }
        examples.append({
            'dataset': ds,
            'task_type': task,
            'source_brief': rows[0][1][:200],
            'single_example': single[0],
            'multi_v1_example': multi_by_style['v1'][0],
            'multi_v2_example': multi_by_style['v2'][0],
            'multi_v3_example': multi_by_style['v3'][0]
        })
    except Exception as e:
        skipped[ds] = f'Conversion failed: {e}'

for ds, reason in skipped.items():
    summary[ds] = {
        'status': 'skipped',
        'reason': reason,
        'task_type': None,
        'sample_size': 0,
        'output_files': []
    }

summary_json_name = 'mapping_summary.json' if RUN_MODE == 'sample' else 'mapping_summary_full.json'
summary_md_name = 'mapping_summary.md' if RUN_MODE == 'sample' else 'mapping_summary_full.md'
skipped_md_name = 'skipped_report.md' if RUN_MODE == 'sample' else 'skipped_report_full.md'
examples_md_name = 'before_after_examples.md' if RUN_MODE == 'sample' else 'before_after_examples_full.md'
noise_md_name = 'noise_style_report.md' if RUN_MODE == 'sample' else 'noise_style_report_full.md'

(OUT / summary_json_name).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

lines = [f'# Dataset-to-Task Mapping ({RUN_MODE})', '']
lines.append('## Converted')
for ds in ALL_DATASETS:
    s = summary.get(ds, {})
    if s.get('status') == 'converted':
        lines.append(f"- {ds}: {s.get('task_type')}, sample_size={s.get('sample_size')}, files={', '.join(s.get('output_files', []))}")
lines.append('')
lines.append('## Skipped with Reasons')
for ds in ALL_DATASETS:
    s = summary.get(ds, {})
    if s.get('status') != 'converted':
        lines.append(f"- {ds}: {s.get('reason', '')}")
(OUT / summary_md_name).write_text('\n'.join(lines), encoding='utf-8')

slines = [f'# Skipped Datasets and Reasons ({RUN_MODE})', '']
for ds in ALL_DATASETS:
    s = summary.get(ds, {})
    if s.get('status') != 'converted':
        slines.append(f"- {ds}: {s.get('reason', '')}")
(OUT / skipped_md_name).write_text('\n'.join(slines), encoding='utf-8')

elines = [f'# Before/After Samples ({RUN_MODE})', '']
for ex in examples:
    elines.append(f"## {ex['dataset']} -> {ex['task_type']}")
    elines.append('- Source excerpt')
    elines.append('```text')
    elines.append(ex['source_brief'])
    elines.append('```')
    elines.append('- single_turn example')
    elines.append('```json')
    elines.append(json.dumps(ex['single_example'], ensure_ascii=False)[:2200])
    elines.append('```')
    elines.append('- multi_turn v1 example')
    elines.append('```json')
    elines.append(json.dumps(ex['multi_v1_example'], ensure_ascii=False)[:2200])
    elines.append('```')
    elines.append('- multi_turn v2 example')
    elines.append('```json')
    elines.append(json.dumps(ex['multi_v2_example'], ensure_ascii=False)[:2200])
    elines.append('```')
    elines.append('- multi_turn v3 example')
    elines.append('```json')
    elines.append(json.dumps(ex['multi_v3_example'], ensure_ascii=False)[:2200])
    elines.append('```')
    elines.append('')
(OUT / examples_md_name).write_text('\n'.join(elines), encoding='utf-8')

nlines = [f'# Noise Style Report ({RUN_MODE})', '']
nlines.append('## Style Definitions')
for style in NOISE_STYLES:
    nlines.append(f"- {style}: {STYLE_DESCRIPTION[style]}")
nlines.append('')
nlines.append('## Dataset and Sample Coverage')
for ds in ALL_DATASETS:
    if ds not in noise_report:
        continue
    info = noise_report[ds]
    nlines.append(f"### {ds}")
    nlines.append(f"- sample_size: {info['sample_size']}")
    nlines.append("- styles_per_sample: v1, v2, v3")
    if RUN_MODE == 'sample':
        nlines.append('- per-sample mapping:')
        for sid in info['source_ids']:
            nlines.append(f"  - {sid}: v1, v2, v3")
    else:
        nlines.append('- per-sample mapping: omitted in full mode (too large), every sample has v1/v2/v3')
    nlines.append('')
(OUT / noise_md_name).write_text('\n'.join(nlines), encoding='utf-8')

print('converted:', sum(1 for v in summary.values() if v.get('status') == 'converted'))
print('skipped:', sum(1 for v in summary.values() if v.get('status') != 'converted'))
print('mode:', RUN_MODE)
print('done -> data-converted')
