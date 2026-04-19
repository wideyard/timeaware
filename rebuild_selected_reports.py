import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

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


def normalize_text(s: str) -> str:
    return ' '.join((s or '').strip().lower().split())


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


def build_gold_mapping():
    gold = {}
    for spec in GROUP_SPECS:
        base_dir = resolve_dataset_folder(spec['dataset'], spec['folder'], spec['forced_task'])
        style_files = resolve_style_files(base_dir)
        for style, fp in style_files.items():
            for obj in read_jsonl(fp):
                sid = str(obj.get('source_id', ''))
                k = (spec['dataset'], spec['folder'], style, sid)
                gold[k] = map_gold_keys(obj.get('answer_key', []), obj.get('options', []))
    return gold


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', type=str, required=True)
    args = parser.parse_args()

    run_dir = DATA_CONVERTED / 'experiments' / args.run_id
    pred_dir = run_dir / 'predictions'
    if not pred_dir.exists():
        raise RuntimeError(f'predictions dir not found: {pred_dir.as_posix()}')

    run_cfg = json.loads((run_dir / 'run_config.json').read_text(encoding='utf-8'))
    expected_calls = int(run_cfg.get('expected_calls', 0))
    models = run_cfg.get('models', [])

    gold_map = build_gold_mapping()

    results = []
    for pred_file in pred_dir.glob('*.jsonl'):
        for row in read_jsonl(pred_file):
            pred_keys = sorted(set(str(x).upper() for x in row.get('prediction_keys', [])))
            gk = (
                str(row.get('dataset', '')),
                str(row.get('folder', '')),
                str(row.get('style', '')),
                str(row.get('source_id', '')),
            )
            gold_keys = sorted(set(gold_map.get(gk, [])))

            pred_set = set(pred_keys)
            gold_set = set(gold_keys)
            exact = int(pred_set == gold_set)
            single_acc = int(len(gold_set) == 1 and pred_set == gold_set)
            f1, jaccard = f1_and_jaccard(pred_set, gold_set)

            row['gold_keys'] = sorted(gold_set)
            row['exact_match'] = exact
            row['single_choice_acc'] = single_acc
            row['f1'] = f1
            row['jaccard'] = jaccard
            results.append(row)

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

    groups = [g['group'] for g in GROUP_SPECS]
    for model in sorted(by_model.keys()):
        for group in groups:
            mgrp = [r for r in results if r['model'] == model and r['group'] == group]
            add_summary(mgrp, summary, 'model_group', f'{model}|{group}')
            for style in STYLES:
                add_summary([r for r in mgrp if r['style'] == style], summary, 'model_group_style', f'{model}|{group}|{style}')

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

    lines = []
    lines.append('# Selected Datasets Paired Experiment Report')
    lines.append('')
    lines.append(f'- run_dir: {run_dir.as_posix()}')
    lines.append(f'- expected_calls: {expected_calls}')
    lines.append(f'- actual_calls: {len(results)}')
    lines.append(f"- seed: {run_cfg.get('seed', '')}")
    lines.append(f"- samples_per_group: {run_cfg.get('samples_per_group', '')}")
    lines.append(f"- styles: {', '.join(run_cfg.get('styles', STYLES))}")
    lines.append(f"- models: {', '.join(models)}")
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
    lines.append('- This report is regenerated from saved predictions with corrected gold mapping: answer_key is first mapped to options.key.')
    lines.append('- This run enforces strict paired evaluation: the same source_id is compared across 4 interaction styles.')
    lines.append('- TempReason is split into two groups: TempReason_T1(full_T1) and TempReason_T5(sample_T5), each sampled independently.')
    lines.append('- Use model_task_style table to compare model behavior over covered task layers (including T1 and T5).')

    (run_dir / 'report.md').write_text('\n'.join(lines), encoding='utf-8')

    print(f'done: {run_dir.as_posix()}')
    print(f'rows: {len(results)}')
    print(f'summary: {summary_csv.as_posix()}')
    print(f"report: {(run_dir / 'report.md').as_posix()}")


if __name__ == '__main__':
    main()
