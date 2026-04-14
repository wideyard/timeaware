import argparse
import csv
import json
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


def row_key(row):
    return (row['model'], row['dataset'], row['source_id'], row['style'])


def load_existing_predictions(pred_dir: Path):
    rows = []
    done = set()
    if not pred_dir.exists():
        return rows, done
    for fp in pred_dir.glob('*.jsonl'):
        for r in read_jsonl(fp):
            if not all(k in r for k in ['model', 'dataset', 'source_id', 'style']):
                continue
            k = row_key(r)
            if k in done:
                continue
            done.add(k)
            rows.append(r)
    return rows, done


def find_all_single_datasets():
    datasets = []
    for ds_dir in DATA_CONVERTED.iterdir():
        if not ds_dir.is_dir():
            continue
        fp = ds_dir / 'full' / f'{ds_dir.name}_single.jsonl'
        if fp.exists():
            datasets.append(ds_dir.name)
    return sorted(datasets)


def load_single_samples(dataset, max_per_dataset):
    fp = DATA_CONVERTED / dataset / 'full' / f'{dataset}_single.jsonl'
    rows = []
    seen = set()
    for obj in read_jsonl(fp):
        sid = str(obj.get('source_id', ''))
        if not sid or sid in seen:
            continue
        seen.add(sid)
        rows.append(obj)
        if len(rows) >= max_per_dataset:
            break
    return rows


def pick_conflict_anchor(options, gold_set):
    for o in options:
        k = str(o.get('key', '')).upper()
        if k and k not in gold_set:
            return k, o.get('text', '')
    if options:
        return str(options[0].get('key', '')).upper(), options[0].get('text', '')
    return 'A', ''


def build_conflict_messages(single_obj, variant):
    msgs = single_obj.get('messages', [])
    sys_msg = None
    user_msg = None

    for m in msgs:
        if m.get('role') == 'system' and sys_msg is None:
            sys_msg = m.get('content', '')
        if m.get('role') == 'user':
            user_msg = m.get('content', '')

    if not sys_msg:
        sys_msg = 'You are a careful reasoning assistant. Answer strictly based on the given context. Do not invent facts.'
    if not user_msg:
        user_msg = ''

    options = single_obj.get('options', [])
    gold_set = {str(x).upper() for x in single_obj.get('answer_key', [])}
    wrong_key, wrong_text = pick_conflict_anchor(options, gold_set)
    wrong_desc = f'{wrong_key} ({wrong_text.strip()})' if wrong_text else wrong_key

    if variant == 'multi_v1':
        body = [
            {'role': 'system', 'content': sys_msg},
            {'role': 'user', 'content': 'We discussed this item and got conflicting takes. Please help resolve it.\n\n' + user_msg},
            {
                'role': 'assistant',
                'content': f'Quick initial hypothesis: maybe {wrong_desc}, mostly based on one superficial temporal cue.',
            },
            {
                'role': 'user',
                'content': 'Do not follow that early hypothesis. Re-evaluate all options from the full context. Multiple options may be correct. Return only option letter(s).',
            },
        ]
        return body

    if variant == 'multi_v2':
        body = [
            {'role': 'system', 'content': sys_msg},
            {'role': 'user', 'content': 'I got contradictory instruction from teammates. Need a clean final answer.\n\n' + user_msg},
            {
                'role': 'assistant',
                'content': f'Teammate A said to pick a single safe option like {wrong_desc} and move on quickly.',
            },
            {
                'role': 'user',
                'content': 'Ignore that shortcut. We need the exact full set of correct options, not a single guess. Return only option letter(s).',
            },
        ]
        return body

    body = [
        {'role': 'system', 'content': sys_msg},
        {'role': 'user', 'content': 'Previous analyst summary may contain factual mistakes. Please re-check from source.\n\n' + user_msg},
        {
            'role': 'assistant',
            'content': f'Potentially wrong summary from previous analyst: the blank is likely {wrong_desc}.',
        },
        {
            'role': 'user',
            'content': 'Treat that summary as untrusted. Use only original context and options to derive the final answer. Return only option letter(s).',
        },
    ]
    return body


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
    out.append(
        {
            'group': group_name,
            'value': group_value,
            'n': n,
            'exact_match': round(exact, 6),
            'single_choice_acc': round(single_acc, 6),
            'f1': round(f1, 6),
            'jaccard': round(jaccard, 6),
            'error_rate': round(err_rate, 6),
        }
    )


def verdict(delta_em):
    if delta_em <= -0.02:
        return 'harder_than_single'
    if delta_em >= 0.02:
        return 'easier_than_single'
    return 'no_clear_difference'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-per-dataset', type=int, default=20)
    parser.add_argument('--datasets', type=str, default='')
    parser.add_argument('--run-id', type=str, default='')
    parser.add_argument('--workers', type=int, default=64)
    parser.add_argument('--retries', type=int, default=1)
    parser.add_argument('--timeout', type=int, default=30)
    args = parser.parse_args()

    models = parse_api_txt(ROOT / 'api.txt')
    if len(models) != 3:
        raise RuntimeError(f'Expected 3 models from api.txt, got {len(models)}')

    if args.datasets:
        datasets = [x.strip() for x in args.datasets.split(',') if x.strip()]
    else:
        datasets = find_all_single_datasets()

    if not datasets:
        raise RuntimeError('No datasets selected.')

    exp_root = DATA_CONVERTED / 'experiments'
    if args.run_id:
        run_dir = exp_root / args.run_id
    else:
        run_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_dir = exp_root / f'run_paired_conflict_{run_ts}'
    pred_dir = run_dir / 'predictions'
    pred_dir.mkdir(parents=True, exist_ok=True)

    all_rows, done_keys = load_existing_predictions(pred_dir)

    pair_rows = []
    for ds in datasets:
        single_samples = load_single_samples(ds, args.max_per_dataset)
        for s in single_samples:
            sid = str(s.get('source_id', ''))
            if not sid:
                continue
            pair_rows.append({'dataset': ds, 'source_id': sid, 'sample': s})

    if not pair_rows:
        raise RuntimeError('No paired samples selected.')

    tasks = []
    for p in pair_rows:
        for style in STYLES:
            if style == 'single':
                messages = p['sample'].get('messages', [])
            else:
                messages = build_conflict_messages(p['sample'], style)
            for m in models:
                k = (m['model'], p['dataset'], p['source_id'], style)
                if k in done_keys:
                    continue
                tasks.append(
                    {
                        'dataset': p['dataset'],
                        'source_id': p['source_id'],
                        'style': style,
                        'messages': messages,
                        'options': p['sample'].get('options', []),
                        'gold_keys': [str(x).upper() for x in p['sample'].get('answer_key', [])],
                        'model_cfg': m,
                    }
                )

    expected_calls = len(pair_rows) * len(STYLES) * len(models)

    run_cfg = {
        'run_dir': run_dir.as_posix(),
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'datasets': datasets,
        'max_per_dataset': args.max_per_dataset,
        'styles': STYLES,
        'models': [m['model'] for m in models],
        'paired_samples': len(pair_rows),
        'expected_calls': expected_calls,
        'note': 'multi_v1-v3 are regenerated as task-conflict multi-turn prompts for strict paired comparison.',
    }
    (run_dir / 'run_config.json').write_text(json.dumps(run_cfg, ensure_ascii=False, indent=2), encoding='utf-8')

    results = list(all_rows)
    completed = 0

    model_files = {}
    for m in models:
        fp = pred_dir / f"{safe_model_name(m['model'])}.jsonl"
        model_files[m['model']] = fp.open('a', encoding='utf-8')

    def run_one(t):
        raw, err = call_with_retry(
            t['model_cfg'],
            t['messages'],
            retries=args.retries,
            timeout=args.timeout,
        )
        pred_keys = extract_predicted_keys(raw or '', t['options']) if raw else []
        pred_set = set(pred_keys)
        gold_set = set(t['gold_keys'])
        exact = int(pred_set == gold_set)
        single_acc = int(len(gold_set) == 1 and pred_set == gold_set)
        f1, jaccard = f1_and_jaccard(pred_set, gold_set)
        return {
            'dataset': t['dataset'],
            'source_id': t['source_id'],
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
            k = row_key(row)
            if k in done_keys:
                continue
            done_keys.add(k)
            results.append(row)
            mf = model_files[row['model']]
            mf.write(json.dumps(row, ensure_ascii=False) + '\n')
            mf.flush()
            completed += 1
            if completed % 100 == 0:
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

    for model in sorted(by_model.keys()):
        mr = [r for r in results if r['model'] == model]
        add_summary(mr, summary, 'model', model)
        for style in STYLES:
            add_summary([r for r in mr if r['style'] == style], summary, 'model_style', f'{model}|{style}')

    for model in sorted(by_model.keys()):
        for ds in datasets:
            mdr = [r for r in results if r['model'] == model and r['dataset'] == ds]
            add_summary(mdr, summary, 'model_dataset', f'{model}|{ds}')
            for style in STYLES:
                add_summary(
                    [r for r in mdr if r['style'] == style],
                    summary,
                    'model_dataset_style',
                    f'{model}|{ds}|{style}',
                )

    summary_csv = run_dir / 'summary.csv'
    with summary_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(
            f,
            fieldnames=['group', 'value', 'n', 'exact_match', 'single_choice_acc', 'f1', 'jaccard', 'error_rate'],
        )
        w.writeheader()
        w.writerows(summary)

    # Paired degradation analysis
    idx = {}
    for r in results:
        idx[(r['model'], r['dataset'], r['source_id'], r['style'])] = r

    deg_rows = []
    deg_rollup = defaultdict(list)

    for model in sorted(by_model.keys()):
        for ds in datasets:
            for style in ['multi_v1', 'multi_v2', 'multi_v3']:
                pairs = []
                for p in pair_rows:
                    if p['dataset'] != ds:
                        continue
                    sid = p['source_id']
                    base = idx.get((model, ds, sid, 'single'))
                    alt = idx.get((model, ds, sid, style))
                    if not base or not alt:
                        continue
                    pairs.append((base, alt))

                if not pairs:
                    continue

                n = len(pairs)
                em_single = sum(x[0]['exact_match'] for x in pairs) / n
                em_style = sum(x[1]['exact_match'] for x in pairs) / n
                f1_single = sum(x[0]['f1'] for x in pairs) / n
                f1_style = sum(x[1]['f1'] for x in pairs) / n
                delta_em = em_style - em_single
                delta_f1 = f1_style - f1_single

                worse = sum(1 for b, a in pairs if a['exact_match'] < b['exact_match'])
                better = sum(1 for b, a in pairs if a['exact_match'] > b['exact_match'])
                equal = n - worse - better

                row = {
                    'model': model,
                    'dataset': ds,
                    'style': style,
                    'n_pairs': n,
                    'em_single': round(em_single, 6),
                    'em_style': round(em_style, 6),
                    'delta_em': round(delta_em, 6),
                    'f1_single': round(f1_single, 6),
                    'f1_style': round(f1_style, 6),
                    'delta_f1': round(delta_f1, 6),
                    'worse_count': worse,
                    'better_count': better,
                    'equal_count': equal,
                    'worse_rate': round(worse / n, 6),
                    'verdict': verdict(delta_em),
                }
                deg_rows.append(row)
                deg_rollup[(model, style)].append(row)

    # model-style rollup over datasets
    for model in sorted(by_model.keys()):
        for style in ['multi_v1', 'multi_v2', 'multi_v3']:
            rows = deg_rollup.get((model, style), [])
            if not rows:
                continue
            n = sum(r['n_pairs'] for r in rows)
            em_single = sum(r['em_single'] * r['n_pairs'] for r in rows) / n
            em_style = sum(r['em_style'] * r['n_pairs'] for r in rows) / n
            f1_single = sum(r['f1_single'] * r['n_pairs'] for r in rows) / n
            f1_style = sum(r['f1_style'] * r['n_pairs'] for r in rows) / n
            worse = sum(r['worse_count'] for r in rows)
            better = sum(r['better_count'] for r in rows)
            equal = sum(r['equal_count'] for r in rows)
            deg_rows.append(
                {
                    'model': model,
                    'dataset': '__ALL__',
                    'style': style,
                    'n_pairs': n,
                    'em_single': round(em_single, 6),
                    'em_style': round(em_style, 6),
                    'delta_em': round(em_style - em_single, 6),
                    'f1_single': round(f1_single, 6),
                    'f1_style': round(f1_style, 6),
                    'delta_f1': round(f1_style - f1_single, 6),
                    'worse_count': worse,
                    'better_count': better,
                    'equal_count': equal,
                    'worse_rate': round(worse / n, 6),
                    'verdict': verdict(em_style - em_single),
                }
            )

    deg_csv = run_dir / 'degradation_report.csv'
    with deg_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                'model',
                'dataset',
                'style',
                'n_pairs',
                'em_single',
                'em_style',
                'delta_em',
                'f1_single',
                'f1_style',
                'delta_f1',
                'worse_count',
                'better_count',
                'equal_count',
                'worse_rate',
                'verdict',
            ],
        )
        w.writeheader()
        w.writerows(deg_rows)

    report = []
    report.append('# Paired Conflict Multi-Turn Experiment Report')
    report.append('')
    report.append(f'- run_dir: {run_dir.as_posix()}')
    report.append(f'- paired_samples: {len(pair_rows)}')
    report.append(f'- expected_calls: {expected_calls}')
    report.append(f'- actual_calls: {len(results)}')
    report.append(f'- styles: {", ".join(STYLES)}')
    report.append(f'- models: {", ".join(m["model"] for m in models)}')
    report.append('- strict_pairing: same dataset + same source_id forced across 4 styles')
    report.append('- multi_turn_design: task-conflict (misleading prior hypothesis / conflicting instruction), not casual chit-chat')
    report.append('')

    report.append('## Model Overall')
    report.append('')
    report.append('| model | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |')
    report.append('|---|---:|---:|---:|---:|---:|---:|')
    for row in summary:
        if row['group'] != 'model':
            continue
        report.append(
            f"| {row['value']} | {row['n']} | {row['exact_match']:.4f} | {row['single_choice_acc']:.4f} | {row['f1']:.4f} | {row['jaccard']:.4f} | {row['error_rate']:.4f} |"
        )
    report.append('')

    report.append('## Paired Degradation (ALL datasets)')
    report.append('')
    report.append('| model | style | n_pairs | em_single | em_style | delta_em | f1_single | f1_style | delta_f1 | worse_rate | verdict |')
    report.append('|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|')
    for row in deg_rows:
        if row['dataset'] != '__ALL__':
            continue
        report.append(
            f"| {row['model']} | {row['style']} | {row['n_pairs']} | {row['em_single']:.4f} | {row['em_style']:.4f} | {row['delta_em']:.4f} | {row['f1_single']:.4f} | {row['f1_style']:.4f} | {row['delta_f1']:.4f} | {row['worse_rate']:.4f} | {row['verdict']} |"
        )
    report.append('')

    report.append('## Answer: Is multi-turn really harder?')
    report.append('')
    all_rollups = [r for r in deg_rows if r['dataset'] == '__ALL__']
    harder = sum(1 for r in all_rollups if r['delta_em'] < 0)
    easier = sum(1 for r in all_rollups if r['delta_em'] > 0)
    neutral = len(all_rollups) - harder - easier
    report.append(f'- rollup_count: {len(all_rollups)} (3 models x 3 multi styles)')
    report.append(f'- harder_cases(delta_em<0): {harder}')
    report.append(f'- easier_cases(delta_em>0): {easier}')
    report.append(f'- neutral_cases(delta_em=0): {neutral}')
    if harder > easier:
        report.append('- conclusion: In this strict paired setup, task-conflict multi-turn is overall harder than single.')
    elif easier > harder:
        report.append('- conclusion: In this strict paired setup, task-conflict multi-turn is not harder overall; several styles become easier or similar.')
    else:
        report.append('- conclusion: In this strict paired setup, no clear overall difficulty difference between task-conflict multi-turn and single.')
    report.append('')

    (run_dir / 'report.md').write_text('\n'.join(report), encoding='utf-8')

    print(f'done: {run_dir.as_posix()}')
    print(f'paired_samples: {len(pair_rows)}')
    print(f'expected_calls: {expected_calls}')
    print(f'actual_calls: {len(results)}')


if __name__ == '__main__':
    main()
