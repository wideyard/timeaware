#!/usr/bin/env python3
import json

print('=== CHECKING 5 TIMEDIAL SAMPLES FOR COUNTERFACTUAL LOGIC ===\n')

with open('data-converted/TimeDial/sample_T5/TIMEDIAL_single.jsonl') as f:
    for sample_idx in range(5):
        line = f.readline()
        if not line:
            break
        d = json.loads(line)
        
        rule = d['metadata']['rule_applied']
        answer = d['answer_key'][0]
        original_label = d['metadata']['original_label']
        
        # Extract the rule explanation from first message
        first_msg = d['messages'][0]['content']
        
        # Check if answer changed
        option_a = d['options'][0]['text']
        option_b = d['options'][1]['text']
        
        print(f'Sample {sample_idx}:')
        print(f'  Rule: {rule}')
        print(f'  Original label: {original_label}')
        print(f'  Option A: {option_a}')
        print(f'  Option B: {option_b}')
        print(f'  Expected answer: {answer}')
        print(f'  Rule explanation (first message):', first_msg.split('Consider')[0].strip()[-100:])
        print(f'  Question: {d["messages"][-2]["content"]}')
        print()
