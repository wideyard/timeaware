"""
Fix answer_key format in T4 (formerly T5) counterfactual dataset JSONL files.

For counterfactual datasets (TempReason, MCTACO, UDST-DurationQA in their T4 task),
the answer_key field previously stored the option TEXT content (e.g., "January 31, 1948",
"yes", "no") instead of the option LETTER key (e.g., "A", "B"). This script converts
text-based answer_key values to their corresponding letter keys.

Note: After task restructure (T5→T4), directory names changed from *_T5 to *_T4.

Usage: python fix_t5_answer_keys.py
"""

import json
import re
from pathlib import Path

DATA_CONVERTED = Path(__file__).parent / 'data-converted'

# T4 (formerly T5) counterfactual dataset files
# Note: directories were renamed from *_T5 to *_T4 after task restructure
T4_FILES = [
    'MCTACO/full_T4/MCTACO_full.jsonl',
    'MCTACO/sample_T4/MCTACO_multi_v1.jsonl',
    'MCTACO/sample_T4/MCTACO_multi_v2.jsonl',
    'MCTACO/sample_T4/MCTACO_multi_v3.jsonl',
    'MCTACO/sample_T4/MCTACO_single.jsonl',
    'TempReason/sample_T4/TEMPREASON_multi_v1.jsonl',
    'TempReason/sample_T4/TEMPREASON_multi_v2.jsonl',
    'TempReason/sample_T4/TEMPREASON_multi_v3.jsonl',
    'TempReason/sample_T4/TEMPREASON_single.jsonl',
    'UDST-DurationQA/full_T4/UDST_full.jsonl',
    'UDST-DurationQA/sample_T4/UDST_multi_v1.jsonl',
    'UDST-DurationQA/sample_T4/UDST_multi_v2.jsonl',
    'UDST-DurationQA/sample_T4/UDST_multi_v3.jsonl',
    'UDST-DurationQA/sample_T4/UDST_single.jsonl',
]


def normalize_text(s):
    s = (s or '').strip().lower()
    s = re.sub(r'[`"\'()\[\]{}<>]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def map_answer_key_to_letters(answer_key, options):
    """Convert text-based answer_key values to their corresponding option letter keys."""
    key_to_text = {str(o.get('key', '')).upper(): normalize_text(str(o.get('text', ''))) for o in options}
    text_to_key = {v: k for k, v in key_to_text.items() if v}
    
    result = []
    for a in answer_key:
        s = str(a).strip()
        if not s:
            continue
        
        # Already a letter key
        s_up = s.upper()
        if s_up in key_to_text:
            result.append(s_up)
            continue
        
        # Try exact normalized text match
        ns = normalize_text(s)
        if ns in text_to_key:
            result.append(text_to_key[ns])
            continue
        
        # Fallback: fuzzy text matching
        matched = False
        for k, t in key_to_text.items():
            if not t:
                continue
            if ns == t or ns in t or t in ns:
                result.append(k)
                matched = True
                break
        
        if not matched:
            # Could not map - keep original
            result.append(s)
    
    return result


def fix_file(rel_path):
    fp = DATA_CONVERTED / rel_path
    if not fp.exists():
        print(f"  SKIP: {fp} does not exist")
        return 0, 0
    
    lines = fp.read_text(encoding='utf-8').splitlines()
    fixed_count = 0
    total_count = 0
    
    new_lines = []
    for line in lines:
        if not line.strip():
            new_lines.append(line)
            continue
        
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            new_lines.append(line)
            continue
        
        total_count += 1
        ak = obj.get('answer_key', [])
        opts = obj.get('options', [])
        
        if not opts or not ak:
            new_lines.append(line)
            continue
        
        # Check if any answer_key value is text (not a letter key)
        opt_key_set = {str(o.get('key', '')).upper() for o in opts}
        needs_fix = any(str(a).strip().upper() not in opt_key_set for a in ak)
        
        if not needs_fix:
            new_lines.append(line)
            continue
        
        # Fix: map text answers to letter keys
        new_ak = map_answer_key_to_letters(ak, opts)
        obj['answer_key'] = new_ak
        new_lines.append(json.dumps(obj, ensure_ascii=False))
        fixed_count += 1
    
    # Write back
    fp.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
    print(f"  FIXED: {rel_path}: {fixed_count}/{total_count} records fixed")
    return fixed_count, total_count


def main():
    total_fixed = 0
    total_records = 0
    
    print("Fixing T4 (counterfactual) answer_key format: converting text-based values to letter keys")
    print("=" * 70)
    
    for rel_path in T4_FILES:
        fixed, total = fix_file(rel_path)
        total_fixed += fixed
        total_records += total
    
    print("=" * 70)
    print(f"Done! Fixed {total_fixed}/{total_records} records across {len(T4_FILES)} files.")
    
    # Verify: check that no text-based answer_keys remain
    print("\nVerification: scanning for remaining text-based answer_keys...")
    issues_found = False
    
    for rel_path in T4_FILES:
        fp = DATA_CONVERTED / rel_path
        if not fp.exists():
            continue
        with fp.open('r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ak = obj.get('answer_key', [])
                opts = obj.get('options', [])
                if not opts or not ak:
                    continue
                opt_key_set = {str(o.get('key', '')).upper() for o in opts}
                for a in ak:
                    if str(a).strip().upper() not in opt_key_set:
                        print(f"  WARNING: {rel_path}:{i} answer_key={ak} contains non-letter value")
                        issues_found = True
                        break
    
    if not issues_found:
        print("  All answer_key values are now letter keys. No issues found.")
    else:
        print("  Some issues remain - please review the warnings above.")


if __name__ == '__main__':
    main()