#!/usr/bin/env python3
import json

print('=== CHECKING NEW TIMEDIAL SAMPLES FOR TRUE COUNTERFACTUAL (5 samples) ===\n')

with open('data-converted/TimeDial/sample_T5/TIMEDIAL_single.jsonl', encoding='utf-8') as f:
    for sample_idx in range(5):
        line = f.readline()
        if not line:
            break
        d = json.loads(line)
        
        rule_name = d['metadata']['rule_applied']
        answer = d['answer_key'][0]
        
        # Get messages
        first_msg = d['messages'][0]['content']
        last_msg = d['messages'][-1]['content']
        
        print(f'Sample {sample_idx}:')
        print(f'  Rule: {rule_name}')
        print(f'  Expected answer: {answer}')
        print(f'\n  First message (rule definition):')
        print(f'    {first_msg[:200]}...')
        print(f'\n  Last message (question with options):')
        print(f'    {last_msg[:250]}...')
        
        # Check if answer is leaked
        if answer in first_msg:
            print(f'  ⚠️  WARNING: Answer "{answer}" is leaked in first message!')
        else:
            print(f'  ✓ Answer is NOT leaked')
        
        print(f'\n  Option A: {d["options"][0]["text"]}')
        print(f'  Option B: {d["options"][1]["text"]}')
        print('-' * 80 + '\n')
