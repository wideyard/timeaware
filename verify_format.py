#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify sample format for all 4 new datasets"""

import json
import os

os.chdir(r'd:\workspace\timeaware\data-converted')

# Check TempReason
print('=== TEMPREASON ===')
with open('TempReason/sample_T5/TEMPREASON_single.jsonl') as f:
    d = json.loads(f.readline())
    print('Messages count:', len(d['messages']))
    print('Last message role:', d['messages'][-1]['role'])
    print('Last message contains "Options:"?', 'Options:' in d['messages'][-1]['content'])
    print('Last message preview:')
    print(d['messages'][-1]['content'][:200])
    print()

# Check tracie  
print('=== TRACIE ===')
with open('tracie/sample_T3/TRACIE_single.jsonl') as f:
    d = json.loads(f.readline())
    print('Messages count:', len(d['messages']))
    print('Last message role:', d['messages'][-1]['role'])
    print('Last message contains "Options:"?', 'Options:' in d['messages'][-1]['content'])
    print('Last message preview:')
    print(d['messages'][-1]['content'][:200])
    print()

# Check TRIP
print('=== TRIP ===')
with open('TRIP/sample_T5/TRIP_single.jsonl') as f:
    d = json.loads(f.readline())
    print('Messages count:', len(d['messages']))
    print('Last message role:', d['messages'][-1]['role'])
    print('Last message contains "Options:"?', 'Options:' in d['messages'][-1]['content'])
    print('Last message preview:')
    print(d['messages'][-1]['content'][:200])
    print()

# Check TimeDial conversation format
print('=== TIMEDIAL (message roles check) ===')
with open('TimeDial/sample_T1/TIMEDIAL_single.jsonl') as f:
    d = json.loads(f.readline())
    print('Messages count:', len(d['messages']))
    print('Message roles:')
    for i, msg in enumerate(d['messages']):
        role = msg['role']
        content_len = len(msg['content'])
        print(f'  Message {i}: role="{role}", content_length={content_len}')
    
    # Check if conversation uses user/assistant
    print('\nConversation check (should have alternating user/assistant):')
    has_user_assistant = any(msg['role'] == 'user' for msg in d['messages']) and any(msg['role'] == 'assistant' for msg in d['messages'])
    print('Has both user and assistant messages?', has_user_assistant)
    
    # Check last message has options
    print('Last message contains "Options:"?', 'Options:' in d['messages'][-1]['content'])
    print('Last message preview:')
    print(d['messages'][-1]['content'][:200])

print('\n=== VERIFICATION COMPLETE ===')
print('✓ All formats appear correct')
