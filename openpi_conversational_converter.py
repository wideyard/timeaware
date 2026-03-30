#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenPI 2.0 Conversational Temporal Data Converter

Converts OpenPI 2.0 dataset to conversational temporal format.
Primary focus: T2 (State Update), T3 (Conflict Detection)

Key features:
- Tracks entity state changes (location, condition, possession)
- Uses saliency filtering (>= 0.3) to keep significant changes
- Supports multi-step procedure tracking

Output: converted_data_v3/openpi_conversational.jsonl
"""

import json
import random
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from pathlib import Path

# =====================================================================
# Data Structures
# =====================================================================

@dataclass
class ConversationalSample:
    task: str  # T2, T3
    sub_task: str  # e.g., "T2-Convo-State", "T2-Convo-Progressive"
    context: str  # Procedure context
    conversation: List[Dict[str, str]]
    query: str
    answer: str
    state_info: Optional[Dict[str, Any]] = None
    ground_truth: Optional[Dict[str, Any]] = None
    difficulty: str = "medium"
    source_id: Optional[str] = None

# =====================================================================
# Helper Functions
# =====================================================================

# Key attributes for state tracking (as per scheme)
KEY_ATTRIBUTES = ["location", "condition", "possession", "is_destroyed", "state"]

# Attribute synonyms for matching
ATTRIBUTE_SYNONYMS = {
    "location": ["location", "placement", "position", "where"],
    "condition": ["condition", "state", "status", "quality"],
    "possession": ["possession", "ownership", "owned"],
    "is_destroyed": ["is_destroyed", "destroyed", "broken"],
}

# Noise questions for distraction
NOISE_QUESTIONS = [
    "By the way, what's the weather like?",
    "I heard about a new restaurant nearby.",
    "The traffic was heavy this morning.",
    "My neighbor has a new pet.",
    "I need to buy some groceries later.",
    "Did you watch the game last night?",
    "What's for dinner tonight?",
    "Have you tried that new coffee shop?",
    "I forgot to water the plants.",
    "What time is it now?"
]

def normalize_attribute(attr: str) -> str:
    """Normalize attribute to canonical form."""
    attr_lower = attr.lower()
    for canonical, synonyms in ATTRIBUTE_SYNONYMS.items():
        if attr_lower in [s.lower() for s in synonyms]:
            return canonical
        if any(syn.lower() in attr_lower for syn in synonyms):
            return canonical
    return attr_lower

def filter_salient_states(states: List[Dict], threshold: float = 0.3) -> List[Dict]:
    """Filter states by saliency threshold."""
    return [s for s in states if s.get("saliency", 0) >= threshold]

def truncate_text(text: str, max_len: int = 200) -> str:
    """Truncate text to max length."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(' ', 1)[0] + '...'

# =====================================================================
# T2: State Update Converter
# =====================================================================

class T2Converter:
    """Convert OpenPI data to T2 conversational format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_state_tracking_sample(self, goal: str, steps: List[str], 
                                      entity: str, step_key: str, state_data: Dict,
                                      source_id: str) -> Optional[ConversationalSample]:
        """T2-Convo-State: Track entity state after a step."""
        # Extract step number
        step_num = int(step_key.replace("step", ""))
        step_idx = step_num - 1  # 0-indexed
        
        if step_idx >= len(steps):
            return None
        
        current_step = steps[step_idx]
        attribute = normalize_attribute(state_data.get("attribute", ""))
        before = state_data.get("before", "")
        after = state_data.get("after", "")
        
        if not before or not after:
            return None
        
        conversation = []
        
        # Round 1: Goal introduction
        conversation.append({
            "role": "user",
            "content": f"I'm going to {goal.lower()}. Let me walk you through the steps."
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Okay, I'll help you with {goal.lower()}."
        })
        
        # Rounds 2-N: Previous steps
        prev_steps = steps[:step_idx]
        for i, step in enumerate(prev_steps[-3:]):  # Last 3 steps before target
            conversation.append({
                "role": "user",
                "content": f"Step {i+1}: {step}"
            })
            conversation.append({
                "role": "assistant",
                "content": f"Got it, step {i+1} done."
            })
        
        # Round N: Target step
        conversation.append({
            "role": "user",
            "content": f"Step {step_num}: {current_step}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Okay, step {step_num} completed."
        })
        
        # Add distraction
        if random.random() < 0.3:
            conversation.append({
                "role": "user",
                "content": random.choice(NOISE_QUESTIONS)
            })
            conversation.append({
                "role": "assistant",
                "content": "Let's focus on the task."
            })
        
        # Query about state
        if attribute == "location":
            query = f"After step {step_num}, where is the {entity}?"
        elif attribute == "condition":
            query = f"After step {step_num}, what is the condition of the {entity}?"
        elif attribute == "possession":
            query = f"After step {step_num}, who owns the {entity}?"
        else:
            query = f"After step {step_num}, what is the {attribute} of the {entity}?"
        
        conversation.append({
            "role": "user",
            "content": query
        })
        
        # Format answer
        answer_text = after.split("|")[0].strip() if "|" in after else after
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-State",
            context=truncate_text(goal + " " + " ".join(steps[:step_num+1]), 300),
            conversation=conversation,
            query=query,
            answer=answer_text,
            state_info={
                "type": "entity_state",
                "entity": entity,
                "attribute": attribute,
                "before": before,
                "after": after,
                "step": step_num
            },
            ground_truth={
                "entity": entity,
                "attribute": attribute,
                "before_state": before,
                "after_state": after,
                "step_number": step_num
            },
            difficulty="medium" if step_num <= 3 else "hard",
            source_id=f"openpi_t2_state_{source_id}"
        )
    
    def create_progressive_tracking_sample(self, goal: str, steps: List[str],
                                            entity: str, all_states: List[Dict],
                                            source_id: str) -> Optional[ConversationalSample]:
        """T2-Convo-Progressive: Track entity state through multiple steps."""
        # Collect states for this entity across steps
        entity_states = []
        for state in all_states:
            step_key = state.get("step_key", "")
            state_data = state.get("data", {})
            if state_data.get("attribute"):
                entity_states.append({
                    "step": step_key,
                    "attribute": normalize_attribute(state_data.get("attribute", "")),
                    "before": state_data.get("before", ""),
                    "after": state_data.get("after", "")
                })
        
        # Filter for interesting changes
        entity_states = [s for s in entity_states if s["before"] and s["after"]]
        
        if len(entity_states) < 2:
            return None
        
        conversation = []
        
        # Round 1: Goal introduction
        conversation.append({
            "role": "user",
            "content": f"I want to {goal.lower()}. I'll track what happens to the {entity} throughout."
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Okay, I'll help you track the {entity}'s state changes."
        })
        
        # Present steps and state changes
        state_changes = []
        for i, state in enumerate(entity_states[:4]):  # Max 4 steps
            step_num = int(state["step"].replace("step", ""))
            if step_num <= len(steps):
                conversation.append({
                    "role": "user",
                    "content": f"Step {step_num}: {steps[step_num-1]}"
                })
                
                conversation.append({
                    "role": "assistant",
                    "content": f"After this step, the {entity}'s {state['attribute']} changed."
                })
                
                state_changes.append({
                    "step": step_num,
                    "attribute": state["attribute"],
                    "after": state["after"]
                })
        
        # Query about final state
        last_state = state_changes[-1]
        
        # Add distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        conversation.append({
            "role": "assistant",
            "content": "Let me stay focused on tracking."
        })
        
        if last_state["attribute"] == "location":
            query = f"Through all these steps, where is the {entity} now?"
        elif last_state["attribute"] == "condition":
            query = f"Through all these steps, what is the condition of the {entity} now?"
        else:
            query = f"Through all these steps, what is the {last_state['attribute']} of the {entity}?"
        
        answer_text = last_state["after"].split("|")[0].strip() if "|" in last_state["after"] else last_state["after"]
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Progressive",
            context=truncate_text(goal, 200),
            conversation=conversation,
            query=query,
            answer=answer_text,
            state_info={
                "type": "progressive_tracking",
                "entity": entity,
                "state_changes": state_changes,
                "total_steps": len(state_changes)
            },
            ground_truth={
                "final_state": answer_text,
                "attribute": last_state["attribute"],
                "all_changes": state_changes
            },
            difficulty="hard",
            source_id=f"openpi_t2_prog_{source_id}"
        )
    
    def create_intermediate_state_sample(self, goal: str, steps: List[str],
                                          entity: str, step_key: str, state_data: Dict,
                                          source_id: str) -> Optional[ConversationalSample]:
        """T2-Convo-Intermediate: Query about intermediate state."""
        step_num = int(step_key.replace("step", ""))
        step_idx = step_num - 1
        
        if step_idx >= len(steps) - 1:  # Need at least one step after
            return None
        
        attribute = normalize_attribute(state_data.get("attribute", ""))
        before = state_data.get("before", "")
        after = state_data.get("after", "")
        
        if not before or not after:
            return None
        
        conversation = []
        
        # Present full procedure
        conversation.append({
            "role": "user",
            "content": f"I'm following a procedure: {goal.lower()}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I understand. Tell me the steps."
        })
        
        # All steps
        for i, step in enumerate(steps[:5], 1):  # Limit to 5 steps
            conversation.append({
                "role": "user",
                "content": f"Step {i}: {step}"
            })
            conversation.append({
                "role": "assistant",
                "content": f"Noted, step {i}."
            })
        
        # Query about intermediate state
        conversation.append({
            "role": "user",
            "content": f"After step {step_num} but before the final step, what was the {attribute} of the {entity}?"
        })
        
        # The answer should be the "after" state of step_num (which is intermediate)
        answer_text = after.split("|")[0].strip() if "|" in after else after
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Intermediate",
            context=truncate_text(goal, 200),
            conversation=conversation,
            query=f"After step {step_num} but before the final step, what was the {attribute} of the {entity}?",
            answer=answer_text,
            state_info={
                "type": "intermediate_state",
                "entity": entity,
                "attribute": attribute,
                "intermediate_state": after
            },
            ground_truth={
                "step_number": step_num,
                "state_before": before,
                "state_after": after
            },
            difficulty="hard",
            source_id=f"openpi_t2_inter_{source_id}"
        )

# =====================================================================
# T3: Conflict Detection Converter
# =====================================================================

class T3Converter:
    """Convert OpenPI data to T3 conflict detection format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_location_conflict_sample(self, goal: str, steps: List[str],
                                         entity: str, state_data: Dict,
                                         source_id: str) -> Optional[ConversationalSample]:
        """T3-Convo-Location: Detect location conflicts."""
        attribute = normalize_attribute(state_data.get("attribute", ""))
        
        # Only for location attribute
        if attribute != "location":
            return None
        
        after = state_data.get("after", "")
        if not after:
            return None
        
        location = after.split("|")[0].strip() if "|" in after else after
        
        conversation = []
        
        # Round 1: Procedure context
        conversation.append({
            "role": "user",
            "content": f"I'm {goal.lower()}. The {entity} is now {location}."
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Got it, the {entity} is at {location}."
        })
        
        # Round 2: Introduce conflicting action
        conflict_location = self._generate_conflicting_location(location)
        conflict_action = self._generate_conflicting_action(entity, conflict_location)
        
        conversation.append({
            "role": "user",
            "content": f"Now I want to {conflict_action}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"You want to {conflict_action}?"
        })
        
        # Add distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        conversation.append({
            "role": "assistant",
            "content": "Let me think about this."
        })
        
        # Query about conflict
        query = f"Is there any issue with my plan? The {entity} is at {location}."
        
        # Answer explains the conflict
        answer_text = f"Yes, there's a potential conflict. The {entity} is currently {location}, but you're trying to use it {conflict_location}. You may need to retrieve or move it first."
        
        return ConversationalSample(
            task="T3",
            sub_task="T3-Convo-Location",
            context=truncate_text(goal, 200),
            conversation=conversation,
            query=query,
            answer=answer_text,
            state_info={
                "type": "location_conflict",
                "entity": entity,
                "current_location": location,
                "conflict_location": conflict_location
            },
            ground_truth={
                "has_conflict": True,
                "conflict_type": "location",
                "locations": [location, conflict_location]
            },
            difficulty="hard",
            source_id=f"openpi_t3_loc_{source_id}"
        )
    
    def create_resource_conflict_sample(self, goal: str, steps: List[str],
                                          entity: str, state_data: Dict,
                                          source_id: str) -> Optional[ConversationalSample]:
        """T3-Convo-Resource: Detect resource availability conflicts."""
        attribute = normalize_attribute(state_data.get("attribute", ""))
        
        # Check for condition or possession changes
        if attribute not in ["condition", "possession"]:
            return None
        
        before = state_data.get("before", "")
        after = state_data.get("after", "")
        
        if not before or not after:
            return None
        
        conversation = []
        
        # Round 1: State change context
        conversation.append({
            "role": "user",
            "content": f"I'm {goal.lower()}. After a step, the {entity} changed from '{before}' to '{after}'."
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"I see, the {entity} is now {after}."
        })
        
        # Round 2: Introduce reuse scenario
        conversation.append({
            "role": "user",
            "content": f"Can I use the same {entity} again for another similar task?"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"That depends on its current state."
        })
        
        # Query about availability
        query = f"Given the {entity} is now '{after}', is it available for reuse?"
        
        # Determine answer based on state
        if "used" in after.lower() or "dirty" in after.lower():
            answer_text = f"No, the {entity} is currently '{after}' and may not be suitable for reuse. Consider cleaning or replacing it first."
        elif "new" in after.lower() or "clean" in after.lower():
            answer_text = f"Yes, the {entity} is '{after}' and likely available for use, but check for any wear."
        else:
            answer_text = f"The {entity} is now '{after}'. You should check if this state affects its availability for your next task."
        
        return ConversationalSample(
            task="T3",
            sub_task="T3-Convo-Resource",
            context=truncate_text(goal, 200),
            conversation=conversation,
            query=f"Given the {entity} is now '{after}', is it available for reuse?",
            answer=answer_text,
            state_info={
                "type": "resource_conflict",
                "entity": entity,
                "before_state": before,
                "after_state": after,
                "attribute": attribute
            },
            ground_truth={
                "state_change": f"{before} -> {after}",
                "reuse_potential": "depends on state"
            },
            difficulty="medium",
            source_id=f"openpi_t3_res_{source_id}"
        )
    
    def create_procedure_conflict_sample(self, goal: str, steps: List[str],
                                          entity: str, state_changes: List[Dict],
                                          source_id: str) -> Optional[ConversationalSample]:
        """T3-Convo-Procedure: Detect conflicts across procedure steps."""
        if len(state_changes) < 2:
            return None
        
        conversation = []
        
        # Round 1: Introduce procedure
        conversation.append({
            "role": "user",
            "content": f"I'm following this procedure: {goal.lower()}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Okay, I'll track potential conflicts."
        })
        
        # Rounds 2-N: Present steps
        for i, change in enumerate(state_changes[:3]):
            step_info = change.get("step", "")
            attr = change.get("attribute", "")
            before = change.get("before", "")
            after = change.get("after", "")
            
            conversation.append({
                "role": "user",
                "content": f"In {step_info}, the {entity}'s {attr} changed from '{before}' to '{after}'."
            })
            
            conversation.append({
                "role": "assistant",
                "content": f"Recorded: {entity} {attr} = {after}."
            })
        
        # Query about consistency
        query = f"Are there any conflicts or inconsistencies in the {entity}'s state changes across these steps?"
        
        # Analyze for conflicts
        conflicts = self._detect_conflicts(state_changes[:3])
        
        if conflicts:
            answer_text = f"Yes, there are potential conflicts: {conflicts}"
        else:
            answer_text = f"No obvious conflicts detected. The {entity}'s state changes appear consistent across steps."
        
        return ConversationalSample(
            task="T3",
            sub_task="T3-Convo-Procedure",
            context=truncate_text(goal, 200),
            conversation=conversation,
            query=query,
            answer=answer_text,
            state_info={
                "type": "procedure_conflict",
                "entity": entity,
                "state_changes": state_changes[:3]
            },
            ground_truth={
                "conflicts_detected": conflicts,
                "steps_analyzed": len(state_changes[:3])
            },
            difficulty="hard",
            source_id=f"openpi_t3_proc_{source_id}"
        )
    
    def _generate_conflicting_location(self, location: str) -> str:
        """Generate a conflicting location."""
        location_lower = location.lower()
        
        conflicts = {
            "car": ["in another room", "outside", "at the office"],
            "home": ["at work", "at the store", "in the car"],
            "store": ["at home", "in the garage", "at the office"],
            "kitchen": ["in the bedroom", "outside", "in the car"],
            "inside": ["outside", "in the car", "at another location"],
            "outside": ["inside", "in the garage", "at home"]
        }
        
        for key, values in conflicts.items():
            if key in location_lower:
                return random.choice(values)
        
        return "in a different location"
    
    def _generate_conflicting_action(self, entity: str, location: str) -> str:
        """Generate a conflicting action."""
        actions = [
            f"use the {entity} which is {location}",
            f"find the {entity} {location}",
            f"get the {entity} from {location}",
        ]
        return random.choice(actions)
    
    def _detect_conflicts(self, state_changes: List[Dict]) -> str:
        """Detect potential conflicts in state changes."""
        conflicts = []
        
        locations = [s.get("after", "") for s in state_changes if normalize_attribute(s.get("attribute", "")) == "location"]
        conditions = [s.get("after", "") for s in state_changes if normalize_attribute(s.get("attribute", "")) == "condition"]
        
        # Check for contradictory locations
        if len(locations) >= 2:
            if locations[0] != locations[-1]:
                conflicts.append(f"Location changed from {locations[0]} to {locations[-1]}")
        
        # Check for contradictory conditions
        if len(conditions) >= 2:
            if "new" in conditions[0].lower() and "used" in conditions[-1].lower():
                conflicts.append("Condition changed from new to used")
        
        return "; ".join(conflicts) if conflicts else ""

# =====================================================================
# Main Converter
# =====================================================================

class OpenPIConversationalConverter:
    """Main converter for OpenPI 2.0 to conversational format."""
    
    def __init__(self, data_dir: str = "data/OpenPI2.0/data"):
        self.data_dir = Path(data_dir)
        self.t2_converter = T2Converter()
        self.t3_converter = T3Converter()
    
    def load_data(self, max_samples: int = None) -> List[Dict]:
        """Load OpenPI data."""
        data_file = self.data_dir / "dev-data-reformatted-v4.json"
        
        if not data_file.exists():
            print(f"Data file not found: {data_file}")
            return []
        
        with open(data_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        samples = []
        for key, value in raw_data.items():
            if max_samples and len(samples) >= max_samples:
                break
            samples.append({"id": key, **value})
        
        print(f"Loaded {len(samples)} procedures")
        return samples
    
    def extract_entity_states(self, data: Dict) -> List[Dict]:
        """Extract all entity state changes from data."""
        states = data.get("states", [])
        entity_states = []
        
        for state_entry in states:
            entity = state_entry.get("entity", "")
            step_answers = state_entry.get("answers", {})
            
            for step_key, step_states in step_answers.items():
                for state_data in step_states:
                    saliency = state_data.get("saliency", 0)
                    
                    # Filter by saliency (keep >= 0.3)
                    if saliency >= 0.3:
                        entity_states.append({
                            "entity": entity,
                            "step_key": step_key,
                            "data": state_data
                        })
        
        return entity_states
    
    def convert_procedure(self, proc_data: Dict, proc_id: str) -> List[ConversationalSample]:
        """Convert a single procedure to conversational samples."""
        results = []
        
        goal = proc_data.get("goal", "")
        steps = proc_data.get("steps", [])
        
        if not goal or not steps:
            return results
        
        # Extract entity states
        entity_states = self.extract_entity_states(proc_data)
        
        if not entity_states:
            return results
        
        # Group by entity
        entities = {}
        for es in entity_states:
            entity = es["entity"]
            if entity not in entities:
                entities[entity] = []
            entities[entity].append(es)
        
        # Generate T2 samples
        for entity, states in entities.items():
            for state in states[:2]:  # Max 2 samples per entity
                step_key = state["step_key"]
                state_data = state["data"]
                
                # T2-Convo-State
                sample_state = self.t2_converter.create_state_tracking_sample(
                    goal, steps, entity, step_key, state_data, 
                    f"{proc_id}_{entity}_{step_key}"
                )
                if sample_state:
                    results.append(sample_state)
            
            # T2-Convo-Progressive (one per entity)
            if len(states) >= 2:
                sample_prog = self.t2_converter.create_progressive_tracking_sample(
                    goal, steps, entity, states,
                    f"{proc_id}_{entity}"
                )
                if sample_prog:
                    results.append(sample_prog)
        
        # Generate T3 samples
        for entity, states in entities.items():
            for state in states[:1]:  # Max 1 T3 sample per entity
                state_data = state["data"]
                attribute = normalize_attribute(state_data.get("attribute", ""))
                
                # T3-Convo-Location
                if attribute == "location":
                    sample_loc = self.t3_converter.create_location_conflict_sample(
                        goal, steps, entity, state_data,
                        f"{proc_id}_{entity}_loc"
                    )
                    if sample_loc:
                        results.append(sample_loc)
                
                # T3-Convo-Resource
                elif attribute in ["condition", "possession"]:
                    sample_res = self.t3_converter.create_resource_conflict_sample(
                        goal, steps, entity, state_data,
                        f"{proc_id}_{entity}_res"
                    )
                    if sample_res:
                        results.append(sample_res)
        
        return results
    
    def convert_all(self, output_file: str, max_samples: int = None):
        """Convert all procedures."""
        procedures = self.load_data(max_samples)
        all_samples = []
        
        print("Converting procedures...")
        for i, proc in enumerate(procedures):
            proc_id = proc.get("id", f"proc_{i}")
            converted = self.convert_procedure(proc, proc_id)
            all_samples.extend(converted)
            
            if i % 100 == 0:
                print(f"  Processed {i} procedures, generated {len(all_samples)} samples")
        
        # Save output
        print(f"\nTotal converted: {len(all_samples)} samples")
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in all_samples:
                f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
        
        print(f"Saved to: {output_path}")
        
        # Print statistics
        self.print_statistics(all_samples)
        
        return all_samples
    
    def print_statistics(self, samples: List[ConversationalSample]):
        """Print conversion statistics."""
        print("\n" + "=" * 60)
        print("Conversion Summary")
        print("=" * 60)
        
        # Task distribution
        task_counts = {}
        for s in samples:
            task_counts[s.task] = task_counts.get(s.task, 0) + 1
        
        print(f"\nTotal samples: {len(samples)}")
        print("\nTask distribution:")
        for task, count in sorted(task_counts.items()):
            print(f"  {task}: {count}")
        
        # Subtask distribution
        subtask_counts = {}
        for s in samples:
            subtask_counts[s.sub_task] = subtask_counts.get(s.sub_task, 0) + 1
        
        print("\nSubtask distribution:")
        for subtask, count in sorted(subtask_counts.items()):
            print(f"  {subtask}: {count}")
        
        # Difficulty distribution
        diff_counts = {}
        for s in samples:
            diff_counts[s.difficulty] = diff_counts.get(s.difficulty, 0) + 1
        
        print("\nDifficulty distribution:")
        for diff, count in sorted(diff_counts.items()):
            print(f"  {diff}: {count}")

# =====================================================================
# Main Entry
# =====================================================================

def main():
    print("=" * 60)
    print("OpenPI 2.0 Conversational Temporal Data Converter")
    print("=" * 60)
    
    converter = OpenPIConversationalConverter()
    output_file = "converted_data_v3/openpi_conversational.jsonl"
    
    # Limit samples for processing time
    samples = converter.convert_all(output_file, max_samples=2000)

if __name__ == "__main__":
    main()