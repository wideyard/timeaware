#!/usr/bin/env python3
import json

print('=== DETAILED TIMEDIAL SAMPLE WITH COUNTERFACTUAL REASONING ===\n')

with open('data-converted/TimeDial/sample_T1/TIMEDIAL_single.jsonl') as f:
    # Get sample 1 which shows answer changing
    for i in range(2):
        line = f.readline()
    
    d = json.loads(line)
    
print(f'Rule: {d["metadata"]["rule_applied"]}')
print(f'Original label (normal world): {d["metadata"]["original_label"]}')
print(f'\n--- FULL MESSAGE SEQUENCE ---\n')

for msg_idx, msg in enumerate(d['messages']):
    print(f'[Message {msg_idx}] {msg["role"].upper()}:')
    print(msg['content'])
    print()

print('--- COUNTERFACTUAL LOGIC ---')
print(f'Original answer (correct choice in normal world): 24 hours')
print(f'New answer (after applying rule): 22 hours')
print(f'\nWhy it changed:')
print(f'  Rule: {d["metadata"]["rule_applied"]}')
print(f'  Effect: {d["messages"][0]["content"].split("Consider")[0].strip().split("\\n\\n")[-1]}')
