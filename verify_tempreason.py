#!/usr/bin/env python3
import json
from datetime import datetime, timedelta
import re

print("=== TEMPREASON Date Arithmetic Verification ===\n")

with open('d:\\workspace\\timeaware\\data-converted\\TempReason\\sample_T5\\TEMPREASON_single.jsonl') as f:
    for i in range(5):
        try:
            data = json.loads(f.readline())
            
            # Extract original date from message (format: "January 11, 1948")
            content = data['messages'][0]['content']
            date_match = re.search(r'Original date: ([A-Za-z]+ \d{1,2}, \d{4})', content)
            if not date_match:
                continue
                
            orig_date_str = date_match.group(1)
            rule = data['metadata']['rule_applied']
            computed_answer = data['metadata']['computed_answer']
            
            # Parse dates
            orig_date = datetime.strptime(orig_date_str, '%B %d, %Y')
            
            # Parse answer - could be in format "January 11, 1948"
            try:
                answer_date = datetime.strptime(computed_answer, '%B %d, %Y')
            except:
                # Try another format
                print(f"Sample {i}: Could not parse answer '{computed_answer}'")
                continue
            
            # Extract offset from rule - format: "+23 days from the reference date"
            offset_match = re.search(r'\+(\d+) days', rule)
            if offset_match:
                offset = int(offset_match.group(1))
                expected_date = orig_date + timedelta(days=offset)
                
                is_correct = answer_date == expected_date
                status = "[OK]" if is_correct else "[ERROR]"
                
                print(f"Sample {i}:")
                print(f"  Original Date: {orig_date_str}")
                print(f"  Rule: {rule}")
                print(f"  Expected: {expected_date.strftime('%B %d, %Y')} ({orig_date_str} + {offset} days)")
                print(f"  Computed Answer: {computed_answer}")
                print(f"  {status}")
                print()
        except Exception as e:
            print(f"Error on sample {i}: {str(e)}\n")
            continue

