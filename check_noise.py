#!/usr/bin/env python3
import json

print("=== TIMEDIAL Noise Verification ===\n")

# Check multi_v1 (light noise)
with open('d:\\workspace\\timeaware\\data-converted\\TimeDial\\sample_T1\\TIMEDIAL_multi_v1.jsonl') as f:
    data = json.loads(f.readline())
    print("TIMEDIAL multi_v1 (light noise):")
    for idx, msg in enumerate(data['messages']):
        content = msg['content']
        if len(content) > 100:
            content = content[:100] + "..."
        print(f"  {idx}. [{msg['role']}]: {content}")
    print()

# Check multi_v3 (heavy noise)
with open('d:\\workspace\\timeaware\\data-converted\\TimeDial\\sample_T1\\TIMEDIAL_multi_v3.jsonl') as f:
    data = json.loads(f.readline())
    print("TIMEDIAL multi_v3 (heavy noise):")
    for idx, msg in enumerate(data['messages']):
        content = msg['content']
        if len(content) > 100:
            content = content[:100] + "..."
        print(f"  {idx}. [{msg['role']}]: {content}")
    print()

# Check for repetition
print("Checking for repetition in assistant responses...")
with open('d:\\workspace\\timeaware\\data-converted\\TimeDial\\sample_T1\\TIMEDIAL_multi_v3.jsonl') as f:
    for i in range(5):
        data = json.loads(f.readline())
        for msg in data['messages']:
            if msg['role'] == 'assistant':
                content = msg['content']
                # Check if same phrase appears multiple times
                phrases = content.split('(')
                if len(phrases) > 3:  # Multiple interruptions
                    print(f"  Sample {i}: POSSIBLE REPETITION DETECTED")
                else:
                    print(f"  Sample {i}: OK (no excessive repetition)")
                break
