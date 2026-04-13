#!/usr/bin/env python3
import json

print('=== COMPLETE TIMEDIAL COUNTERFACTUAL EXAMPLE (Method B) ===\n')

# Find a Method B example
with open('data-converted/TimeDial/sample_T5/TIMEDIAL_single.jsonl', encoding='utf-8') as f:
    for line in f:
        d = json.loads(line)
        if 'Duration constraint' in d['metadata']['rule_applied']:
            break

print(f'Rule Applied: {d["metadata"]["rule_applied"]}')
print(f'Original Label: {d["metadata"]["original_label"]}')
print(f'Expected Answer: {d["answer_key"][0]}\n')

print('=== CONVERSATION FLOW ===\n')

for msg_idx, msg in enumerate(d['messages']):
    print(f'[Message {msg_idx}] {msg["role"].upper()}:')
    print(f'{msg["content"]}')
    print()

print('=== COUNTERFACTUAL REASONING REQUIRED ===\n')
print('The model must:')
print('1. Understand the NEW rule (no activity can last > 1 hour)')
print('2. Examine both options:')
for opt in d['options']:
    print(f'   - {opt["key"]}: {opt["text"]}')
print('3. Determine which violates the constraint')
print('4. Choose the appropriate answer based on the new rule\n')
print(f'Correct answer: {d["answer_key"][0]}')
