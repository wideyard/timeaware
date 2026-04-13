#!/usr/bin/env python3
import json

print('=== COMPLETE TIMEDIAL SAMPLE ===\n')
with open('data-converted/TimeDial/sample_T5/TIMEDIAL_single.jsonl') as f:
    d = json.loads(f.readline())
    
print(f'Dataset: {d["dataset_name"]}')
print(f'Source ID: {d["source_id"]}')
print(f'Rule Applied: {d["metadata"]["rule_applied"]}')
print(f'\n--- Messages ({len(d["messages"])} total) ---\n')

for i, msg in enumerate(d['messages']):
    role = msg['role']
    content = msg['content']
    print(f'[Message {i}] {role.upper()}')
    print(f'{content}')
    print()

print('--- Answer Key ---')
print(f'Expected Answer: {d["answer_key"]}')
print(f'Options: {[o["text"] for o in d["options"]]}')
