import csv
import json
import re
import time
import argparse
import threading
from datetime import datetime
from pathlib import Path
from urllib import request, error
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path('.')
DATA_CONVERTED = ROOT / 'data-converted'

STYLES = ['single', 'multi_v1', 'multi_v2', 'multi_v3']
STYLE_TO_SUFFIX = {
    'single': '_single.jsonl',
    'multi_v1': '_multi_v1.jsonl',
    'multi_v2': '_multi_v2.jsonl',
    'multi_v3': '_multi_v3.jsonl',
}

TASK_TAG_RE = re.compile(r'^T[1-4]$')


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


def post_chat_completion(base_url, api_key, model, messages, temperature=0.0, timeout=120):
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


def call_with_retry(model_cfg, messages, retries=0, timeout=20):
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


def extract_predicted_keys(raw_text, options):
    text = (raw_text or '').strip()
    if not text:
        return []

    key_to_text = {o['key'].upper(): o.get('text', '') for o in options}
    valid_keys = set(key_to_text.keys())

    # 1) Letter extraction: A / B / A,B / B.No
    letter_hits = re.findall(r'\b([A-Z])\b', text.upper())
    preds = []
    for k in letter_hits:
        if k in valid_keys and k not in preds:
            preds.append(k)
    if preds:
        return preds

    # 2) Fuzzy text matching against option text
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

    # 3) no/yes fallbacks
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


def find_datasets_with_full():
    datasets = []
    for ds_dir in DATA_CONVERTED.iterdir():
        if not ds_dir.is_dir():
            continue
        try:
            full_dir = resolve_dataset_folder(ds_dir.name, 'full')
        except Exception:
            continue
        has_all = True
        for suffix in STYLE_TO_SUFFIX.values():
            fp = full_dir / f'{ds_dir.name}{suffix}'
            if not fp.exists():
                has_all = False
                break
        if has_all:
            datasets.append(ds_dir.name)
    return sorted(datasets)


def load_style_maps(dataset):
    full_dir = resolve_dataset_folder(dataset, 'full')
    style_maps = {}
    for style in STYLES:
        fp = full_dir / f'{dataset}{STYLE_TO_SUFFIX[style]}'
        m = {}
        for obj in read_jsonl(fp):
            sid = str(obj.get('source_id', ''))
            if sid and sid not in m:
                m[sid] = obj
        style_maps[style] = m
    return style_maps


def load_style_maps_limited(dataset, max_per_dataset):
    full_dir = resolve_dataset_folder(dataset, 'full')

    # pick candidate source_ids from single file in order
    single_fp = full_dir / f'{dataset}{STYLE_TO_SUFFIX["single"]}'
    source_ids = []
    seen = set()
    for obj in read_jsonl(single_fp):
        sid = str(obj.get('source_id', ''))
        if not sid or sid in seen:
            continue
        seen.add(sid)
        source_ids.append(sid)
        if len(source_ids) >= max_per_dataset:
            break

    target = set(source_ids)
    style_maps = {}
    for style in STYLES:
        fp = full_dir / f'{dataset}{STYLE_TO_SUFFIX[style]}'
        m = {}
        for obj in read_jsonl(fp):
            sid = str(obj.get('source_id', ''))
            if sid in target and sid not in m:
                m[sid] = obj
                if len(m) >= len(target):
                    break
        style_maps[style] = m

    return style_maps


def pick_source_ids(style_maps, max_per_dataset):
    sets = [set(style_maps[s].keys()) for s in STYLES]
    common = sorted(set.intersection(*sets)) if sets else []
    return common[:max_per_dataset]


def safe_model_name(model):
    return re.sub(r'[^a-zA-Z0-9._-]+', '_', model)


def write_jsonl(path: Path, rows):
    with path.open('w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def row_key(row):
    return (row['model'], row['dataset'], row['source_id'], row['style'])


def load_existing_predictions(pred_dir: Path):
    rows = []
    done = set()
    if not pred_dir.exists():
        return rows, done
    for fp in pred_dir.glob('*.jsonl'):
        name = fp.name
        if name.startswith('source_style_comparison_'):
            continue
        for r in read_jsonl(fp):
            if not all(k in r for k in ['model', 'dataset', 'source_id', 'style']):
                continue
            k = row_key(r)
            if k in done:
                continue
            done.add(k)
            rows.append(r)
    return rows, done


def latest_run_dir(base: Path):
    if not base.exists():
        return None
    cands = [p for p in base.iterdir() if p.is_dir() and p.name.startswith('run_')]
    if not cands:
        return None
    return sorted(cands, key=lambda p: p.name)[-1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-per-dataset', type=int, default=20)
    parser.add_argument('--run-id', type=str, default='', help='Resume or write into data-converted/experiments/<run-id>')
    parser.add_argument('--resume-latest', action='store_true', help='Resume latest existing run_* directory')
    parser.add_argument('--workers', type=int, default=6, help='Concurrent API workers')
    args = parser.parse_args()

    models = parse_api_txt(ROOT / 'api.txt')
    if len(models) != 3:
        raise RuntimeError(f'Expected 3 models from api.txt, got {len(models)}')

    datasets = find_datasets_with_full()
    if not datasets:
        raise RuntimeError('No eligible full datasets found in data-converted')

    exp_root = DATA_CONVERTED / 'experiments'
    if args.run_id:
        run_dir = exp_root / args.run_id
    elif args.resume_latest:
        latest = latest_run_dir(exp_root)
        if latest is None:
            run_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            run_dir = exp_root / f'run_{run_ts}'
        else:
            run_dir = latest
    else:
        run_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_dir = exp_root / f'run_{run_ts}'

    pred_dir = run_dir / 'predictions'
    pred_dir.mkdir(parents=True, exist_ok=True)

    all_rows, done_keys = load_existing_predictions(pred_dir)

    run_cfg = {
        'run_dir': run_dir.as_posix(),
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'max_per_dataset': args.max_per_dataset,
        'styles': STYLES,
        'models': [m['model'] for m in models],
        'datasets': datasets,
    }
    (run_dir / 'run_config.json').write_text(json.dumps(run_cfg, ensure_ascii=False, indent=2), encoding='utf-8')

    model_files = {}
    for m in models:
        mname = m['model']
        fp = pred_dir / f'{safe_model_name(mname)}.jsonl'
        model_files[mname] = fp.open('a', encoding='utf-8')

    completed_new = 0
    total_target = len(datasets) * args.max_per_dataset * len(STYLES) * len(models)

    tasks = []
    for ds in datasets:
        style_maps = load_style_maps_limited(ds, args.max_per_dataset)
        source_ids = pick_source_ids(style_maps, args.max_per_dataset)
        for sid in source_ids:
            for style in STYLES:
                sample = style_maps[style][sid]
                for model_cfg in models:
                    k = (model_cfg['model'], ds, sid, style)
                    if k in done_keys:
                        continue
                    tasks.append((ds, sid, style, sample, model_cfg))

    lock = threading.Lock()

    def run_one(task):
        ds, sid, style, sample, model_cfg = task
        raw, err = call_with_retry(model_cfg, sample.get('messages', []), retries=0, timeout=20)
        pred_keys = extract_predicted_keys(raw or '', sample.get('options', [])) if raw else []
        gold_keys = map_gold_keys(sample.get('answer_key', []), sample.get('options', []))
        pred_set = set(pred_keys)
        gold_set = set(gold_keys)
        exact = int(pred_set == gold_set)
        single_acc = int(len(gold_set) == 1 and pred_set == gold_set)
        f1, jaccard = f1_and_jaccard(pred_set, gold_set)
        row = {
            'dataset': ds,
            'source_id': sid,
            'style': style,
            'model': model_cfg['model'],
            'prediction_raw': raw,
            'prediction_keys': sorted(pred_set),
            'gold_keys': sorted(gold_set),
            'exact_match': exact,
            'single_choice_acc': single_acc,
            'f1': f1,
            'jaccard': jaccard,
            'error': err,
        }
        return row

    interrupted = False
    try:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
            futures = [ex.submit(run_one, t) for t in tasks]
            for fut in as_completed(futures):
                row = fut.result()
                with lock:
                    k = row_key(row)
                    if k in done_keys:
                        continue
                    all_rows.append(row)
                    done_keys.add(k)
                    mf = model_files[row['model']]
                    mf.write(json.dumps(row, ensure_ascii=False) + '\n')
                    mf.flush()
                    completed_new += 1
                    if completed_new % 25 == 0:
                        progress = {
                            'timestamp': datetime.now().isoformat(timespec='seconds'),
                            'new_completed': completed_new,
                            'total_saved': len(all_rows),
                            'total_target_upper_bound': total_target,
                        }
                        (run_dir / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding='utf-8')
                        print(f"progress: new_completed={completed_new}, total_saved={len(all_rows)}")
    except KeyboardInterrupt:
        interrupted = True
        print('Interrupted by user. Partial results were saved and can be resumed.')
    finally:
        for fh in model_files.values():
            try:
                fh.close()
            except Exception:
                pass

    # Predictions by model
    model_to_rows = {}
    for r in all_rows:
        model_to_rows.setdefault(r['model'], []).append(r)

    for model, rows in model_to_rows.items():
        write_jsonl(pred_dir / f'{safe_model_name(model)}.jsonl', rows)

    # Summary csv
    summary_rows = []

    def add_summary(group_name, group_value, rows):
        n = len(rows)
        if n == 0:
            return
        exact = sum(r['exact_match'] for r in rows) / n
        single_rows = [r for r in rows if len(r['gold_keys']) == 1]
        single_acc = (sum(r['single_choice_acc'] for r in single_rows) / len(single_rows)) if single_rows else 0.0
        f1 = sum(r['f1'] for r in rows) / n
        jaccard = sum(r['jaccard'] for r in rows) / n
        err_rate = sum(1 for r in rows if r['error']) / n
        summary_rows.append({
            'group': group_name,
            'value': group_value,
            'n': n,
            'exact_match': round(exact, 6),
            'single_choice_acc': round(single_acc, 6),
            'f1': round(f1, 6),
            'jaccard': round(jaccard, 6),
            'error_rate': round(err_rate, 6),
        })

    add_summary('overall', 'all', all_rows)

    # model x style
    for model in sorted(model_to_rows.keys()):
        model_rows = [r for r in all_rows if r['model'] == model]
        for style in STYLES:
            rows = [r for r in model_rows if r['style'] == style]
            add_summary('model_style', f'{model}|{style}', rows)

    # model x style x dataset
    for model in sorted(model_to_rows.keys()):
        for style in STYLES:
            for ds in datasets:
                rows = [r for r in all_rows if r['model'] == model and r['style'] == style and r['dataset'] == ds]
                add_summary('model_style_dataset', f'{model}|{style}|{ds}', rows)

    summary_csv = run_dir / 'summary.csv'
    with summary_csv.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['group', 'value', 'n', 'exact_match', 'single_choice_acc', 'f1', 'jaccard', 'error_rate']
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    # Per-model source-style comparison tables
    comparison_paths = []
    for model in sorted(model_to_rows.keys()):
        rows = [r for r in all_rows if r['model'] == model]
        by_key = {}
        for r in rows:
            key = (r['dataset'], r['source_id'])
            by_key.setdefault(key, {})[r['style']] = r

        comp_csv = pred_dir / f'source_style_comparison_{safe_model_name(model)}.csv'
        comparison_paths.append((model, comp_csv))
        with comp_csv.open('w', newline='', encoding='utf-8') as f:
            fields = [
                'dataset', 'source_id', 'gold',
                'single_pred', 'single_em',
                'multi_v1_pred', 'multi_v1_em',
                'multi_v2_pred', 'multi_v2_em',
                'multi_v3_pred', 'multi_v3_em',
            ]
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for (ds, sid), m in sorted(by_key.items()):
                gold = sorted(next(iter(m.values()))['gold_keys']) if m else []
                def pred(style):
                    rr = m.get(style)
                    return ','.join(rr['prediction_keys']) if rr else ''
                def em(style):
                    rr = m.get(style)
                    return rr['exact_match'] if rr else ''
                writer.writerow({
                    'dataset': ds,
                    'source_id': sid,
                    'gold': ','.join(gold),
                    'single_pred': pred('single'),
                    'single_em': em('single'),
                    'multi_v1_pred': pred('multi_v1'),
                    'multi_v1_em': em('multi_v1'),
                    'multi_v2_pred': pred('multi_v2'),
                    'multi_v2_em': em('multi_v2'),
                    'multi_v3_pred': pred('multi_v3'),
                    'multi_v3_em': em('multi_v3'),
                })

    # Markdown report
    report_md = run_dir / 'report.md'
    lines = []
    lines.append('# Batch Experiment Report')
    lines.append('')
    lines.append(f'- run_dir: {run_dir.as_posix()}')
    lines.append(f'- datasets: {len(datasets)}')
    lines.append(f'- max_per_dataset: {args.max_per_dataset}')
    lines.append(f'- styles: {", ".join(STYLES)}')
    lines.append(f'- models: {", ".join(m["model"] for m in models)}')
    lines.append('')

    lines.append('## Overall by Model and Style')
    lines.append('')
    lines.append('| model | style | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|---:|')
    for row in summary_rows:
        if row['group'] != 'model_style':
            continue
        model, style = row['value'].split('|', 1)
        lines.append(
            f"| {model} | {style} | {row['n']} | {row['exact_match']:.4f} | {row['single_choice_acc']:.4f} | {row['f1']:.4f} | {row['jaccard']:.4f} | {row['error_rate']:.4f} |"
        )
    lines.append('')

    lines.append('## Dataset Breakdown (model_style_dataset)')
    lines.append('')
    lines.append('| model | style | dataset | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |')
    lines.append('|---|---|---|---:|---:|---:|---:|---:|---:|')
    for row in summary_rows:
        if row['group'] != 'model_style_dataset':
            continue
        model, style, ds = row['value'].split('|', 2)
        lines.append(
            f"| {model} | {style} | {ds} | {row['n']} | {row['exact_match']:.4f} | {row['single_choice_acc']:.4f} | {row['f1']:.4f} | {row['jaccard']:.4f} | {row['error_rate']:.4f} |"
        )
    lines.append('')

    lines.append('## Source-Level Cross-Style Comparison Tables')
    lines.append('')
    for model, comp_path in comparison_paths:
        lines.append(f'- {model}: {comp_path.as_posix()}')
    lines.append('')

    report_md.write_text('\n'.join(lines), encoding='utf-8')

    progress = {
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'new_completed': completed_new,
        'total_saved': len(all_rows),
        'total_target_upper_bound': total_target,
        'interrupted': interrupted,
    }
    (run_dir / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'done: {run_dir.as_posix()}')
    print(f'total_predictions: {len(all_rows)}')
    print(f'new_predictions_this_run: {completed_new}')


if __name__ == '__main__':
    main()
