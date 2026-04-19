#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run benchmark experiment across all T1-T4 task tiers.

Design:
  - 3 models from api.txt
  - 4 task tiers (T1-T4), all datasets per tier
  - 2 styles: single (single_turn) and multi (randomly pick one of v1/v2/v3 per sample)
  - single and multi have equal sample counts
  - 20 samples per dataset per style
  - Output: per-sample predictions JSONL + summary CSV + analysis report MD
"""

import csv
import json
import random
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

# Only two styles: single and multi (multi picks randomly from v1/v2/v3 per sample)
STYLES = ['single', 'multi']
MULTI_VARIANTS = ['multi_v1', 'multi_v2', 'multi_v3']

STYLE_TO_SUFFIX = {
    'single': '_single.jsonl',
    'multi_v1': '_multi_v1.jsonl',
    'multi_v2': '_multi_v2.jsonl',
    'multi_v3': '_multi_v3.jsonl',
}

# T1-T4 task tiers
TASK_TIERS = ['T1', 'T2', 'T3', 'T4']

TASK_TAG_RE = re.compile(r'^T[1-4]$')

SEED = 42


# ──────────────────────────── API helpers ────────────────────────────

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


# ──────────────────────────── Evaluation helpers ────────────────────────────

def normalize_text(s: str) -> str:
    s = (s or '').strip().lower()
    s = re.sub(r'[`\"\'\(\)\[\]{}<>]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def map_gold_keys(answer_key, options):
    """Map answer_key values to option letter keys.

    Handles both letter-based answer_keys (e.g. ['A', 'B']) and
    text-based answer_keys (e.g. ['January 31, 1948'], ['yes']).
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

    # 1) Letter extraction
    letter_hits = re.findall(r'\b([A-Z])\b', text.upper())
    preds = []
    for k in letter_hits:
        if k in valid_keys and k not in preds:
            preds.append(k)
    if preds:
        return preds

    # 2) Fuzzy text matching
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

    # 3) yes/no fallback
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


# ──────────────────────────── Dataset resolution ────────────────────────────

def resolve_dataset_folder(dataset: str, folder: str, preferred_task: str | None = None) -> Path:
    """Resolve a dataset+tier to its data directory.

    For a dataset like MCTACO called with folder='sample', preferred_task='T1':
      1. Try MCTACO/sample_T1 (exact match with task tag)
      2. Try MCTACO/sample (plain folder)
      3. If neither exists, try MCTACO/full_T1 (fallback to full)
      4. Try MCTACO/full (plain full folder)
    """
    ds_dir = DATA_CONVERTED / dataset
    if not ds_dir.exists():
        raise RuntimeError(f'Dataset directory not found: {ds_dir.as_posix()}')

    # Step 1: Try sample_T{tier} if tier specified
    if preferred_task and TASK_TAG_RE.match(str(preferred_task)):
        tagged = ds_dir / f'{folder}_{preferred_task}'
        if tagged.exists():
            return tagged

    # Step 2: Try plain folder (e.g. MCTACO/sample)
    exact = ds_dir / folder
    if exact.exists():
        return exact

    # Step 3: Fallback from sample to full
    if folder == 'sample':
        fallback_folder = 'full'
    elif folder == 'full':
        fallback_folder = 'sample'
    else:
        fallback_folder = None

    if fallback_folder:
        # Try fallback_folder_T{tier}
        if preferred_task and TASK_TAG_RE.match(str(preferred_task)):
            fallback_tagged = ds_dir / f'{fallback_folder}_{preferred_task}'
            if fallback_tagged.exists():
                return fallback_tagged

        # Try plain fallback folder
        fallback_exact = ds_dir / fallback_folder
        if fallback_exact.exists():
            return fallback_exact

    # Step 4: Search all subdirectories for matching pattern
    cand = []
    for p in ds_dir.iterdir():
        if p.is_dir() and re.fullmatch(rf'{re.escape(folder)}_T[1-4]', p.name):
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


# ──────────────────────────── Data loading ────────────────────────────

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


def discover_datasets():
    """Discover all datasets with sample/full directories across T1-T4.

    Some datasets appear in multiple task tiers (e.g. MCTACO has T1 and T4,
    TempReason has T1 and T4, UDST-DurationQA has T1 and T4).
    Each dataset-tier combination is a separate entry.
    Prefers sample directory, falls back to full directory if sample doesn't exist.
    """
    # Map each dataset to ALL its task tiers
    DATASET_TIERS = {
        # T1
        'TimeDial': ['T1'], 'TimeQA': ['T1'], 'TempReason': ['T1', 'T4'],
        'UDST-DurationQA': ['T1', 'T4'], 'MCTACO': ['T1', 'T4'],
        # T2
        'tracie': ['T2'], 'PIQA': ['T2'], 'HellaSwag': ['T2'], 'pasta': ['T2'],
        # T3
        'SocialIQA': ['T3'], 'CosmosQA': ['T3'], 'DROP': ['T3'],
        'narrative-qa': ['T3'], 'qasper': ['T3'], 'SI-Bench': ['T3'],
    }

    datasets = []

    for ds_dir in sorted(DATA_CONVERTED.iterdir()):
        if not ds_dir.is_dir() or ds_dir.name == 'experiments':
            continue
        ds_name = ds_dir.name

        tiers = DATASET_TIERS.get(ds_name)
        if not tiers:
            continue

        for tier in tiers:
            # Try sample directory first, fall back to full
            data_dir = None
            try:
                data_dir = resolve_dataset_folder(ds_name, 'sample', preferred_task=tier)
            except RuntimeError:
                pass

            if data_dir is None:
                try:
                    data_dir = resolve_dataset_folder(ds_name, 'full', preferred_task=tier)
                except RuntimeError:
                    continue

            datasets.append({
                'name': ds_name,
                'tier': tier,
                'data_dir': data_dir,
            })

    return datasets


def load_samples(dataset_name, style, data_dir, k, preferred_task, rng):
    """Load up to k samples for a given dataset and style.

    For 'multi' style, randomly picks one of v1/v2/v3 per sample.
    Returns list of (sample_dict, actual_style_used).
    """
    if style == 'single':
        suffix = STYLE_TO_SUFFIX['single']
        fp = data_dir / f'{dataset_name}{suffix}'
        if not fp.exists():
            # Try with dataset name variations (TEMPREASON vs TempReason)
            candidates = list(data_dir.glob(f'*{suffix}'))
            if candidates:
                fp = candidates[0]
            else:
                return []

        results = []
        seen = set()
        for obj in read_jsonl(fp):
            sid = str(obj.get('source_id', ''))
            if not sid or sid in seen:
                continue
            seen.add(sid)
            results.append((obj, 'single'))
            if len(results) >= k:
                break
        return results

    elif style == 'multi':
        # For each sample, randomly pick one of v1/v2/v3
        all_variants = {}
        for variant in MULTI_VARIANTS:
            suffix = STYLE_TO_SUFFIX[variant]
            fp = data_dir / f'{dataset_name}{suffix}'
            if not fp.exists():
                candidates = list(data_dir.glob(f'*{suffix}'))
                if candidates:
                    fp = candidates[0]
                else:
                    continue
            all_variants[variant] = {}
            for obj in read_jsonl(fp):
                sid = str(obj.get('source_id', ''))
                if sid:
                    all_variants[variant][sid] = obj

        if not all_variants:
            return []

        # Collect all source IDs shared across available variants
        available_variants = list(all_variants.keys())
        if not available_variants:
            return []

        all_sids = set(all_variants[available_variants[0]].keys())
        for v in available_variants[1:]:
            all_sids &= set(all_variants[v].keys())

        sids = sorted(all_sids)
        rng.shuffle(sids)

        results = []
        for sid in sids:
            variant = rng.choice(available_variants)
            results.append((all_variants[variant][sid], variant))
            if len(results) >= k:
                break
        return results

    return []


# ──────────────────────────── Main ────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Run benchmark experiment (single + random multi)')
    parser.add_argument('--samples', type=int, default=20, help='Number of samples per dataset per style')
    parser.add_argument('--workers', type=int, default=16, help='Number of parallel workers')
    parser.add_argument('--retries', type=int, default=2, help='Number of retries on API failure')
    parser.add_argument('--timeout', type=int, default=60, help='API call timeout in seconds')
    parser.add_argument('--seed', type=int, default=SEED, help='Random seed for reproducibility')
    parser.add_argument('--run-id', type=str, default='', help='Custom run ID (default: auto-generated)')
    args = parser.parse_args()

    rng = random.Random(args.seed)

    models = parse_api_txt(ROOT / 'api.txt')
    if len(models) != 3:
        print(f'Warning: Expected 3 models, got {len(models)}. Proceeding anyway.')

    datasets = discover_datasets()
    if not datasets:
        print('ERROR: No datasets found!')
        return

    print(f'Datasets discovered: {len(datasets)}')
    for ds in datasets:
        print(f'  {ds["name"]:20s} tier={ds["tier"]}')

    print(f'Models: {[m["model"] for m in models]}')
    print(f'Styles: {STYLES} (multi randomly picks from {MULTI_VARIANTS})')
    print(f'Samples per dataset per style: {args.samples}')

    # ─── Create run directory ───
    exp_root = DATA_CONVERTED / 'experiments'
    if args.run_id:
        run_dir = exp_root / args.run_id
    else:
        run_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_dir = exp_root / f'run_{run_ts}'

    pred_dir = run_dir / 'predictions'
    pred_dir.mkdir(parents=True, exist_ok=True)

    # ─── Build task list ───
    tasks = []
    sample_log = []  # Track which variant was used for each multi sample

    for ds in datasets:
        ds_name = ds['name']
        tier = ds['tier']
        data_dir = ds['data_dir']

        for style in STYLES:
            samples = load_samples(ds_name, style, data_dir, args.samples, preferred_task=tier, rng=rng)
            for sample, actual_variant in samples:
                sid = str(sample.get('source_id', ''))
                for model_cfg in models:
                    tasks.append({
                        'dataset': ds_name,
                        'tier': tier,
                        'source_id': sid,
                        'style': style,
                        'actual_variant': actual_variant,
                        'sample': sample,
                        'model_cfg': model_cfg,
                    })
                if style == 'single':
                    sample_log.append({
                        'dataset': ds_name, 'tier': tier, 'source_id': sid,
                        'style': 'single', 'actual_variant': 'single',
                    })
                else:
                    sample_log.append({
                        'dataset': ds_name, 'tier': tier, 'source_id': sid,
                        'style': 'multi', 'actual_variant': actual_variant,
                    })

    print(f'\nTotal API calls to make: {len(tasks)}')
    print(f'  Datasets: {len(datasets)}')
    print(f'  Samples per dataset per style: {args.samples}')
    print(f'  Styles: {STYLES}')

    # ─── Save run config ───
    run_cfg = {
        'run_dir': run_dir.as_posix(),
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'samples_per_dataset_per_style': args.samples,
        'styles': STYLES,
        'multi_variants': MULTI_VARIANTS,
        'models': [m['model'] for m in models],
        'datasets': [{'name': ds['name'], 'tier': ds['tier']} for ds in datasets],
        'seed': args.seed,
        'total_tasks': len(tasks),
    }
    (run_dir / 'run_config.json').write_text(
        json.dumps(run_cfg, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    # ─── Build resume key function ───
    def row_key(r):
        return (r['model'], r['dataset'], r['tier'], r['source_id'], r['style'])

    # ─── Load existing predictions for resume ───
    all_rows = []
    done_keys = set()
    for fp in pred_dir.glob('*.jsonl'):
        for line in fp.open('r', encoding='utf-8', errors='ignore'):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                all_rows.append(r)
                done_keys.add(row_key(r))
            except Exception:
                continue

    if done_keys:
        print(f'Resuming: found {len(done_keys)} existing predictions, skipping them.')

    # ─── Open output files for streaming writes ───
    model_files = {}
    for m in models:
        mname = m['model']
        fp = pred_dir / f'{safe_model_name(mname)}.jsonl'
        # Append mode for resume
        model_files[mname] = fp.open('a', encoding='utf-8')

    # ─── Filter out already-done tasks ───
    remaining_tasks = []
    for t in tasks:
        k = (t['model_cfg']['model'], t['dataset'], t['tier'], t['source_id'], t['style'])
        if k not in done_keys:
            remaining_tasks.append(t)

    print(f'\nTotal tasks: {len(tasks)}, already done: {len(done_keys)}, remaining: {len(remaining_tasks)}')

    completed_new = 0
    lock = threading.Lock()

    def run_one(task):
        ds, sid, style = task['dataset'], task['source_id'], task['style']
        actual_variant = task['actual_variant']
        model_cfg = task['model_cfg']
        sample = task['sample']
        mname = model_cfg['model']

        raw, err = call_with_retry(model_cfg, sample.get('messages', []), retries=args.retries, timeout=args.timeout)
        pred_keys = extract_predicted_keys(raw or '', sample.get('options', [])) if raw else []
        gold_keys = map_gold_keys(sample.get('answer_key', []), sample.get('options', []))
        pred_set = set(pred_keys)
        gold_set = set(gold_keys)
        exact = int(pred_set == gold_set)
        single_acc = int(len(gold_set) == 1 and pred_set == gold_set)
        f1, jaccard = f1_and_jaccard(pred_set, gold_set)

        return {
            'dataset': ds,
            'tier': task['tier'],
            'source_id': sid,
            'style': style,
            'actual_variant': actual_variant,
            'model': mname,
            'prediction_raw': raw,
            'prediction_keys': sorted(pred_set),
            'gold_keys': sorted(gold_set),
            'exact_match': exact,
            'single_choice_acc': single_acc,
            'f1': f1,
            'jaccard': jaccard,
            'error': err,
        }

    interrupted = False
    try:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
            futures = [ex.submit(run_one, t) for t in remaining_tasks]
            for fut in as_completed(futures):
                row = fut.result()
                k = row_key(row)
                with lock:
                    if k in done_keys:
                        continue
                    all_rows.append(row)
                    done_keys.add(k)
                    # Stream write to per-model file
                    mf = model_files[row['model']]
                    mf.write(json.dumps(row, ensure_ascii=False) + '\n')
                    mf.flush()
                    completed_new += 1
                    if completed_new % 10 == 0:
                        progress = {
                            'timestamp': datetime.now().isoformat(timespec='seconds'),
                            'new_completed': completed_new,
                            'total_saved': len(all_rows),
                            'total_tasks': len(tasks),
                        }
                        (run_dir / 'progress.json').write_text(
                            json.dumps(progress, ensure_ascii=False, indent=2), encoding='utf-8'
                        )
                        print(f'progress: new={completed_new}, total_saved={len(all_rows)}, remaining={len(tasks)-len(all_rows)}')
    except KeyboardInterrupt:
        interrupted = True
        print('Interrupted! Partial results saved and can be resumed.')
    finally:
        for fh in model_files.values():
            try:
                fh.close()
            except Exception:
                pass

    # Save sample log (which multi variant was used for each sample)
    log_path = run_dir / 'sample_variant_log.json'
    with log_path.open('w', encoding='utf-8') as f:
        json.dump(sample_log, f, ensure_ascii=False, indent=2)

    # ─── Summary & Analysis ───
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

    # Overall
    add_summary('overall', 'all', all_rows)

    # Per model
    models_in_results = sorted(set(r['model'] for r in all_rows))
    for m in models_in_results:
        mr = [r for r in all_rows if r['model'] == m]
        add_summary('model', m, mr)

        # Per model x style
        for style in STYLES:
            sr = [r for r in mr if r['style'] == style]
            add_summary('model_style', f'{m}|{style}', sr)

        # Per model x tier
        for tier in TASK_TIERS:
            tr = [r for r in mr if r['tier'] == tier]
            add_summary('model_tier', f'{m}|{tier}', tr)

            # Per model x tier x style
            for style in STYLES:
                tsr = [r for r in tr if r['style'] == style]
                add_summary('model_tier_style', f'{m}|{tier}|{style}', tsr)

    # Per tier
    for tier in TASK_TIERS:
        tr = [r for r in all_rows if r['tier'] == tier]
        add_summary('tier', tier, tr)
        for style in STYLES:
            tsr = [r for r in tr if r['style'] == style]
            add_summary('tier_style', f'{tier}|{style}', tsr)

    # Per dataset
    for ds in datasets:
        dn = ds['name']
        dr = [r for r in all_rows if r['dataset'] == dn]
        add_summary('dataset', dn, dr)
        for style in STYLES:
            dsr = [r for r in dr if r['style'] == style]
            add_summary('dataset_style', f'{dn}|{style}', dsr)

    # Per style
    for style in STYLES:
        sr = [r for r in all_rows if r['style'] == style]
        add_summary('style', style, sr)

    # Save summary CSV
    summary_csv = run_dir / 'summary.csv'
    with summary_csv.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['group', 'value', 'n', 'exact_match', 'single_choice_acc', 'f1', 'jaccard', 'error_rate']
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    # ─── Analysis Report ───
    lines = []
    lines.append('# Benchmark Experiment Report (Single vs Random Multi)')
    lines.append('')
    lines.append(f'- run_dir: {run_dir.as_posix()}')
    lines.append(f'- created_at: {run_cfg["created_at"]}')
    lines.append(f'- datasets: {len(datasets)}')
    lines.append(f'- samples_per_dataset_per_style: {args.samples}')
    lines.append(f'- styles: {STYLES} (multi randomly picks from {MULTI_VARIANTS})')
    lines.append(f'- seed: {args.seed}')
    lines.append(f'- total_predictions: {len(all_rows)}')
    lines.append(f'- models: {", ".join(m["model"] for m in models)}')
    lines.append('')

    # 1. Overall Performance
    lines.append('## 1. Overall Performance')
    lines.append('')
    lines.append('| model | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|')
    for row in summary_rows:
        if row['group'] != 'model':
            continue
        lines.append(
            f"| {row['value']} | {row['n']} | {row['exact_match']:.4f} | "
            f"{row['single_choice_acc']:.4f} | {row['f1']:.4f} | {row['jaccard']:.4f} | {row['error_rate']:.4f} |"
        )
    lines.append('')

    # 2. Style Comparison (single vs multi)
    lines.append('## 2. Style Comparison: Single vs Multi')
    lines.append('')
    lines.append('| model | style | n | exact_match | single_choice_acc | f1 | jaccard | error_rate |')
    lines.append('|---|---|---:|---:|---:|---:|---:|---:|')
    for row in summary_rows:
        if row['group'] != 'model_style':
            continue
        lines.append(
            f"| {row['value'].split('|')[0]} | {row['value'].split('|')[1]} | {row['n']} | "
            f"{row['exact_match']:.4f} | {row['single_choice_acc']:.4f} | {row['f1']:.4f} | "
            f"{row['jaccard']:.4f} | {row['error_rate']:.4f} |"
        )
    lines.append('')

    # 3. Performance by Task Tier
    lines.append('## 3. Performance by Task Tier')
    lines.append('')
    lines.append('| tier | n | exact_match | single_choice_acc | f1 | jaccard |')
    lines.append('|---|---:|---:|---:|---:|---:|')
    for row in summary_rows:
        if row['group'] != 'tier':
            continue
        lines.append(
            f"| {row['value']} | {row['n']} | {row['exact_match']:.4f} | "
            f"{row['single_choice_acc']:.4f} | {row['f1']:.4f} | {row['jaccard']:.4f} |"
        )
    lines.append('')

    # 4. Model × Tier × Style breakdown
    lines.append('## 4. Model × Tier × Style Breakdown')
    lines.append('')
    lines.append('| model | tier | style | n | exact_match | single_choice_acc | f1 | jaccard |')
    lines.append('|---|---|---|---:|---:|---:|---:|---:|')
    for row in summary_rows:
        if row['group'] != 'model_tier_style':
            continue
        parts = row['value'].split('|')
        lines.append(
            f"| {parts[0]} | {parts[1]} | {parts[2]} | {row['n']} | "
            f"{row['exact_match']:.4f} | {row['single_choice_acc']:.4f} | "
            f"{row['f1']:.4f} | {row['jaccard']:.4f} |"
        )
    lines.append('')

    # 5. Style Degradation Analysis
    lines.append('## 5. Style Degradation Analysis (multi vs single)')
    lines.append('')
    lines.append('How much does multi-turn noise degrade performance compared to single-turn?')
    lines.append('')

    # Compute degradation per model
    for m in sorted(model_to_rows.keys()):
        mr = [r for r in all_rows if r['model'] == m]
        single_rows_m = [r for r in mr if r['style'] == 'single']
        multi_rows_m = [r for r in mr if r['style'] == 'multi']

        if not single_rows_m or not multi_rows_m:
            continue

        single_acc = sum(r['exact_match'] for r in single_rows_m) / len(single_rows_m)
        multi_acc = sum(r['exact_match'] for r in multi_rows_m) / len(multi_rows_m)
        degradation = single_acc - multi_acc

        lines.append(f'### {m}')
        lines.append(f'- Single exact_match: {single_acc:.4f} ({len(single_rows_m)} samples)')
        lines.append(f'- Multi exact_match: {multi_acc:.4f} ({len(multi_rows_m)} samples)')
        lines.append(f'- Degradation: {degradation:+.4f} ({degradation/single_acc*100:+.1f}% relative)' if single_acc > 0 else f'- Degradation: N/A')
        lines.append('')

    # 6. Per-Dataset Results
    lines.append('## 6. Per-Dataset Results')
    lines.append('')
    lines.append('| dataset | tier | style | n | exact_match | single_choice_acc | f1 | jaccard |')
    lines.append('|---|---|---|---:|---:|---:|---:|---:|')
    for ds in datasets:
        for style in STYLES:
            key = f"{ds['name']}|{style}"
            for row in summary_rows:
                if row['group'] == 'dataset_style' and row['value'] == key:
                    lines.append(
                        f"| {ds['name']} | {ds['tier']} | {style} | {row['n']} | "
                        f"{row['exact_match']:.4f} | {row['single_choice_acc']:.4f} | "
                        f"{row['f1']:.4f} | {row['jaccard']:.4f} |"
                    )
    lines.append('')

    # Write report
    (run_dir / 'report.md').write_text('\n'.join(lines), encoding='utf-8')

    # Save progress
    progress = {
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'new_completed': completed_new,
        'total_saved': len(all_rows),
        'total_tasks': len(tasks),
        'interrupted': interrupted,
    }
    (run_dir / 'progress.json').write_text(
        json.dumps(progress, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    print(f'\ndone: {run_dir.as_posix()}')
    print(f'total_predictions: {len(all_rows)}')
    print(f'report: {(run_dir / "report.md").as_posix()}')


if __name__ == '__main__':
    main()