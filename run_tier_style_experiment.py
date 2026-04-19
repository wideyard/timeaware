import argparse
import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib import error, request

ROOT = Path('.')
DATA_CONVERTED = ROOT / 'data-converted'
STYLE_TO_SUFFIX = {
    'single': '_single.jsonl',
    'multi_v1': '_multi_v1.jsonl',
    'multi_v2': '_multi_v2.jsonl',
    'multi_v3': '_multi_v3.jsonl',
}
STYLES = ['single', 'multi_v1', 'multi_v2', 'multi_v3']

TASK_TAG_RE = re.compile(r'^T[1-4]$')


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
            time.sleep(min(2 ** i, 3))
    return None, last_err


def normalize_text(s: str) -> str:
    s = (s or '').strip().lower()
    s = re.sub(r'[`\"\'\(\)\[\]{}<>]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def map_gold_keys(answer_key, options):
    """Map answer_key values to option letter keys.

    Handles both letter-based answer_keys (e.g. ['A', 'B']) and
    text-based answer_keys (e.g. ['January 31, 1948'], ['yes']).
    For text-based values, finds the matching option by its text content
    and returns the corresponding letter key.
    """
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


def resolve_dataset_folder(dataset: str, folder: str, preferred_task: str | None = None) -> Path:
    ds_dir = DATA_CONVERTED / dataset
    if not ds_dir.exists():
        raise RuntimeError(f'Dataset directory not found: {ds_dir.as_posix()}')

    exact = ds_dir / folder
    if exact.exists():
        return exact

    if preferred_task and TASK_TAG_RE.match(str(preferred_task)):
        tagged = ds_dir / f'{folder}_{preferred_task}'
        if tagged.exists():
            return tagged

    cand = []
    for p in ds_dir.iterdir():
        if p.is_dir() and re.fullmatch(rf'{re.escape(folder)}_T[1-5]', p.name):
            cand.append(p)

    if preferred_task and TASK_TAG_RE.match(str(preferred_task)):
        want = f'{folder}_{preferred_task}'
        for p in cand:
            if p.name == want:
                return p

    if len(cand) == 1:
        return cand[0]

    raise RuntimeError(
        f'Cannot resolve folder for dataset={dataset}, folder={folder}, preferred_task={preferred_task}. '
        f'Candidates={[p.name for p in sorted(cand)]}'
    )


def load_tier_style_map(path: Path):
    rows = []
    with path.open('r', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append({
                'tier': r['tier'],
                'style': r['style'],
                'dataset': r['hardest_dataset'],
            })
    return rows


def pick_samples(dataset, style, k, preferred_task=None):
    full_dir = resolve_dataset_folder(dataset, 'full', preferred_task=preferred_task)
    fp = full_dir / f'{dataset}{STYLE_TO_SUFFIX[style]}'
    picked = []
    seen = set()
    for obj in read_jsonl(fp):
        sid = str(obj.get('source_id', ''))
        if not sid or sid in seen:
            continue
        seen.add(sid)
        picked.append(obj)
        if len(picked) >= k:
            break
    if len(picked) < k:
        raise RuntimeError(f'{dataset} {style} only has {len(picked)} samples, need {k}')
    return picked


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', type=str, default='')
    parser.add_argument('--samples-per-cell', type=int, default=20)
    parser.add_argument('--workers', type=int, default=48)
    parser.add_argument('--retries', type=int, default=1)
    parser.add_argument('--timeout', type=int, default=30)
    parser.add_argument(
        '--tier-style-csv',
        type=str,
        default='data-converted/experiments/run_20260413_193954/tier_style_hardest.csv',
    )
    args = parser.parse_args()

    models = parse_api_txt(ROOT / 'api.txt')
    if len(models) != 3:
        raise RuntimeError(f'Expected 3 models from api.txt, got {len(models)}')

    tier_style = load_tier_style_map(ROOT / args.tier_style_csv)
    if len(tier_style) != 20:
        raise RuntimeError(f'Expected 20 tier-style rows (5x4), got {len(tier_style)}')

    exp_root = DATA_CONVERTED / 'experiments'
    if args.run_id:
        run_dir = exp_root / args.run_id
    else:
        run_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_dir = exp_root / f'run_tierstyle_{run_ts}'
    pred_dir = run_dir / 'predictions'
    pred_dir.mkdir(parents=True, exist_ok=True)

    tasks = []
    for cell in tier_style:
        tier = cell['tier']
        style = cell['style']
        dataset = cell['dataset']
        samples = pick_samples(dataset, style, args.samples_per_cell, preferred_task=tier)
        for s in samples:
            sid = str(s.get('source_id', ''))
            for m in models:
                tasks.append({
                    'tier': tier,
                    'style': style,
                    'dataset': dataset,
                    'source_id': sid,
                    'sample': s,
                    'model_cfg': m,
                })

    expected_calls = 5 * 4 * args.samples_per_cell * len(models)
    if len(tasks) != expected_calls:
        raise RuntimeError(f'Expected {expected_calls} tasks, got {len(tasks)}')

    run_cfg = {
        'run_dir': run_dir.as_posix(),
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'samples_per_cell': args.samples_per_cell,
        'models': [m['model'] for m in models],
        'expected_calls': expected_calls,
        'tier_style_csv': args.tier_style_csv,
    }
    (run_dir / 'run_config.json').write_text(json.dumps(run_cfg, ensure_ascii=False, indent=2), encoding='utf-8')

    results = []
    completed = 0

    def run_one(t):
        m = t['model_cfg']
        raw, err = call_with_retry(m, t['sample'].get('messages', []), retries=args.retries, timeout=args.timeout)
        pred_keys = extract_predicted_keys(raw or '', t['sample'].get('options', [])) if raw else []
        gold_keys = map_gold_keys(t['sample'].get('answer_key', []), t['sample'].get('options', []))
        pred_set = set(pred_keys)
        gold_set = set(gold_keys)
        exact = int(pred_set == gold_set)
        single_acc = int(len(gold_set) == 1 and pred_set == gold_set)
        f1, jaccard = f1_and_jaccard(pred_set, gold_set)
        return {
            'tier': t['tier'],
            'style': t['style'],
            'dataset': t['dataset'],
            'source_id': t['source_id'],
            'model': m['model'],
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
            completed += 1
            if completed % 50 == 0:
                print(f'progress: {completed}/{expected_calls}')

    by_model = {}
    for r in results:
        by_model.setdefault(r['model'], []).append(r)
    for model, rows in by_model.items():
        fp = pred_dir / f'{safe_model_name(model)}.jsonl'
        with fp.open('w', encoding='utf-8') as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')

    summary = []
    add_summary(results, summary, 'overall', 'all')

    for m in sorted(by_model.keys()):
        mr = [r for r in results if r['model'] == m]
        add_summary(mr, summary, 'model', m)
        for style in STYLES:
            add_summary([r for r in mr if r['style'] == style], summary, 'model_style', f'{m}|{style}')

    for tier in ['T1', 'T2', 'T3', 'T4']:
        tr = [r for r in results if r['tier'] == tier]
        add_summary(tr, summary, 'tier', tier)
        for style in STYLES:
            ts = [r for r in tr if r['style'] == style]
            add_summary(ts, summary, 'tier_style', f'{tier}|{style}')
            for m in sorted(by_model.keys()):
                tsm = [r for r in ts if r['model'] == m]
                add_summary(tsm, summary, 'model_tier_style', f'{m}|{tier}|{style}')

    summary_csv = run_dir / 'summary.csv'
    with summary_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(
            f,
            fieldnames=['group', 'value', 'n', 'exact_match', 'single_choice_acc', 'f1', 'jaccard', 'error_rate'],
        )
        w.writeheader()
        w.writerows(summary)

    report_lines = []
    report_lines.append('# Tier-Style Hardest Dataset Experiment Report')
    report_lines.append('')
    report_lines.append(f'- run_dir: {run_dir.as_posix()}')
    report_lines.append(f'- expected_calls: {expected_calls}')
    report_lines.append(f'- actual_calls: {len(results)}')
    report_lines.append(f'- tiers: T1, T2, T3, T4')
    report_lines.append(f'- styles: {", ".join(STYLES)}')
    report_lines.append(f'- models: {", ".join(m["model"] for m in models)}')
    report_lines.append('')

    report_lines.append('## Tier-Style Dataset Mapping')
    report_lines.append('')
    report_lines.append('| tier | style | dataset |')
    report_lines.append('|---|---|---|')
    for cell in sorted(tier_style, key=lambda x: (x['tier'], x['style'])):
        report_lines.append(f"| {cell['tier']} | {cell['style']} | {cell['dataset']} |")
    report_lines.append('')

    report_lines.append('## Model x Tier x Style')
    report_lines.append('')
    report_lines.append('| model | tier | style | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |')
    report_lines.append('|---|---|---|---:|---:|---:|---:|---:|---:|')
    for row in summary:
        if row['group'] != 'model_tier_style':
            continue
        model, tier, style = row['value'].split('|')
        report_lines.append(
            f"| {model} | {tier} | {style} | {row['n']} | {row['exact_match']:.4f} | {row['single_choice_acc']:.4f} | {row['f1']:.4f} | {row['jaccard']:.4f} | {row['error_rate']:.4f} |"
        )
    report_lines.append('')

    report_lines.append('## Model Overall')
    report_lines.append('')
    report_lines.append('| model | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |')
    report_lines.append('|---|---:|---:|---:|---:|---:|---:|')
    for row in summary:
        if row['group'] != 'model':
            continue
        report_lines.append(
            f"| {row['value']} | {row['n']} | {row['exact_match']:.4f} | {row['single_choice_acc']:.4f} | {row['f1']:.4f} | {row['jaccard']:.4f} | {row['error_rate']:.4f} |"
        )
    report_lines.append('')

    (run_dir / 'report.md').write_text('\n'.join(report_lines), encoding='utf-8')

    print(f'done: {run_dir.as_posix()}')
    print(f'expected_calls: {expected_calls}')
    print(f'actual_calls: {len(results)}')


if __name__ == '__main__':
    main()
