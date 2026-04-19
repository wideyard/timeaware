import json
import re
from pathlib import Path

ROOT = Path('data-converted')
MARKER_RE = re.compile(r'^\s*(A|B|用户|对方)\s*:\s*(.*)$')
MARKER_TO_ROLE = {
    'A': 'user',
    'B': 'assistant',
    '用户': 'user',
    '对方': 'assistant',
}


def should_skip(path: Path) -> bool:
    p = path.as_posix()
    return '/experiments/' in p


def split_content_with_markers(content: str):
    lines = content.splitlines()
    marker_idxs = []
    marker_keys = []

    for i, ln in enumerate(lines):
        m = MARKER_RE.match(ln)
        if m:
            marker_idxs.append(i)
            marker_keys.append(m.group(1))

    if len(marker_idxs) < 2:
        return None

    # Require at least two distinct speaker markers to reduce false positives.
    if len(set(marker_keys)) < 2:
        return None

    first_idx = marker_idxs[0]
    last_idx = marker_idxs[-1]

    pre = '\n'.join(lines[:first_idx]).strip()
    block = lines[first_idx:last_idx + 1]
    post = '\n'.join(lines[last_idx + 1:]).strip()

    out = []
    if pre:
        out.append({'role': 'user', 'content': pre})

    residue = []
    for ln in block:
        m = MARKER_RE.match(ln)
        if m:
            if residue:
                txt = '\n'.join(residue).strip()
                if txt:
                    out.append({'role': 'user', 'content': txt})
                residue = []
            speaker = m.group(1)
            text = m.group(2).strip()
            out.append({'role': MARKER_TO_ROLE[speaker], 'content': text})
        else:
            residue.append(ln)

    if residue:
        txt = '\n'.join(residue).strip()
        if txt:
            out.append({'role': 'user', 'content': txt})

    if post:
        out.append({'role': 'user', 'content': post})

    return out if out else None


def transform_obj(obj):
    messages = obj.get('messages')
    if not isinstance(messages, list) or not messages:
        return obj, False

    changed = False
    new_messages = []

    for m in messages:
        role = m.get('role')
        content = m.get('content')

        if role != 'user' or not isinstance(content, str):
            new_messages.append(m)
            continue

        if ':' not in content:
            new_messages.append(m)
            continue

        repl = split_content_with_markers(content)
        if repl is None:
            new_messages.append(m)
            continue

        new_messages.extend(repl)
        changed = True

    if changed:
        obj['messages'] = new_messages
    return obj, changed


def process_file(path: Path):
    total = 0
    changed = 0
    out_lines = []

    with path.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except Exception:
                out_lines.append(line)
                continue

            obj, ch = transform_obj(obj)
            if ch:
                changed += 1
            out_lines.append(json.dumps(obj, ensure_ascii=False))

    if changed > 0:
        with path.open('w', encoding='utf-8', newline='\n') as f:
            for line in out_lines:
                f.write(line + '\n')

    return total, changed


def main():
    changed_files = []
    total_files = 0

    for path in ROOT.rglob('*.jsonl'):
        if should_skip(path):
            continue
        total_files += 1
        total, changed = process_file(path)
        if changed > 0:
            changed_files.append((path.as_posix(), total, changed))

    print(f'total_files_scanned={total_files}')
    print(f'files_changed={len(changed_files)}')
    for p, total, changed in changed_files:
        print(f'{p}\ttotal={total}\tchanged={changed}')


if __name__ == '__main__':
    main()
