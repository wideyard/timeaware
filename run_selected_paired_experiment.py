import argparse
import csv
import json
import random
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib import error, request

ROOT = Path('.')
DATA_CONVERTED = ROOT / 'data-converted'
STYLES = ['single', 'multi_v1', 'multi_v2', 'multi_v3']
STYLE_SUFFIX = {
    'single': '_single.jsonl',
    'multi_v1': '_multi_v1.jsonl',
    'multi_v2': '_multi_v2.jsonl',
    'multi_v3': '_multi_v3.jsonl',
}

TASK_TAG_RE = re.compile(r'^T[1-5]$')


GROUP_SPECS = [
    {'group': 'TimeDial', 'dataset': 'TimeDial', 'folder': 'full_T1', 'forced_task': 'T1'},
    {'group': 'SI-Bench', 'dataset': 'SI-Bench', 'folder': 'full_T4', 'forced_task': 'T4'},
    {'group': 'DROP', 'dataset': 'DROP', 'folder': 'full_T4', 'forced_task': 'T4'},
    {'group': 'pasta', 'dataset': 'pasta', 'folder': 'full_T2', 'forced_task': 'T2'},
    {'group': 'SocialIQA', 'dataset': 'SocialIQA', 'folder': 'full_T4', 'forced_task': 'T4'},
    {'group': 'CosmosQA', 'dataset': 'CosmosQA', 'folder': 'full_T4', 'forced_task': 'T4'},
    {'group': 'TempReason_T1', 'dataset': 'TempReason', 'folder': 'full_T1', 'forced_task': 'T1'},
    {'group': 'TempReason_T5', 'dataset': 'TempReason', 'folder': 'sample_T5', 'forced_task': 'T5'},
]


def resolve_dataset_folder(dataset: str, folder: str, forced_task: str | None = None) -> Path:
    ds_dir = DATA_CONVERTED / dataset
    if not ds_dir.exists():
        raise RuntimeError(f'Dataset directory not found: {ds_dir.as_posix()}')

    exact = ds_dir / folder
    if exact.exists():
        return exact

    if forced_task and TASK_TAG_RE.match(str(forced_task)):
        tagged = ds_dir / f'{folder}_{forced_task}'
        if tagged.exists():
            return tagged

    cand = []
    for p in ds_dir.iterdir():
        if p.is_dir() and re.fullmatch(rf'{re.escape(folder)}_T[1-5]', p.name):
            cand.append(p)

    if forced_task and TASK_TAG_RE.match(str(forced_task)):
        want = f'{folder}_{forced_task}'
        for p in cand:
            if p.name == want:
                return p

    if len(cand) == 1:
        return cand[0]

    raise RuntimeError(
        f'Cannot resolve folder for dataset={dataset}, folder={folder}, forced_task={forced_task}. '
        f'Candidates={[p.name for p in sorted(cand)]}'
    )


def read_jsonl(path: Path):
    with path.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def parse_api_txt(path: Path):
    providers = {
        'OPENAI': {'base_url': None, 'api_key': None},
        'ARK': {'base_url': None, 'api_key': None},
    }
    models = []
    current_provider = None

    for raw in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, val = line.split('=', 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")

        if key.endswith('_BASE_URL'):
            prefix = key.replace('_BASE_URL', '')
            if prefix in providers:
                providers[prefix]['base_url'] = val
                current_provider = prefix
            continue

        if key.endswith('_API_KEY'):
            prefix = key.replace('_API_KEY', '')
            if prefix in providers:
                providers[prefix]['api_key'] = val
                current_provider = prefix
            continue

        if key == 'model_name' and current_provider in providers:
            entry = {
                'provider': current_provider,
                'model': val,
                'base_url': providers[current_provider]['base_url'],
                'api_key': providers[current_provider]['api_key'],
            }
            if entry['base_url'] and entry['api_key'] and entry['model']:
                models.append(entry)

    return models


def post_chat_completion(base_url, api_key, model, messages, temperature=0.0, timeout=30):
    endpoint = base_url.rstrip('/') + '/chat/completions'
    payload = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
    }
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(endpoint, method='POST', data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {api_key}')

    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode('utf-8', errors='ignore')
        obj = json.loads(body)
        return obj['choices'][0]['message']['content']


def call_with_retry(model_cfg, messages, retries=1, timeout=30):
    last_err = None
    for i in range(retries + 1):
        try:
            content = post_chat_completion(
                base_url=model_cfg['base_url'],
                api_key=model_cfg['api_key'],
                model=model_cfg['model'],
                messages=messages,
                temperature=0.0,
                timeout=timeout,
            )
            return content, None
        except error.HTTPError as e:
            try:
                body = e.read().decode('utf-8', errors='ignore')
            except Exception:
                body = ''
            last_err = f'HTTPError {e.code}: {body[:500]}'
        except Exception as e:
            last_err = f'{type(e).__name__}: {e}'

        if i < retries:
            time.sleep(min(2 ** i, 4))

    return None, last_err


def normalize_text(s: str) -> str:
    s = (s or '').strip().lower()
    s = re.sub(r'[`\"\'\(\)\[\]{}<>]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def extract_predicted_keys(raw_text, options):
    text = (raw_text or '').strip()
    if not text:
        return []

    key_to_text = {o['key'].upper(): o.get('text', '') for o in options}
    valid_keys = set(key_to_text.keys())

    letter_hits = re.findall(r'\b([A-Z])\b', text.upper())
    preds = []
    for k in letter_hits:
        if k in valid_keys and k not in preds:
            preds.append(k)
    if preds:
        return preds

    norm_out = normalize_text(text)
    if not norm_out:
        return []

    text_matches = []
    for k, opt_text in key_to_text.items():
        nopt = normalize_text(opt_text)
        if not nopt:
            continue
        if norm_out == nopt or norm_out in nopt or nopt in norm_out:
            text_matches.append(k)

    if text_matches:
        seen = set()
        ordered = []
        for k in text_matches:
            if k not in seen:
                ordered.append(k)
                seen.add(k)
        return ordered

    if norm_out in {'no', 'yes'}:
        for k, opt_text in key_to_text.items():
            if normalize_text(opt_text) == norm_out:
                return [k]

    return []


def map_gold_keys(answer_key, options):
    key_to_text = {str(o.get('key', '')).upper(): normalize_text(str(o.get('text', ''))) for o in options}
    text_to_key = {v: k for k, v in key_to_text.items() if v}
    out = []

    for a in answer_key or []:
        s = str(a).strip()
        if not s:
            continue

        s_up = s.upper()
        if s_up in key_to_text:
            if s_up not in out:
                out.append(s_up)
            continue

        ns = normalize_text(s)
        if ns in text_to_key:
            k = text_to_key[ns]
            if k not in out:
                out.append(k)
            continue

        # Fallback for slight formatting differences in textual gold labels.
        for k, t in key_to_text.items():
            if not t:
                continue
            if ns == t or ns in t or t in ns:
                if k not in out:
                    out.append(k)

    return out


def f1_and_jaccard(pred_set, gold_set):
    if not pred_set and not gold_set:
        return 1.0, 1.0
    inter = len(pred_set & gold_set)
    p = inter / len(pred_set) if pred_set else 0.0
    r = inter / len(gold_set) if gold_set else 0.0
    f1 = 0.0 if (p + r) == 0 else (2 * p * r / (p + r))
    union = len(pred_set | gold_set)
    j = inter / union if union else 1.0
    return f1, j


def safe_model_name(model):
    return re.sub(r'[^a-zA-Z0-9._-]+', '_', model)


def add_summary(rows, out, group_name, group_value):
    n = len(rows)
    if n == 0:
        return
    exact = sum(r['exact_match'] for r in rows) / n
    single_rows = [r for r in rows if len(r['gold_keys']) == 1]
    single_acc = (sum(r['single_choice_acc'] for r in single_rows) / len(single_rows)) if single_rows else 0.0
    f1 = sum(r['f1'] for r in rows) / n
    jaccard = sum(r['jaccard'] for r in rows) / n
    err_rate = sum(1 for r in rows if r['error']) / n
    out.append({
        'group': group_name,
        'value': group_value,
        'n': n,
        'exact_match': round(exact, 6),
        'single_choice_acc': round(single_acc, 6),
        'f1': round(f1, 6),
        'jaccard': round(jaccard, 6),
        'error_rate': round(err_rate, 6),
    })


def resolve_style_files(base_dir: Path):
    files = {}
    for style, suf in STYLE_SUFFIX.items():
        hits = list(base_dir.glob(f'*{suf}'))
        if len(hits) != 1:
            raise RuntimeError(f'Expected exactly 1 file for {style} in {base_dir.as_posix()}, got {len(hits)}')
        files[style] = hits[0]
    return files


def read_source_ids(path: Path):
    s = set()
    pat = re.compile(r'"source_id"\s*:\s*"([^"]+)"')
    with path.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if m:
                s.add(m.group(1))
    return s


def load_samples_for_ids(path: Path, target_ids):
    m = {}
    need = set(target_ids)
    for obj in read_jsonl(path):
        sid = str(obj.get('source_id', ''))
        if sid in need and sid not in m:
            m[sid] = obj
            if len(m) >= len(need):
                break
    return m


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', type=str, default='')
    parser.add_argument('--samples-per-group', type=int, default=20)
    parser.add_argument('--seed', type=int, default=6)
    parser.add_argument('--workers', type=int, default=64)
    parser.add_argument('--retries', type=int, default=1)
    parser.add_argument('--timeout', type=int, default=30)
    args = parser.parse_args()

    models = parse_api_txt(ROOT / 'api.txt')
    if len(models) != 3:
        raise RuntimeError(f'Expected 3 models from api.txt, got {len(models)}')

    exp_root = DATA_CONVERTED / 'experiments'
    if args.run_id:
        run_dir = exp_root / args.run_id
    else:
        run_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_dir = exp_root / f'run_{run_ts}'

    pred_dir = run_dir / 'predictions'
    pred_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    selected = []

    for spec in GROUP_SPECS:
        base_dir = resolve_dataset_folder(spec['dataset'], spec['folder'], spec['forced_task'])
        files = resolve_style_files(base_dir)

        id_sets = [read_source_ids(files[s]) for s in STYLES]
        common = sorted(set.intersection(*id_sets))

        if len(common) < args.samples_per_group:
            raise RuntimeError(
                f"Group {spec['group']} has only {len(common)} paired source_ids; need {args.samples_per_group}"
            )

        chosen_ids = rng.sample(common, args.samples_per_group)

        style_maps = {}
        for style in STYLES:
            style_maps[style] = load_samples_for_ids(files[style], chosen_ids)

        for sid in chosen_ids:
            if any(sid not in style_maps[style] for style in STYLES):
                raise RuntimeError(f"Missing selected source_id {sid} in one or more styles for group {spec['group']}")
            samples = {style: style_maps[style][sid] for style in STYLES}
            any_obj = samples['single']
            task_type = spec['forced_task'] or str(any_obj.get('task_type', 'unknown'))
            selected.append({
                'group': spec['group'],
                'dataset': spec['dataset'],
                'folder': spec['folder'],
                'source_id': sid,
                'task_type': task_type,
                'samples': samples,
            })

    expected_calls = len(GROUP_SPECS) * args.samples_per_group * len(STYLES) * len(models)

    run_cfg = {
        'run_dir': run_dir.as_posix(),
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'samples_per_group': args.samples_per_group,
        'seed': args.seed,
        'styles': STYLES,
        'models': [m['model'] for m in models],
        'groups': GROUP_SPECS,
        'selected_pairs': len(selected),
        'expected_calls': expected_calls,
    }
    (run_dir / 'run_config.json').write_text(json.dumps(run_cfg, ensure_ascii=False, indent=2), encoding='utf-8')

    tasks = []
    for item in selected:
        for style in STYLES:
            sample = item['samples'][style]
            for m in models:
                tasks.append({
                    'group': item['group'],
                    'dataset': item['dataset'],
                    'folder': item['folder'],
                    'source_id': item['source_id'],
                    'task_type': item['task_type'],
                    'style': style,
                    'sample': sample,
                    'model_cfg': m,
                })

    results = []
    completed = 0

    model_files = {}
    for m in models:
        fp = pred_dir / f"{safe_model_name(m['model'])}.jsonl"
        model_files[m['model']] = fp.open('w', encoding='utf-8')

    def run_one(t):
        raw, err = call_with_retry(
            t['model_cfg'],
            t['sample'].get('messages', []),
            retries=args.retries,
            timeout=args.timeout,
        )
        pred_keys = extract_predicted_keys(raw or '', t['sample'].get('options', [])) if raw else []
        gold_keys = map_gold_keys(t['sample'].get('answer_key', []), t['sample'].get('options', []))
        pred_set = set(pred_keys)
        gold_set = set(gold_keys)
        exact = int(pred_set == gold_set)
        single_acc = int(len(gold_set) == 1 and pred_set == gold_set)
        f1, jaccard = f1_and_jaccard(pred_set, gold_set)
        return {
            'group': t['group'],
            'dataset': t['dataset'],
            'folder': t['folder'],
            'source_id': t['source_id'],
            'task_type': t['task_type'],
            'style': t['style'],
            'model': t['model_cfg']['model'],
            'prediction_raw': raw,
            'prediction_keys': sorted(pred_set),
            'gold_keys': sorted(gold_set),
            'exact_match': exact,
            'single_choice_acc': single_acc,
            'f1': f1,
            'jaccard': jaccard,
            'error': err,
        }

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = [ex.submit(run_one, t) for t in tasks]
        for fut in as_completed(futures):
            row = fut.result()
            results.append(row)
            mf = model_files[row['model']]
            mf.write(json.dumps(row, ensure_ascii=False) + '\n')
            mf.flush()
            completed += 1
            if completed % 25 == 0:
                print(f'progress: {completed}/{expected_calls}')

    for fh in model_files.values():
        try:
            fh.close()
        except Exception:
            pass

    by_model = defaultdict(list)
    for r in results:
        by_model[r['model']].append(r)

    summary = []
    add_summary(results, summary, 'overall', 'all')

    # model/style
    for model in sorted(by_model.keys()):
        mr = [r for r in results if r['model'] == model]
        add_summary(mr, summary, 'model', model)
        for style in STYLES:
            add_summary([r for r in mr if r['style'] == style], summary, 'model_style', f'{model}|{style}')

    # model/group/style
    groups = [g['group'] for g in GROUP_SPECS]
    for model in sorted(by_model.keys()):
        for group in groups:
            mgrp = [r for r in results if r['model'] == model and r['group'] == group]
            add_summary(mgrp, summary, 'model_group', f'{model}|{group}')
            for style in STYLES:
                add_summary([r for r in mgrp if r['style'] == style], summary, 'model_group_style', f'{model}|{group}|{style}')

    # model/task/style (for T1-T5 comparison over covered layers)
    task_types = sorted({r['task_type'] for r in results})
    for model in sorted(by_model.keys()):
        for tt in task_types:
            mt = [r for r in results if r['model'] == model and r['task_type'] == tt]
            add_summary(mt, summary, 'model_task', f'{model}|{tt}')
            for style in STYLES:
                add_summary([r for r in mt if r['style'] == style], summary, 'model_task_style', f'{model}|{tt}|{style}')

    summary_csv = run_dir / 'summary.csv'
    with summary_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(
            f,
            fieldnames=['group', 'value', 'n', 'exact_match', 'single_choice_acc', 'f1', 'jaccard', 'error_rate'],
        )
        w.writeheader()
        w.writerows(summary)

    # report
    lines = []
    lines.append('# Selected Datasets Paired Experiment Report')
    lines.append('')
    lines.append(f'- run_dir: {run_dir.as_posix()}')
    lines.append(f'- expected_calls: {expected_calls}')
    lines.append(f'- actual_calls: {len(results)}')
    lines.append(f'- seed: {args.seed}')
    lines.append(f'- samples_per_group: {args.samples_per_group}')
    lines.append(f'- styles: {", ".join(STYLES)}')
    lines.append(f'- models: {", ".join(m["model"] for m in models)}')
    lines.append('')

    lines.append('## Group Setup')
    lines.append('')
    lines.append('| group | dataset | folder | forced_task |')
    lines.append('|---|---|---|---|')
    for g in GROUP_SPECS:
        lines.append(f"| {g['group']} | {g['dataset']} | {g['folder']} | {g['forced_task'] or ''} |")
    lines.append('')

    lines.append('## Model x Style')
    lines.append('')
    lines.append('| model | style | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |')
    lines.append('|---|---|---:|---:|---:|---:|---:|---:|')
    for row in summary:
        if row['group'] != 'model_style':
            continue
        model, style = row['value'].split('|')
        lines.append(
            f"| {model} | {style} | {row['n']} | {row['exact_match']:.4f} | {row['single_choice_acc']:.4f} | {row['f1']:.4f} | {row['jaccard']:.4f} | {row['error_rate']:.4f} |"
        )
    lines.append('')

    lines.append('## Model x Group x Style')
    lines.append('')
    lines.append('| model | group | style | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |')
    lines.append('|---|---|---|---:|---:|---:|---:|---:|---:|')
    for row in summary:
        if row['group'] != 'model_group_style':
            continue
        model, group, style = row['value'].split('|')
        lines.append(
            f"| {model} | {group} | {style} | {row['n']} | {row['exact_match']:.4f} | {row['single_choice_acc']:.4f} | {row['f1']:.4f} | {row['jaccard']:.4f} | {row['error_rate']:.4f} |"
        )
    lines.append('')

    lines.append('## Covered Task Layers Comparison (T1-T5 in covered layers)')
    lines.append('')
    lines.append('| model | task_type | style | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |')
    lines.append('|---|---|---|---:|---:|---:|---:|---:|---:|')
    for row in summary:
        if row['group'] != 'model_task_style':
            continue
        model, tt, style = row['value'].split('|')
        lines.append(
            f"| {model} | {tt} | {style} | {row['n']} | {row['exact_match']:.4f} | {row['single_choice_acc']:.4f} | {row['f1']:.4f} | {row['jaccard']:.4f} | {row['error_rate']:.4f} |"
        )
    lines.append('')

    lines.append('## Analysis Notes')
    lines.append('')
    lines.append('- This run enforces strict paired evaluation: the same source_id is compared across 4 interaction styles.')
    lines.append('- TempReason is split into two groups: TempReason_T1(full_T1) and TempReason_T5(sample_T5), each sampled independently.')
    lines.append('- Use model_task_style table to compare model behavior over covered task layers (including T1 and T5).')

    (run_dir / 'report.md').write_text('\n'.join(lines), encoding='utf-8')

    print(f'done: {run_dir.as_posix()}')
    print(f'expected_calls: {expected_calls}')
    print(f'actual_calls: {len(results)}')


if __name__ == '__main__':
    main()
