#!/usr/bin/env python3
import json
import re

with open('data-converted/TimeDial/sample_T5/TIMEDIAL_single.jsonl', encoding='utf-8') as f:
    samples = [json.loads(line) for line in f]

print('=== TIMEDIAL Method C (Unit Change) - Verification ===\n')

method_c_samples = []
for i, sample in enumerate(samples[:30]):
    msgs = sample.get('messages', [])
    rule_applied = sample.get('metadata', {}).get('rule_applied', '')
    
    if 'Time unit' not in rule_applied:
        continue
    
    # Extract rule
    rule_desc = ''
    for msg in msgs:
        if 'world where' in msg.get('content', ''):
            lines = msg['content'].split('\n')
            rule_desc = lines[1] if len(lines) > 1 else ''
            break
    
    # Extract options
    last_msg = msgs[-1].get('content', '')
    options_match = re.search(r'A\.\s*(.+?)\s*\n.*?B\.\s*(.+)', last_msg, re.DOTALL)
    
    opt_a = opt_b = ''
    if options_match:
        opt_a = options_match.group(1).strip()
        opt_b = options_match.group(2).strip().split('\n')[0]
    
    # Extract units from options
    def get_time_units(text):
        matches = re.findall(r'(seconds?|minutes?|hours?|days?|weeks?|months?|years?)', text.lower())
        return [m.rstrip('s') for m in matches]
    
    units_a = get_time_units(opt_a)
    units_b = get_time_units(opt_b)
    all_answer_units = set(units_a + units_b)
    
    # Extract changed unit from rule
    rule_unit_match = re.search(r'(\d+)\s*(\w+)\s*=\s*(\d+)\s*(\w+)', rule_desc)
    rule_units = set()
    if rule_unit_match:
        rule_units.add(rule_unit_match.group(2).rstrip('s'))
        rule_units.add(rule_unit_match.group(4).rstrip('s'))
    
    # Check relevance
    is_relevant = len(rule_units & all_answer_units) > 0
    
    method_c_samples.append({
        'rule': rule_desc[:80],
        'rule_units': rule_units,
        'opt_a': opt_a[:40],
        'opt_b': opt_b[:40],
        'answer_units': all_answer_units,
        'relevant': is_relevant
    })

print(f'Found {len(method_c_samples)} Method C (Time Unit) samples\n')

for i, s in enumerate(method_c_samples[:10]):
    relevant_marker = '✓' if s['relevant'] else '✗'
    print(f'{relevant_marker} Sample {i}:')
    print(f'    Rule units:     {s["rule_units"]}')
    print(f'    Answer units:   {s["answer_units"]}')
    print(f'    Rule:           {s["rule"]}...')
    print(f'    A: {s["opt_a"]}')
    print(f'    B: {s["opt_b"]}\n')

# Statistics
relevant_count = sum(1 for s in method_c_samples if s['relevant'])
print(f'\n=== Summary ===')
print(f'Total Method C samples: {len(method_c_samples)}')
print(f'Relevant (rule units match answer units): {relevant_count}/{len(method_c_samples)} ({100*relevant_count//len(method_c_samples)}%)')
