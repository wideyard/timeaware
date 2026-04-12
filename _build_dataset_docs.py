import json
import re
from pathlib import Path

inv_path = Path('data-states/_dataset_inventory.json')
items = json.loads(inv_path.read_text(encoding='utf-8'))

order = [
'ATOMIC','choice-75','CosmosQA','DROP','HellaSwag','LongBench','MCTACO','narrative-qa','OpenPI2.0','pasta','PIQA','ProPara','qasper','SI-Bench','situated_gen','SocialIQA','TempReason','TimeDial','TimeQA','tracie','TRaVelER','TRIP','UDS_T_v1.0','UDST-DurationQA','winogrande'
]

profiles = {
'ATOMIC': {
'task':'常识时序与因果推理（事件后果、意图、反应）',
'method':'以事件短语为锚点，人工/众包补全 xIntent、xEffect、oReact 等关系；同时保留 ATOMIC 2020 的三元组格式。',
'purpose':'训练模型进行 if-then 常识推理，增强对事件因果链与人物心理状态的建模能力。',
'notes':'目录内同时包含 v4 csv 与 atomic2020 tsv 两种版本，字段定义不同，建模前需统一 schema。'
},
'choice-75': {
'task':'目标导向程序脚本分支选择与理由生成',
'method':'围绕日常 goal 构造步骤序列，在关键分歧点设置两个候选分支并标注 rationale（如 op1_ra/op2_ra）。',
'purpose':'评测模型在程序化计划中做分支决策、解释决策依据以及检索相关步骤的能力。',
'notes':'仓库中含 archived 与任务提示模板文件，训练时应区分原始标注数据与 prompt 资源。'
},
'CosmosQA': {
'task':'阅读理解 + 常识选择题（四选一）',
'method':'基于叙事段落（多来自博客/故事）构造问题与 4 个候选答案，人工标注正确选项。',
'purpose':'测试模型在给定上下文下进行隐含因果和社会常识推断的能力。',
'notes':'train/valid 为 csv，test 为 jsonl；提交格式通常是 id,label。'
},
'DROP': {
'task':'离散推理阅读理解（数值、比较、计数）',
'method':'从段落中抽取可执行离散运算的问题，答案可涉及算术、集合比较与实体抽取。',
'purpose':'衡量模型在长段落中结合文本证据做符号化推理的能力，而非仅做 span 匹配。',
'notes':'当前仓库以 jsonl 保存实例化样本；注意与官方原始 json 结构可能存在转换差异。'
},
'HellaSwag': {
'task':'常识完形续写（多选）',
'method':'给定场景前缀 ctx 与四个 endings，通过对抗过滤（adversarial filtering）构造高迷惑负例。',
'purpose':'评估模型对日常事件连续性与物理/社会常识的理解。',
'notes':'split_type 可区分 indomain 等设置；test 通常不提供标签。'
},
'LongBench': {
'task':'长上下文综合评测（QA/摘要/代码等多任务）',
'method':'整合多个子任务数据集为统一 jsonl 格式，每条包含 input/context/answers 等字段。',
'purpose':'评估长上下文模型在不同任务类型上的鲁棒性与泛化。',
'notes':'该目录是多子集集合，不是单一任务；报告结果时需分子任务汇总。'
},
'MCTACO': {
'task':'时间常识问答（二分类 yes/no）',
'method':'给定句子、问题、候选答案和类别标签（如 Duration、Stationarity），判断候选是否成立。',
'purpose':'测试模型对时间范围、频率、顺序、持续时长等时间常识的掌握。',
'notes':'tsv 最后一列是 temporal category，可用于细粒度分析。'
},
'narrative-qa': {
'task':'叙事问答改写/切块数据',
'method':'将长篇叙事文档切分为 chunk，并为 query 关联 chunk_id 与答案。',
'purpose':'支持长叙事场景下的检索增强问答与问题重写研究。',
'notes':'本目录更像处理后的中间数据，不一定与官方 NarrativeQA 原始发布格式一致。'
},
'OpenPI2.0': {
'task':'过程理解与实体状态追踪',
'method':'围绕目标导向步骤（多源于 how-to）标注实体属性/状态在步骤前后的变化。',
'purpose':'训练模型理解 procedural text 中“谁在何时发生何种状态变化”。',
'notes':'包含多种重排与重格式版本（reformatted、ranked、cluster-removed），实验需固定版本。'
},
'pasta': {
'task':'故事断言支持性判断与时间一致性分析',
'method':'基于五句故事与断言，标注断言由哪些句子支持，并提供人类评测导出。',
'purpose':'评估模型在短叙事中对事实支持、时序连贯和解释性的处理能力。',
'notes':'human_eval_data 体量较大，属于评测导出；训练主数据在 data/*.jsonl。'
},
'PIQA': {
'task':'物理常识选择题（二选一）',
'method':'给定 goal 与两个解决方案，标签指示哪个方案更符合物理世界常识。',
'purpose':'测试模型在日常物理可行性判断上的能力。',
'notes':'文本与标签分离：jsonl 存题干与候选，*.lst 存金标。'
},
'ProPara': {
'task':'过程段落中的参与者状态变化追踪',
'method':'围绕自然过程（如“油如何形成”）标注实体在每步的存在/位置变化，并扩展了多种子任务格式。',
'purpose':'衡量模型对过程类文本中的动态状态更新与结构化推理能力。',
'notes':'目录同时包含官方数据、派生格式与测试夹具；统计时需区分真实训练集与测试资源。'
},
'qasper': {
'task':'学术论文问答（基于全文证据）',
'method':'以论文为单位组织标题/摘要/全文片段和问题答案标注。',
'purpose':'评估模型在科研文档场景下的多跳证据检索与回答能力。',
'notes':'json 顶层通常为 paper_id 映射；训练/开发/测试按论文数切分。'
},
'SI-Bench': {
'task':'社交语义理解与隐含意图识别（中文）',
'method':'收集真实对话片段并标注一级/二级场景（如讽刺、言外之意等）。',
'purpose':'评估模型在中文社交对话中的语用理解、隐喻和情感语境解析能力。',
'notes':'单文件 json，字段包含中英文场景名，适合做多标签或层级分类。'
},
'situated_gen': {
'task':'情境化陈述生成与一致性建模',
'method':'从多个 QA/知识源抽取 statement 与关键词，构造可控生成样本。',
'purpose':'训练模型在给定关键词/事实约束下生成连贯陈述。',
'notes':'除 train/dev/test 外，还提供 preprocessed statements 作为中间语料。'
},
'SocialIQA': {
'task':'社会常识问答（三选一）',
'method':'给定 context+question+3 个选项，通过标签文件给出正确答案。',
'purpose':'评估模型对人物动机、反应和社会互动结果的常识推理能力。',
'notes':'与 PIQA 类似，标签在独立 lst 文件中。'
},
'TempReason': {
'task':'时间算术与日期推理',
'method':'自动生成“若干年/月之后（或之前）”类问题，配对标准化日期答案。',
'purpose':'测试模型在公历日期上的算术推理和格式化输出能力。',
'notes':'部分 .json 实际为 jsonl（逐行 JSON），读取时应按行解析。'
},
'TimeDial': {
'task':'对话时间补全/推理（mask 预测）',
'method':'在多轮对话中掩蔽时间表达，利用上下文推断合理时间片段。',
'purpose':'评估对话场景下的时间一致性理解能力。',
'notes':'当前目录主要提供 test；训练集可能在上游仓库或其他分发路径。'
},
'TimeQA': {
'task':'时间约束问答（知识 + 文本）',
'method':'围绕时间区间构造问题，并区分 easy/hard、human test 等切分。',
'purpose':'评测模型在时间限定条件下进行实体关系问答与证据定位能力。',
'notes':'多个 .json 为逐行对象格式，解析时按 jsonl 处理更稳妥。'
},
'tracie': {
'task':'时间关系一致性判断（before/after）',
'method':'将故事与事件关系改写为正负样本，判断事件时间关系是否与叙事一致。',
'purpose':'测试模型在短叙事中的时序推断与矛盾识别能力。',
'notes':'包含 iid 与 uniform-prior 等不同采样设置，比较实验需保持同分布。'
},
'TRaVelER': {
'task':'事件日志上的时间/指代检索推理',
'method':'合成事件序列并构造 explicit/referential 查询，评估模型从事件流中检索答案。',
'purpose':'检验模型在结构化事件记忆上的时序检索与实体解析能力。',
'notes':'仓库中以结果文件为主，原始 dataset 可能在 dataset 子目录或外部来源。'
},
'TRIP': {
'task':'旅行规划结构化生成与评测',
'method':'基于用户画像、预算和约束生成多天行程，采用 JSON 结构对齐评测。',
'purpose':'测试模型在多约束规划任务中的可执行性与偏好对齐能力。',
'notes':'当前可见样本主要在 postprocess 中，属于评测格式示例。'
},
'UDS_T_v1.0': {
'task':'事件时间结构标注（Universal Decompositional Semantics - Time）',
'method':'在 UD 语料上对事件持续时间、起止区间和事件间关系进行细粒度标注。',
'purpose':'支持时间语义解析、时序关系建模和可解释时间推理研究。',
'notes':'tsv 字段较多，建模前建议先做字段字典与取值清洗。'
},
'UDST-DurationQA': {
'task':'持续时间问答（二分类）',
'method':'给定句子与“需要多长时间”问题，判断候选时长答案是否合理。',
'purpose':'评估模型对事件持续时间常识的判别能力。',
'notes':'与 MCTACO 同属时间常识类，但任务格式更聚焦 duration。'
},
'winogrande': {
'task':'常识指代消解（Wino 式填空）',
'method':'围绕歧义指代句构造候选替换并标注正确项（官方为多规模版本）。',
'purpose':'评估模型在去偏置设置下的常识推理与指代解析能力。',
'notes':'当前目录仅见 README，未检出主数据文件；需从上游或附加脚本下载。'
}
}


def read_text(path: Path, max_chars=6000):
    try:
        return path.read_text(encoding='utf-8', errors='ignore')[:max_chars]
    except Exception:
        return ''


def extract_readme_info(readme_paths):
    if not readme_paths:
        return ('未找到 README。', '未提取到显式数据构造描述。')
    # prefer top-level README files; avoid LICENSE as primary summary source
    def rank(path_str):
        p = path_str.lower()
        is_readme = 0 if 'readme' in p else 1
        is_license = 1 if 'license' in p else 0
        return (is_readme, is_license, path_str.count('/'), len(path_str))

    cand = sorted(readme_paths, key=rank)
    text = read_text(Path(cand[0]))
    lines = [ln.strip() for ln in text.splitlines()]

    para = []
    started = False
    for ln in lines:
        if not ln:
            if started:
                break
            continue
        if ln.startswith('#'):
            continue
        started = True
        para.append(ln)
        if len(' '.join(para)) > 280:
            break
    para_text = ' '.join(para) if para else 'README 首段为空或为徽章/链接。'

    kw = []
    for ln in lines:
        l = ln.lower()
        if any(k in l for k in ['construct', 'build', 'collect', 'annotation', 'crowd', 'mturk', 'dataset', 'split']):
            kw.append(ln.strip())
        if len(kw) >= 3:
            break
    method_hint = '；'.join(kw) if kw else 'README 中未直接命中构造关键词，以下方法依据任务定义与目录结构归纳。'
    return para_text, method_hint


def normalize_sample(s):
    if not s:
        return '（无）'
    s = s.replace('\n', ' ').replace('\r',' ').strip()
    if len(s) > 260:
        s = s[:260] + ' ...'
    return s


def pick_key_files(data_files):
    # prefer files with split markers and likely primary data
    priority = []
    for f in data_files:
        p = f.get('path','').lower()
        score = 0
        if any(k in p for k in ['/train', 'train.', '_train', '/dev', 'dev.', '/test', 'test.', '/val', 'valid']):
            score += 3
        if '/data/' in p:
            score += 2
        if any(k in p for k in ['results', 'experiment', 'prompt', 'fixture', 'requirements']):
            score -= 2
        if any(p.endswith(ext) for ext in ['.jsonl','.tsv','.csv','.json','.lst']):
            score += 1
        priority.append((score, f))
    priority.sort(key=lambda x: x[0], reverse=True)
    chosen = [f for _, f in priority[:6]]
    return chosen

out_dir = Path('data-states')
out_dir.mkdir(exist_ok=True)

for idx, name in enumerate(order, 1):
    entry = next((x for x in items if x['dataset'] == name), None)
    if not entry:
        continue
    p = profiles.get(name, {
        'task':'待补充',
        'method':'待补充',
        'purpose':'待补充',
        'notes':'待补充'
    })
    readme_intro, readme_method_hint = extract_readme_info(entry.get('readmes', []))
    key_files = pick_key_files(entry.get('data_files', []))

    total_known = 0
    total_files = 0
    for f in key_files:
        c = f.get('count')
        if isinstance(c, int):
            total_known += c
            total_files += 1

    lines = []
    lines.append(f"# {idx:02d}. {name} 数据集说明")
    lines.append('')
    lines.append('## 1. 数据集定位')
    lines.append(f"- 任务类型：{p['task']}")
    lines.append(f"- 目录位置：data/{name}")
    lines.append(f"- README 来源：{', '.join(entry.get('readmes', [])) if entry.get('readmes') else '无'}")
    lines.append('')
    lines.append('## 2. 数据规模（基于仓库内可见文件）')
    if key_files:
        for f in key_files:
            cnt = f.get('count', '未知')
            if isinstance(cnt, int):
                cnt = f"{cnt}"
            elif f.get('error'):
                cnt = f"解析失败（{f.get('error')}）"
            lines.append(f"- {f.get('path')}: {cnt}")
        if total_files:
            lines.append(f"- 已统计主文件合计（非去重）：{total_known}")
    else:
        lines.append('- 未检测到可直接统计的数据文件（仅有说明或需额外下载）。')
    lines.append('')
    lines.append('## 3. 数据样例')
    if key_files:
        sf = key_files[0]
        lines.append(f"- 样例来源：{sf.get('path')}")
        lines.append('')
        lines.append('```text')
        lines.append(normalize_sample(sf.get('sample','')))
        lines.append('```')
    else:
        lines.append('- 暂无样例（目录中未发现主数据文件）。')
    lines.append('')
    lines.append('## 4. 数据构造方法')
    lines.append(f"- 方法概述：{p['method']}")
    lines.append(f"- README/文件线索：{readme_method_hint}")
    lines.append('')
    lines.append('## 5. 数据构造目的')
    lines.append(f"- 目标：{p['purpose']}")
    lines.append('')
    lines.append('## 6. 你在使用前需要注意')
    lines.append(f"- 关键注意事项：{p['notes']}")
    lines.append(f"- README 摘要：{readme_intro}")
    lines.append('- 统计口径说明：本说明的条数来自仓库当前文件快照，若后续运行下载脚本或预处理脚本，条数可能变化。')

    out_path = out_dir / f"{idx:02d}-{name}.md"
    out_path.write_text('\n'.join(lines), encoding='utf-8')

print('generated', len(order), 'markdown files in data-states')
