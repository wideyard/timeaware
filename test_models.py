"""测试多模型调用"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from llm_client import call_llm

print("Testing gpt-4o-mini...")
try:
    r = call_llm('Say hello in one sentence.', model_key='gpt-4o-mini')
    print(f"  Response: {r[:100]}")
except Exception as e:
    print(f"  Error: {e}")

print("\nTesting doubao-seed-1-8...")
try:
    r = call_llm('Say hello in one sentence.', model_key='doubao-seed-1-8')
    print(f"  Response: {r[:100]}")
except Exception as e:
    print(f"  Error: {e}")

print("\nTesting doubao-seed-2-0-pro...")
try:
    r = call_llm('Say hello in one sentence.', model_key='doubao-seed-2-0-pro')
    print(f"  Response: {r[:100]}")
except Exception as e:
    print(f"  Error: {e}")
