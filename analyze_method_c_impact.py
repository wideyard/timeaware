#!/usr/bin/env python3
import json
import re

with open('data-converted/TimeDial/sample_T5/TIMEDIAL_single.jsonl', encoding='utf-8') as f:
    samples = [json.loads(line) for line in f]

print('=== TIMEDIAL Method C Impact Analysis ===\n')

unit_order = {'second': 0, 'minute': 1, 'hour': 2, 'day': 3, 'week': 4, 'month': 5, 'year': 6}

method_c_samples = []
for i, sample in enumerate(samples[:100]):
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
    
    # Extract rule units
    rule_unit_match = re.search(r'(\d+)\s*(\w+)\s*=\s*(\d+)\s*(\w+)', rule_desc)
    rule_units = set()
    if rule_unit_match:
        rule_units.add(rule_unit_match.group(2).rstrip('s'))
        rule_units.add(rule_unit_match.group(4).rstrip('s'))
    
    # Calculate impact
    # For Method C to have impact on BOTH options:
    # - At least one unit from rule_units must appear in both opt_a AND opt_b units
    # - OR answer units must be WITHIN or BETWEEN rule units in hierarchy
    
    impact_a = len(set(units_a) & rule_units) > 0
    impact_b = len(set(units_b) & rule_units) > 0
    has_genuine_impact = impact_a or impact_b  # At least one option affected
    
    # Better check: are answer units in the same "neighborhood" as rule units?
    if rule_units and all_answer_units:
        answer_positions = [unit_order.get(u, 2) for u in all_answer_units if u in unit_order]
        rule_positions = [unit_order.get(u, 2) for u in rule_units if u in unit_order]
        
        if answer_positions and rule_positions:
            min_ans = min(answer_positions)
            max_ans = max(answer_positions)
            min_rule = min(rule_positions)
            max_rule = max(rule_positions)
            
            # Check if ranges overlap or are adjacent
            truly_related = (min_ans <= max_rule and min_rule <= max_ans) or \
                           abs(min_ans - max_rule) <= 1 or abs(min_rule - max_ans) <= 1
        else:
            truly_related = False
    else:
        truly_related = False
    
    method_c_samples.append({
        'rule_units': rule_units,
        'answer_units': all_answer_units,
        'opt_a': opt_a[:40],
        'opt_b': opt_b[:40],
        'has_impact': has_genuine_impact,
        'truly_related': truly_related
    })

print(f'Total Method C samples: {len(method_c_samples)}')
genuine_impact = sum(1 for s in method_c_samples if s['has_impact'])
truly_related_count = sum(1 for s in method_c_samples if s['truly_related'])

print(f'Has genuine impact on options: {genuine_impact}/{len(method_c_samples)} ({100*genuine_impact//len(method_c_samples) if method_c_samples else 0}%)')
print(f'Truly related (ranges overlap): {truly_related_count}/{len(method_c_samples)} ({100*truly_related_count//len(method_c_samples) if method_c_samples else 0}%)')

print('\n=== Problematic samples (not truly related) ===\n')
problem_count = 0
for i, s in enumerate(method_c_samples):
    if not s['truly_related']:
        problem_count += 1
        if problem_count <= 5:  # Show first 5 problems
            print(f'Sample {i}:')
            print(f'  Rule units: {s["rule_units"]}')
            print(f'  Answer units: {s["answer_units"]}')
            print(f'  A: {s["opt_a"]}')
            print(f'  B: {s["opt_b"]}\n')

print(f'Total problematic: {problem_count}')
