#!/usr/bin/env python3
import json
import re
from collections import Counter

with open('data-converted/TimeDial/sample_T5/TIMEDIAL_single.jsonl', encoding='utf-8') as f:
    samples = [json.loads(line) for line in f]

print('=== TIMEDIAL Final Verification ===\n')

# 1. Count method distribution
methods = []
method_c_samples = []

for sample in samples:
    rule_applied = sample.get('metadata', {}).get('rule_applied', '')
    methods.append(rule_applied)
    
    if 'Time unit' in rule_applied:
        method_c_samples.append(sample)

method_counts = Counter(methods)
print('Method Distribution:')
for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True):
    pct = 100 * count // len(samples)
    print(f'  {method:40} {count:3} ({pct}%)')

# 2. For Method C samples, verify relevance
print(f'\n=== Method C (Time Unit) - {len(method_c_samples)} samples ===\n')

unit_order = {'second': 0, 'minute': 1, 'hour': 2, 'day': 3, 'week': 4, 'month': 5, 'year': 6}

relevant_count = 0
for i, sample in enumerate(method_c_samples[:15]):  # Show first 15 Method C samples
    msgs = sample.get('messages', [])
    
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
    
    # Extract units
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
    
    # Check relevance
    if rule_units and all_answer_units:
        # Check if ranges overlap
        answer_positions = [unit_order.get(u, 2) for u in all_answer_units if u in unit_order]
        rule_positions = [unit_order.get(u, 2) for u in rule_units if u in unit_order]
        
        if answer_positions and rule_positions:
            min_ans = min(answer_positions)
            max_ans = max(answer_positions)
            min_rule = min(rule_positions)
            max_rule = max(rule_positions)
            
            is_relevant = (min_ans <= max_rule and min_rule <= max_ans)
            if is_relevant:
                relevant_count += 1
        else:
            is_relevant = False
    else:
        is_relevant = False
    
    marker = '✓' if is_relevant else '✗'
    print(f'{marker} Sample {i}: Rule units={rule_units}, Answer units={all_answer_units}')
    print(f'    Rule:  {rule_desc[:80]}...')
    print(f'    A: {opt_a[:50]}')
    print(f'    B: {opt_b[:50]}\n')

print(f'Method C relevance: {relevant_count}/15 shown = {100*relevant_count//15}% (first 15 samples)')

# 3. Overall statistics
print('\n=== Summary ===')
print(f'Total samples: {len(samples)}')
print(f'Method A (Time Speed): {method_counts.get("Time flow speed changed", 0)}')
print(f'Method B (Duration Constraint): {method_counts.get("Duration constraint", 0) + method_counts.get("Duration constraint: maximum", 0) + method_counts.get("Duration constraint: minimum", 0)}')
print(f'Method C (Time Unit): {len(method_c_samples)}')
