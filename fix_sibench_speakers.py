import json
import re
from pathlib import Path

BASE = Path('data-converted/SI-Bench/full_T4')
FILES = [
    BASE / 'SI-Bench_single.jsonl',
    BASE / 'SI-Bench_multi_v1.jsonl',
    BASE / 'SI-Bench_multi_v2.jsonl',
    BASE / 'SI-Bench_multi_v3.jsonl',
]

DIALOGUE_LINE = re.compile(r'^\s*(用户|对方)\s*:\s*(.*)$')


def split_dialogue_lines(block: str):
    turns = []
    residue = []
    for raw in block.splitlines():
        m = DIALOGUE_LINE.match(raw)
        if m:
            role = 'user' if m.group(1) == '用户' else 'assistant'
            turns.append({'role': role, 'content': m.group(2).strip()})
        else:
            residue.append(raw)
    return turns, '\n'.join(residue).strip()


def split_single_user_message(content: str):
    key_ctx = '\n\n原文：\n'
    key_q = '\n\n问题：'
    if key_ctx not in content or key_q not in content:
        return None

    head, rest = content.split(key_ctx, 1)
    if key_q not in rest:
        return None

    ctx, qtail = rest.split(key_q, 1)
    turns, residue = split_dialogue_lines(ctx)
    if not turns:
        return None

    out = []
    if head.strip():
        out.append({'role': 'user', 'content': head.strip()})
    out.extend(turns)
    if residue:
        out.append({'role': 'user', 'content': residue})
    out.append({'role': 'user', 'content': '问题：' + qtail})
    return out


def split_multi_context_message(content: str):
    lines = content.splitlines()
    first_idx = None
    last_idx = None

    for i, ln in enumerate(lines):
        if DIALOGUE_LINE.match(ln):
            if first_idx is None:
                first_idx = i
            last_idx = i

    if first_idx is None:
        return None

    pre = '\n'.join(lines[:first_idx]).strip()
    dia = '\n'.join(lines[first_idx:last_idx + 1]).strip()
    post = '\n'.join(lines[last_idx + 1:]).strip()

    turns, residue = split_dialogue_lines(dia)
    if not turns:
        return None

    out = []
    if pre:
        out.append({'role': 'user', 'content': pre})
    out.extend(turns)
    if residue:
        out.append({'role': 'user', 'content': residue})
    if post:
        out.append({'role': 'user', 'content': post})
    return out


def transform_obj(obj):
    msgs = obj.get('messages', [])
    if not msgs:
        return obj, False

    changed = False
    new_msgs = []

    for idx, m in enumerate(msgs):
        role = m.get('role')
        content = m.get('content', '')

        if role != 'user' or '用户:' not in content or '对方:' not in content:
            new_msgs.append(m)
            continue

        replacement = None
        if idx == 1 and msgs[0].get('role') == 'system':
            replacement = split_single_user_message(content)
        else:
            replacement = split_multi_context_message(content)

        if replacement:
            new_msgs.extend(replacement)
            changed = True
        else:
            new_msgs.append(m)

    if changed:
        obj['messages'] = new_msgs
    return obj, changed


def process_file(path: Path):
    changed_count = 0
    total = 0
    out_lines = []

    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.strip():
                continue
            total += 1
            obj = json.loads(line)
            obj, changed = transform_obj(obj)
            if changed:
                changed_count += 1
            out_lines.append(json.dumps(obj, ensure_ascii=False))

    with path.open('w', encoding='utf-8', newline='\n') as f:
        for line in out_lines:
            f.write(line + '\n')

    return total, changed_count


def main():
    for fp in FILES:
        if not fp.exists():
            print(f'skip missing: {fp.as_posix()}')
            continue
        total, changed = process_file(fp)
        print(f'{fp.as_posix()} total={total} changed={changed}')


if __name__ == '__main__':
    main()
