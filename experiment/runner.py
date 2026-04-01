"""Runner module for the Timeaware Benchmark Experiment.

Handles LLM API calls with retry logic, rate limiting, and result collection.
Uses the existing llm_client.py for model invocation.
"""

import sys
import os
import time
import json
from typing import Dict, List, Any, Optional

# Add parent directory to path for importing llm_client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client import call_llm
from experiment.subtask_config import EVAL_MODELS, LLM_TEMPERATURE, MAX_RETRIES, API_DELAY
from experiment.prompt_builder import build_messages_for_mode
from experiment.noise_injector import inject_noise, NOISE_INJECTORS


def call_with_retry(messages: List[Dict[str, str]], model_key: str,
                     temperature: float = LLM_TEMPERATURE,
                     max_retries: int = MAX_RETRIES) -> Optional[str]:
    """Call LLM with retry logic.
    
    Args:
        messages: List of message dicts
        model_key: Model identifier
        temperature: Temperature parameter
        max_retries: Maximum number of retries
    
    Returns:
        LLM response text, or None if all retries failed
    """
    # Convert messages to prompt format for call_llm
    system_prompt = None
    user_prompt = ""
    
    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        elif msg["role"] == "user":
            # For multi-turn, accumulate all user messages
            if user_prompt:
                user_prompt += "\n\n" + msg["content"]
            else:
                user_prompt = msg["content"]
        elif msg["role"] == "assistant":
            # Include assistant messages in the prompt for multi-turn
            user_prompt += f"\n\n[Assistant]: {msg['content']}"
    
    # For multi-turn conversations, use a different approach
    # Build a single prompt that contains the full conversation
    full_prompt_parts = []
    for msg in messages:
        if msg["role"] == "system":
            full_prompt_parts.append(f"[System]: {msg['content']}")
        elif msg["role"] == "user":
            full_prompt_parts.append(f"[User]: {msg['content']}")
        elif msg["role"] == "assistant":
            full_prompt_parts.append(f"[Assistant]: {msg['content']}")
    
    full_prompt = "\n\n".join(full_prompt_parts)
    
    for attempt in range(max_retries):
        try:
            response = call_llm(
                prompt=full_prompt,
                system_prompt=system_prompt if system_prompt else "",
                temperature=temperature,
                model_key=model_key,
            )
            return response
        except Exception as e:
            print(f"    [RETRY {attempt+1}/{max_retries}] Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    return None


def run_single_sample(sample: Dict[str, Any], subtask_key: str,
                       model_key: str, mode: str,
                       noise_type: Optional[str] = None) -> Dict[str, Any]:
    """Run a single sample through the LLM.
    
    Args:
        sample: The data sample
        subtask_key: The merged subtask key
        model_key: Model to use
        mode: Conversation mode
        noise_type: Noise type (only for multi_turn_noise mode)
    
    Returns:
        Result dict with prediction and metadata
    """
    # Apply noise if needed
    if mode == "multi_turn_noise" and noise_type:
        sample = inject_noise(sample, noise_type)
    
    # Build messages
    messages = build_messages_for_mode(sample, subtask_key, mode)
    
    # Call LLM
    start_time = time.time()
    response = call_with_retry(messages, model_key)
    elapsed = time.time() - start_time
    
    return {
        "subtask_key": subtask_key,
        "atomic_task": sample.get('_atomic_task', sample.get('sub_task', '')),
        "dimension": sample.get('task', ''),
        "model": model_key,
        "mode": mode,
        "noise_type": noise_type,
        "query": sample.get('query', ''),
        "ground_truth": sample.get('answer', ''),
        "prediction": response,
        "elapsed_seconds": elapsed,
        "success": response is not None,
        "source_id": sample.get('source_id', ''),
        "difficulty": sample.get('difficulty', ''),
    }


def run_experiment(samples: Dict[str, List[Dict]],
                    models: Optional[List[str]] = None,
                    modes: Optional[List[str]] = None,
                    noise_types: Optional[List[str]] = None,
                    delay: float = API_DELAY) -> List[Dict[str, Any]]:
    """Run the full experiment.
    
    Args:
        samples: {subtask_key: [sample_dicts]}
        models: List of model keys to test
        modes: List of conversation modes
        noise_types: List of noise types (for multi_turn_noise mode)
        delay: Delay between API calls
    
    Returns:
        List of result dicts
    """
    models = models or EVAL_MODELS
    modes = modes or ["single_turn", "multi_turn", "multi_turn_noise"]
    noise_types = noise_types or list(NOISE_INJECTORS.keys())
    
    results = []
    total = 0
    
    # Count total
    for subtask_key, sample_list in samples.items():
        for sample in sample_list:
            for model in models:
                for mode in modes:
                    if mode == "multi_turn_noise":
                        total += len(noise_types)
                    else:
                        total += 1
    
    print(f"\n{'='*60}")
    print(f"Running experiment: {total} total API calls")
    print(f"  Models: {models}")
    print(f"  Modes: {modes}")
    print(f"  Noise types: {noise_types}")
    print(f"{'='*60}\n")
    
    current = 0
    
    for subtask_key, sample_list in samples.items():
        print(f"\n--- Subtask: {subtask_key} ({len(sample_list)} samples) ---")
        
        for sample in sample_list:
            for model in models:
                for mode in modes:
                    if mode == "multi_turn_noise":
                        for noise_type in noise_types:
                            current += 1
                            print(f"  [{current}/{total}] {model} | {mode}+{noise_type} | {sample.get('source_id', '')[:30]}")
                            
                            result = run_single_sample(
                                sample, subtask_key, model, mode, noise_type
                            )
                            results.append(result)
                            
                            if delay > 0:
                                time.sleep(delay)
                    else:
                        current += 1
                        print(f"  [{current}/{total}] {model} | {mode} | {sample.get('source_id', '')[:30]}")
                        
                        result = run_single_sample(
                            sample, subtask_key, model, mode, None
                        )
                        results.append(result)
                        
                        if delay > 0:
                            time.sleep(delay)
    
    return results


def save_results(results: List[Dict[str, Any]], output_path: str):
    """Save experiment results to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    # Print summary
    success = sum(1 for r in results if r.get('success'))
    failed = len(results) - success
    print(f"  Total: {len(results)} | Success: {success} | Failed: {failed}")
