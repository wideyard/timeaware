#!/usr/bin/env python3
import json

with open('data-converted/TimeDial/sample_T5/TIMEDIAL_single.jsonl') as f:
    d = json.loads(f.readline())
    
print('=== TIMEDIAL MESSAGE STRUCTURE (First 5 messages) ===\n')
for i, msg in enumerate(d['messages'][:5]):
    role = msg['role']
    content = msg['content'][:100].replace('\n', ' ')
    print(f'Message {i}: role="{role}"')
    print(f'Content: {content}...\n')
