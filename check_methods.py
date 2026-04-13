#!/usr/bin/env python3
import json
from collections import Counter

print('=== DISTRIBUTION OF COUNTERFACTUAL METHODS ===\n')

method_counts = Counter()
with open('data-converted/TimeDial/sample_T5/TIMEDIAL_single.jsonl', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        d = json.loads(line)
        rule_name = d['metadata']['rule_applied']
        
        if 'Time flow speed' in rule_name:
            method_counts['Method A: Time flow speed changed'] += 1
        elif 'Duration constraint' in rule_name:
            method_counts['Method B: Duration constraint'] += 1
        elif 'Time unit' in rule_name:
            method_counts['Method C: Time unit redefined'] += 1
        else:
            method_counts['Unknown'] += 1
    
    print(f'Total samples: {idx + 1}\n')
    for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
        percentage = (count / (idx + 1)) * 100
        print(f'{method}: {count} ({percentage:.1f}%)')

print('\n=== EXAMPLE OF EACH METHOD ===\n')

methods_shown = set()
with open('data-converted/TimeDial/sample_T5/TIMEDIAL_single.jsonl', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        d = json.loads(line)
        rule_name = d['metadata']['rule_applied']
        
        method_key = None
        if 'Time flow speed' in rule_name and 'A' not in methods_shown:
            method_key = 'A'
        elif 'Duration constraint' in rule_name and 'B' not in methods_shown:
            method_key = 'B'
        elif 'Time unit' in rule_name and 'C' not in methods_shown:
            method_key = 'C'
        
        if method_key:
            methods_shown.add(method_key)
            print(f'Method {method_key}:')
            print(f'  Rule: {rule_name}')
            print(f'  Description: {d["messages"][0]["content"][:150]}...')
            print(f'  Question: {d["messages"][-1]["content"][:150]}...')
            print()
